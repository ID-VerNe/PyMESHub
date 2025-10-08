from pyomo.environ import *
import numpy as np
from typing import Dict, Any as AnyType, List

from ..core.energy_hub import EnergyHub
from ..components.storage import Storage # Import Storage component to identify it

def solve_economic_dispatch(hub: EnergyHub, time_series_data: Dict[str, AnyType]) -> Dict[str, AnyType]:
    """
    Solves the economic dispatch problem for the given EnergyHub using Pyomo.
    
    :param hub: An EnergyHub instance with X, Y, Z matrices already built.
    :param time_series_data: A dictionary containing time-series data for loads, prices, etc.
                             Expected keys:
                             'load_profiles' (dict of {output_branch_name: list of values}),
                             'input_prices' (dict of {input_branch_name: list of values}),
                             'time_steps' (int, number of time steps),
                             'storage_params' (dict of {storage_comp_name: {E_min, E_max, E_initial, delta_soc_branch_name}}).
    :return: A dictionary containing the optimization results (e.g., optimal branch flows).
    """
    model = ConcreteModel()

    # --- Sets and Parameters ---
    time_steps = time_series_data['time_steps']
    model.T = RangeSet(0, time_steps - 1) # Time steps

    # Global branches from the EnergyHub
    global_branches = hub.global_branches
    model.BRANCHES = Set(initialize=global_branches)
    num_branches = len(global_branches)

    # Map branch names to their indices for matrix operations
    branch_to_idx = {name: i for i, name in enumerate(global_branches)}

    # Hub inputs and outputs (branch names)
    hub_input_branches = [global_branches[i] for i in hub.hub_input_branch_indices]
    hub_output_branches = [global_branches[i] for i in hub.hub_output_branch_indices]
    model.HUB_INPUTS = Set(initialize=hub_input_branches)
    model.HUB_OUTPUTS = Set(initialize=hub_output_branches)

    # Group output branches by their destination IO node
    from collections import defaultdict
    output_node_to_branches = defaultdict(list)
    for branch_name in hub_output_branches:
        # Assumes branch name format: from_node_from_port_to_to_node_to_port
        to_node = branch_name.split('_to_')[1].split('_')[0]
        output_node_to_branches[to_node].append(branch_name)

    model.HUB_OUTPUT_NODES = Set(initialize=output_node_to_branches.keys())

    # Input prices (indexed by input branch name and time step)
    model.input_price = Param(model.HUB_INPUTS, model.T, initialize=lambda m, b, t: time_series_data['input_prices'][b][t])

    # Load profiles (indexed by output IO node name and time step)
    model.load_profile = Param(model.HUB_OUTPUT_NODES, model.T, initialize=lambda m, n, t: time_series_data['load_profiles'][n][t])

    # --- Variables ---
    # V_b_t: Flow in branch b at time t
    model.V = Var(model.BRANCHES, model.T, domain=NonNegativeReals) # Enforce non-negative flows

    # --- Storage Specific Variables and Sets ---
    storage_components = {name: comp for name, comp in hub.components.items() if isinstance(comp, Storage)}
    model.STORAGE_COMPONENTS = Set(initialize=storage_components.keys())

    if storage_components:
        # E_s_t: State of Charge for storage s at time t
        model.E = Var(model.STORAGE_COMPONENTS, model.T, domain=NonNegativeReals) # SoC must be non-negative

        # Parameters for storage
        model.E_min = Param(model.STORAGE_COMPONENTS, initialize=lambda m, s: time_series_data['storage_params'][s]['E_min'])
        model.E_max = Param(model.STORAGE_COMPONENTS, initialize=lambda m, s: time_series_data['storage_params'][s]['E_max'])
        model.E_initial = Param(model.STORAGE_COMPONENTS, initialize=lambda m, s: time_series_data['storage_params'][s]['E_initial'])
        
        # Map storage component name to its delta_soc branch name
        model.delta_soc_branch = Param(model.STORAGE_COMPONENTS, initialize=lambda m, s: time_series_data['storage_params'][s]['delta_soc_branch_name'], within=Any)


    # --- Constraints ---
    # 1. Energy Hub Balance (Z * V = 0) for each time step
    # Convert symbolic Z matrix to numpy for Pyomo
    Z_np = np.array(hub.Z_matrix.tolist(), dtype=float) 
    num_Z_rows = Z_np.shape[0]

    def _energy_balance_rule(model, i, t):
        return sum(Z_np[i, branch_to_idx[b]] * model.V[b, t] for b in model.BRANCHES) == 0
    model.energy_balance = Constraint(RangeSet(0, num_Z_rows - 1), model.T, rule=_energy_balance_rule)

    # 2. Output Load Satisfaction (Aggregated)
    def _load_satisfaction_rule(model, node, t):
        branches_to_node = output_node_to_branches[node]
        return sum(model.V[b, t] for b in branches_to_node) >= model.load_profile[node, t]
    model.load_satisfaction = Constraint(model.HUB_OUTPUT_NODES, model.T, rule=_load_satisfaction_rule)

    # 3. Input Flow Non-Negative (assuming V is positive for flow INTO hub for input branches)
    def _input_flow_non_negative_rule(model, b, t):
        if b in model.HUB_INPUTS:
            return model.V[b, t] >= 0
        return Constraint.Skip
    model.input_flow_non_negative = Constraint(model.BRANCHES, model.T, rule=_input_flow_non_negative_rule)

    # --- Storage Specific Constraints ---
    if storage_components:
        # 3.1. SoC Dynamics: E(t) = E(t-1) + Delta_E(t)
        def _soc_dynamics_rule(model, s, t):
            delta_e_branch = model.delta_soc_branch[s]
            if t == 0:
                return model.E[s, t] == model.E_initial[s] + model.V[delta_e_branch, t]
            return model.E[s, t] == model.E[s, t-1] + model.V[delta_e_branch, t]
        model.soc_dynamics = Constraint(model.STORAGE_COMPONENTS, model.T, rule=_soc_dynamics_rule)

        # 3.2. SoC Limits: E_min <= E(t) <= E_max
        def _soc_min_rule(model, s, t):
            return model.E[s, t] >= model.E_min[s]
        model.soc_min = Constraint(model.STORAGE_COMPONENTS, model.T, rule=_soc_min_rule)

        def _soc_max_rule(model, s, t):
            return model.E[s, t] <= model.E_max[s]
        model.soc_max = Constraint(model.STORAGE_COMPONENTS, model.T, rule=_soc_max_rule)

        # 3.3. Final SoC (Optional: ensure battery returns to initial state or above a minimum)
        # Temporarily commented out for debugging infeasibility
        # def _final_soc_rule(model, s):
        #     return model.E[s, time_steps - 1] >= model.E_initial[s]
        # model.final_soc = Constraint(model.STORAGE_COMPONENTS, rule=_final_soc_rule)



    # --- Objective Function ---
    # Minimize total cost of input energy
    def _total_cost_rule(model):
        return sum(model.input_price[b, t] * model.V[b, t] for b in model.HUB_INPUTS for t in model.T)
    model.total_cost = Objective(rule=_total_cost_rule, sense=minimize)

    # --- Solve ---
    # For now, we'll use 'glpk' as the solver. User needs to ensure it's installed and in PATH.
    solver = SolverFactory('glpk')
    results = solver.solve(model, tee=True) # tee=True to see solver output

    # --- Process Results ---
    if (results.solver.status == SolverStatus.ok) and (results.solver.termination_condition == TerminationCondition.optimal):
        print("Optimization successful!")
        optimal_flows = {
            b: {t: model.V[b, t].value for t in model.T}
            for b in model.BRANCHES
        }
        optimal_soc = {}
        if storage_components:
            optimal_soc = {
                s: {t: model.E[s, t].value for t in model.T}
                for s in model.STORAGE_COMPONENTS
            }

        total_cost = model.total_cost()
        return {
            "optimal_flows": optimal_flows,
            "optimal_soc": optimal_soc,
            "total_cost": total_cost,
            "solver_status": results.solver.status,
            "termination_condition": results.solver.termination_condition
        }
    else:
        print(f"Optimization failed or not optimal: {results.solver.status}, {results.solver.termination_condition}")
        return {
            "solver_status": results.solver.status,
            "termination_condition": results.solver.termination_condition
        }