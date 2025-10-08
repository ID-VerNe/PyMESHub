import sympy
import numpy as np
from pymeshub.graph.builder import GraphEnergyHub
from pymeshub.solvers.optimizer import solve_economic_dispatch

def run_optimization_with_storage_example():
    print("--- Running Optimization with Storage Example (Phase 4 Milestone) ---")

    # 1. Define symbolic parameters (even if we use numeric values later, the framework expects them)
    eta_q_chp = sympy.Float(0.8)
    eta_w_chp = sympy.Float(0.3)
    eta_boiler = sympy.Float(0.9)
    eta_c_storage = sympy.Float(0.95)
    eta_d_storage = sympy.Float(0.9)

    # 2. Use GraphEnergyHub to build a system
    graph_hub = GraphEnergyHub("MyOptimizedHub")

    # Components
    graph_hub.add_component(
        'CHP1', 
        'CHPBackPressure', 
        eta_q=eta_q_chp, 
        eta_w=eta_w_chp, 
        elec_ports=['elec_for_load', 'elec_for_storage'] # Define two distinct elec ports
    )
    graph_hub.add_component('Boiler1', 'Boiler', eta=eta_boiler)
    graph_hub.add_component('Storage1', 'Storage', eta_c=eta_c_storage, eta_d=eta_d_storage)

    # IO Nodes
    graph_hub.add_io_node('GasInput', 'input')
    graph_hub.add_io_node('ElecLoad', 'output')
    graph_hub.add_io_node('HeatLoad', 'output')

    # Connections
    # Gas to CHP and Boiler
    graph_hub.connect('GasInput', 'out', 'CHP1', 'fuel_in')
    graph_hub.connect('GasInput', 'out', 'Boiler1', 'fuel_in')

    # CHP outputs
    graph_hub.connect('CHP1', 'heat_out', 'HeatLoad', 'in')
    graph_hub.connect('CHP1', 'elec_for_load', 'ElecLoad', 'in') # Use the specific port for the load
    graph_hub.connect('CHP1', 'elec_for_storage', 'Storage1', 'energy_in') # Use the specific port for storage

    # Boiler output
    graph_hub.connect('Boiler1', 'heat_out', 'HeatLoad', 'in')

    # Storage output
    graph_hub.connect('Storage1', 'energy_out', 'ElecLoad', 'in') # Storage can discharge to load

    # 3. Call build() to get the EnergyHub instance
    hub = graph_hub.build()

    # 4. Define time-series data
    time_steps = 2
    time_series_data = {
        'time_steps': time_steps,
        'load_profiles': {
            'HeatLoad': [10.0, 12.0], # Total heat load
            'ElecLoad': [20.0, 25.0]  # Total electricity load
        },
        'input_prices': {
            # These are the branch names for the inputs
            'GasInput_out_to_CHP1_fuel_in': [1.0, 1.2], # Gas price for CHP
            'GasInput_out_to_Boiler1_fuel_in': [1.0, 1.2] # Gas price for Boiler
        },
        'storage_params': {
            'Storage1': {
                'E_min': 0.0,
                'E_max': 50.0,
                'E_initial': 10.0,
                'delta_soc_branch_name': f"Storage1_delta_soc_branch" # This branch is now created automatically
            }
        }
    }

    # The delta_soc branch is now automatically handled by GraphEnergyHub.build()
    # No manual intervention needed here.

    # 5. Call solve_economic_dispatch()
    results = solve_economic_dispatch(hub, time_series_data)

    # 6. Print the optimization results
    print("\n--- Optimization Results ---")
    if results['solver_status'] == 'ok' and results['termination_condition'] == 'optimal':
        print(f"Total Cost: {results['total_cost']:.2f}")
        print("Optimal Flows (V_b_t):")
        for branch, flows in results['optimal_flows'].items():
            print(f"  {branch}: {flows}")
        if results['optimal_soc']:
            print("Optimal SoC (E_s_t):")
            for storage_comp, soc_values in results['optimal_soc'].items():
                print(f"  {storage_comp}: {soc_values}")
    else:
        print("Optimization did not find an optimal solution.")

    print("\n--- Phase 4 Milestone Achieved (if optimization is successful)! ---")

if __name__ == "__main__":
    run_optimization_with_storage_example()
