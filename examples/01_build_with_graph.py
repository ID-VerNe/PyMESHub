import numpy as np
from pymeshub.graph.builder import GraphEnergyHub

def run_graph_build_example():
    print("--- Running Graph Build Example (Phase 2 Milestone) ---")

    # 1. Create a GraphEnergyHub instance
    graph_hub = GraphEnergyHub("MyGraphHub")

    # 2. Use add_component, add_io_node, and connect to define the system
    # Components
    graph_hub.add_component('CHP1', 'CHPBackPressure', eta_q=0.8, eta_w=0.3)
    graph_hub.add_component('Boiler1', 'Boiler', eta=0.9)

    # IO Nodes (representing external connections)
    graph_hub.add_io_node('GasInput', 'input')
    graph_hub.add_io_node('HeatLoad', 'output')
    graph_hub.add_io_node('ElecLoad', 'output')

    # Connections
    # GasInput -> CHP1.fuel_in
    graph_hub.connect('GasInput', 'out', 'CHP1', 'fuel_in') # 'out' is a generic port for IO nodes
    # CHP1.heat_out -> HeatLoad
    graph_hub.connect('CHP1', 'heat_out', 'HeatLoad', 'in') # 'in' is a generic port for IO nodes
    # CHP1.elec_out -> ElecLoad
    graph_hub.connect('CHP1', 'elec_out', 'ElecLoad', 'in')

    # GasInput -> Boiler1.fuel_in
    # Note: For simplicity, we're connecting GasInput to both CHP and Boiler. In a real system, 
    # this might imply a splitter or separate gas lines. For matrix building, it means two branches
    # originating from the same conceptual 'GasInput' but going to different components.
    # The 'build' method will handle unique branch names.
    graph_hub.connect('GasInput', 'out', 'Boiler1', 'fuel_in')
    # Boiler1.heat_out -> HeatLoad
    graph_hub.connect('Boiler1', 'heat_out', 'HeatLoad', 'in')

    # 3. Visualize the graph topology
    graph_hub.visualize()

    # 4. Call build() to get the populated EnergyHub instance
    hub = graph_hub.build()

    # 5. Retrieve and print the X, Y, Z matrices
    X, Y, Z = hub.get_system_matrices()

    print("\n--- Generated Matrices from Graph Build ---")
    print("X Matrix (Input Incidence):")
    print(X)
    print("\nY Matrix (Output Incidence):")
    print(Y)
    print("\nZ Matrix (System Energy Conversion):")
    print(Z)

    # 5. Include assertions to verify that the matrices are identical to the expected matrices from Phase 1.
    # Expected matrices from 00_simple_numeric.py (after correction)
    expected_X = np.array([
        [0., 0., 0., 1., 0.],
        [0., 0., 0., 0., 1.]
    ])
    expected_Y = np.array([
        [1., 0., 0., 0., 0.],
        [0., 1., 0., 0., 0.],
        [0., 0., 1., 0., 0.]
    ])
    expected_Z = np.array([
        [0., 0., 1., 0., 0.8],
        [0., 1., 0., 0., 0.3],
        [1., 0., 0., 0.9, 0.]
    ])

    print("\n--- Verification ---")
    assert np.allclose(X, expected_X)
    assert np.allclose(Y, expected_Y)
    assert np.allclose(Z, expected_Z)
    print("All matrices match expected values from Phase 1.")

    print("\n--- Phase 2 Milestone Achieved! ---")

if __name__ == "__main__":
    run_graph_build_example()
