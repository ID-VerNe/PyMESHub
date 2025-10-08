import numpy as np
from pymeshub.core.energy_hub import EnergyHub
from pymeshub.core.matrix_builder import MatrixBuilder
from pymeshub.components.converters import CHPBackPressure, Boiler

def run_simple_numeric_example():
    print("--- Running Simple Numeric Example (Phase 1 Milestone) ---")

    # 1. Define a sample configuration dictionary
    config = {
        'components': [
            {'name': 'CHP1', 'type': 'CHPBackPressure', 'params': {'eta_q': 0.8, 'eta_w': 0.3}},
            {'name': 'Boiler1', 'type': 'Boiler', 'params': {'eta': 0.9}}
        ],
        'branches': [
            'b_gas_in_chp',
            'b_chp_heat_out',
            'b_chp_elec_out',
            'b_gas_in_boiler',
            'b_boiler_heat_out'
        ],
        'port_mappings': {
            'CHP1': {
                'fuel_in': 'b_gas_in_chp',
                'heat_out': 'b_chp_heat_out',
                'elec_out': 'b_chp_elec_out'
            },
            'Boiler1': {
                'fuel_in': 'b_gas_in_boiler',
                'heat_out': 'b_boiler_heat_out'
            }
        },
        'hub_inputs': ['b_gas_in_chp', 'b_gas_in_boiler'],
        'hub_outputs': ['b_chp_heat_out', 'b_chp_elec_out', 'b_boiler_heat_out']
    }

    # Map component type strings to actual classes
    component_types = {
        'CHPBackPressure': CHPBackPressure,
        'Boiler': Boiler
    }

    # 2. Create an EnergyHub instance
    hub = EnergyHub("MyTestHub")

    # 3. Load the configuration into the EnergyHub
    hub.load_config(config, component_types)
    print(f"Energy Hub: {hub.name}")
    print(f"Components: {list(hub.components.keys())}")
    print(f"Global Branches: {hub.global_branches}")

    # 4. Create a MatrixBuilder instance
    builder = MatrixBuilder(hub)

    # 5. Call build_system_matrices() to get X, Y, Z
    X, Y, Z = builder.build_system_matrices()

    # 6. Print the matrices
    print("\n--- Generated Matrices ---")
    print("X Matrix (Input Incidence):")
    print(X)
    print("\nY Matrix (Output Incidence):")
    print(Y)
    print("\nZ Matrix (System Energy Conversion):")
    print(Z)

    # Verification (simple check)
    expected_X_shape = (len(config['hub_inputs']), len(config['branches']))
    expected_Y_shape = (len(config['hub_outputs']), len(config['branches']))
    # Z rows = (CHP_Hg_rows + Boiler_Hg_rows) = (2 + 1) = 3
    expected_Z_shape = (3, len(config['branches']))

    print("\n--- Verification ---")
    print(f"X shape: {X.shape}, Expected: {expected_X_shape}")
    print(f"Y shape: {Y.shape}, Expected: {expected_Y_shape}")
    print(f"Z shape: {Z.shape}, Expected: {expected_Z_shape}")

    assert X.shape == expected_X_shape
    assert Y.shape == expected_Y_shape
    assert Z.shape == expected_Z_shape
    print("Matrix shapes are correct.")

    # Further manual checks for content (optional, but good for debugging)
    # For example, check specific values in Z matrix
    # CHP1 (eta_q=0.8, eta_w=0.3)
    # Boiler1 (eta=0.9)

    # Z matrix should look like:
    # [ 0.8  -1.   0.   0.   0. ]  (CHP1 heat equation: 0.8*b_gas_in_chp - b_chp_heat_out = 0)
    # [ 0.3   0.  -1.   0.   0. ]  (CHP1 elec equation: 0.3*b_gas_in_chp - b_chp_elec_out = 0)
    # [ 0.    0.   0.   0.9  -1. ]  (Boiler1 heat equation: 0.9*b_gas_in_boiler - b_boiler_heat_out = 0)

    # X matrix should have 1s at b_gas_in_chp (index 0) and b_gas_in_boiler (index 3)
    # Y matrix should have 1s at b_chp_heat_out (index 1), b_chp_elec_out (index 2), b_boiler_heat_out (index 4)

    # Let's add a more specific check for Z
    expected_Z = np.array([
        [0.8, 1.0, 0.0, 0.0, 0.0],
        [0.3, 0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.9, 1.0]
    ], dtype=float)
    assert np.allclose(Z, expected_Z)
    print("Z matrix content is correct.")

    print("\n--- Phase 1 Milestone Achieved! ---")

if __name__ == "__main__":
    run_simple_numeric_example()
