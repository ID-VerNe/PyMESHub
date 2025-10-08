import sympy
import numpy as np
from pymeshub.graph.builder import GraphEnergyHub
from pymeshub.analysis.symbolic_analyzer import SymbolicAnalyzer

def run_symbolic_derivation_example():
    print("--- Running Symbolic Derivation Example (Phase 3 Milestone) ---")

    # 1. Define symbolic parameters for components
    eta_q_chp = sympy.Symbol('eta_q_chp')
    eta_w_chp = sympy.Symbol('eta_w_chp')
    eta_boiler = sympy.Symbol('eta_boiler')

    # 2. Use GraphEnergyHub to build a system with these symbolic parameters
    graph_hub = GraphEnergyHub("MySymbolicHub")

    # Components with symbolic parameters
    graph_hub.add_component('CHP1', 'CHPBackPressure', eta_q=eta_q_chp, eta_w=eta_w_chp)
    graph_hub.add_component('Boiler1', 'Boiler', eta=eta_boiler)

    # IO Nodes (representing external connections)
    graph_hub.add_io_node('GasInput', 'input')
    graph_hub.add_io_node('HeatLoad', 'output')
    graph_hub.add_io_node('ElecLoad', 'output')

    # Connections (same as Phase 2 example)
    graph_hub.connect('GasInput', 'out', 'CHP1', 'fuel_in')
    graph_hub.connect('CHP1', 'heat_out', 'HeatLoad', 'in')
    graph_hub.connect('CHP1', 'elec_out', 'ElecLoad', 'in')
    graph_hub.connect('GasInput', 'out', 'Boiler1', 'fuel_in')
    graph_hub.connect('Boiler1', 'heat_out', 'HeatLoad', 'in')

    # 3. Call build() to get the EnergyHub with symbolic matrices
    hub = graph_hub.build()

    # 4. Create a SymbolicAnalyzer instance
    analyzer = SymbolicAnalyzer(hub)

    # 5. Call derive_coupling_matrix() to get the symbolic C matrix
    C_symbolic = analyzer.derive_coupling_matrix()

    # 6. Print the symbolic C matrix using pretty_print_results()
    analyzer.pretty_print_results(C_symbolic, "Symbolic Coupling Matrix C")

    # 7. Use get_numeric_function() to convert C to a numeric function
    # Define the order of arguments for the numeric function
    symbolic_args = [eta_q_chp, eta_w_chp, eta_boiler]
    numeric_C_func = analyzer.get_numeric_function(C_symbolic, symbolic_args)

    # 8. Evaluate the numeric function with sample values
    sample_eta_q_chp = 0.8
    sample_eta_w_chp = 0.3
    sample_eta_boiler = 0.9

    C_numeric = numeric_C_func(sample_eta_q_chp, sample_eta_w_chp, sample_eta_boiler)

    print("\n--- Numeric Coupling Matrix C (evaluated with sample values) ---")
    print(C_numeric)

    # Verification: Compare with expected numeric C from Phase 1 logic
    # V_out = C * V_in
    # V_out = [V_heat_load, V_elec_load, V_heat_load_boiler]
    # V_in = [V_gas_in_chp, V_gas_in_boiler]

    # From ZV=0, X,Y,Z matrices, we have:
    # 0.8*V_gas_in_chp + V_chp_heat_out = 0  => V_chp_heat_out = -0.8*V_gas_in_chp
    # 0.3*V_gas_in_chp + V_chp_elec_out = 0  => V_chp_elec_out = -0.3*V_gas_in_chp
    # 0.9*V_gas_in_boiler + V_boiler_heat_out = 0 => V_boiler_heat_out = -0.9*V_gas_in_boiler

    # Hub outputs are: Boiler1_heat_out_to_HeatLoad_in (idx 0), CHP1_elec_out_to_ElecLoad_in (idx 1), CHP1_heat_out_to_HeatLoad_in (idx 2)
    # Hub inputs are: GasInput_out_to_Boiler1_fuel_in (idx 3), GasInput_out_to_CHP1_fuel_in (idx 4)

    # Let V_in = [V_gas_in_boiler, V_gas_in_chp]
    # V_out[0] (Boiler heat) = -eta_boiler * V_gas_in_boiler
    # V_out[1] (CHP elec) = -eta_w_chp * V_gas_in_chp
    # V_out[2] (CHP heat) = -eta_q_chp * V_gas_in_chp

    # C matrix maps V_in (GasInput_out_to_Boiler1_fuel_in, GasInput_out_to_CHP1_fuel_in) to V_out
    # C[0,0] = -eta_boiler (Boiler heat from GasInput_out_to_Boiler1_fuel_in)
    # C[0,1] = 0 (Boiler heat from GasInput_out_to_CHP1_fuel_in)
    # C[1,0] = 0 (CHP elec from GasInput_out_to_Boiler1_fuel_in)
    # C[1,1] = -eta_w_chp (CHP elec from GasInput_out_to_CHP1_fuel_in)
    # C[2,0] = 0 (CHP heat from GasInput_out_to_Boiler1_fuel_in)
    # C[2,1] = -eta_q_chp (CHP heat from GasInput_out_to_CHP1_fuel_in)

    expected_C_numeric = np.array([
        [-sample_eta_boiler, 0.0],
        [0.0, -sample_eta_w_chp],
        [0.0, -sample_eta_q_chp]
    ])

    print("\n--- Verification ---")
    assert np.allclose(C_numeric, expected_C_numeric)
    print("Numeric C matrix matches expected values.")

    print("\n--- Phase 3 Milestone Achieved! ---")

if __name__ == "__main__":
    run_symbolic_derivation_example()
