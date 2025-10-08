
import unittest
import sympy
import numpy as np

from pymeshub.core.energy_hub import EnergyHub
from pymeshub.core.matrix_builder import MatrixBuilder
from pymeshub.components.converters import CHPBackPressure

class TestMatrixBuilder(unittest.TestCase):
    """
    Unit tests for the MatrixBuilder class.
    """

    def test_simple_chp_system_symbolic(self):
        """
        Tests the MatrixBuilder with a simple system containing one CHP unit,
        using symbolic parameters. This verifies that the Z matrix is built correctly.
        """
        print("\n--- Running Test: test_simple_chp_system_symbolic ---")

        # 1. Define symbolic parameters
        eta_q_sym = sympy.Symbol('eta_q')
        eta_w_sym = sympy.Symbol('eta_w')

        # 2. Manually configure the EnergyHub
        hub = EnergyHub("TestHub_CHP_Symbolic")

        # Add component
        chp = CHPBackPressure(name="CHP1", eta_q=eta_q_sym, eta_w=eta_w_sym, elec_ports=['elec_out'])
        hub.add_component(chp)

        # Define global branches and mappings
        hub.global_branches = ['gas_in', 'heat_out', 'elec_out']
        branch_map = {
            ('CHP1', 'fuel_in'): 0,
            ('CHP1', 'heat_out'): 1,
            ('CHP1', 'elec_out'): 2,
        }
        hub.port_to_global_branch_map = branch_map
        hub.hub_input_branch_indices = [0]
        hub.hub_output_branch_indices = [1, 2]

        # 3. Run the MatrixBuilder
        builder = MatrixBuilder(hub)
        X, Y, Z = builder.build_system_matrices()

        # 4. Define expected matrices
        # Expected Z = Hg * Ag_global
        # Hg = [[eta_q, -1, 0], [eta_w, 0, -1]]
        # Ag_global = [[1, 0, 0], [0, -1, 0], [0, 0, -1]]
        # Z = [[eta_q, 1, 0], [eta_w, 0, 1]]
        expected_Z = sympy.Matrix([
            [eta_q_sym, 1, 0],
            [eta_w_sym, 0, 1]
        ])

        # Expected X
        expected_X = sympy.Matrix([[1, 0, 0]])

        # Expected Y
        expected_Y = sympy.Matrix([
            [0, 1, 0],
            [0, 0, 1]
        ])

        # 5. Assert that the generated matrices match the expected ones
        self.assertEqual(Z, expected_Z)
        self.assertEqual(X, expected_X)
        self.assertEqual(Y, expected_Y)
        
        print("Symbolic CHP system matrices are correct.")

    def test_simple_chp_system_numeric(self):
        """
        Tests the MatrixBuilder with a simple system containing one CHP unit,
        using numeric parameters. This is a sanity check with concrete values.
        """
        print("\n--- Running Test: test_simple_chp_system_numeric ---")

        # 1. Define numeric parameters
        eta_q_num = 0.8
        eta_w_num = 0.3

        # 2. Manually configure the EnergyHub
        hub = EnergyHub("TestHub_CHP_Numeric")
        chp = CHPBackPressure(name="CHP1", eta_q=eta_q_num, eta_w=eta_w_num, elec_ports=['elec_out'])
        hub.add_component(chp)
        hub.global_branches = ['gas_in', 'heat_out', 'elec_out']
        hub.port_to_global_branch_map = {('CHP1', 'fuel_in'): 0, ('CHP1', 'heat_out'): 1, ('CHP1', 'elec_out'): 2}
        hub.hub_input_branch_indices = [0]
        hub.hub_output_branch_indices = [1, 2]

        # 3. Run the MatrixBuilder
        builder = MatrixBuilder(hub)
        X, Y, Z = builder.build_system_matrices()

        # 4. Define expected matrices (as numpy arrays for comparison)
        expected_Z_np = np.array([[0.8, 1.0, 0.0], [0.3, 0.0, 1.0]])
        expected_X_np = np.array([[1.0, 0.0, 0.0]])
        expected_Y_np = np.array([[0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])

        # Convert sympy matrices to numpy for comparison
        Z_np = np.array(Z.tolist(), dtype=float)
        X_np = np.array(X.tolist(), dtype=float)
        Y_np = np.array(Y.tolist(), dtype=float)

        # 5. Assert that the generated matrices match the expected ones
        self.assertTrue(np.allclose(Z_np, expected_Z_np))
        self.assertTrue(np.allclose(X_np, expected_X_np))
        self.assertTrue(np.allclose(Y_np, expected_Y_np))

        print("Numeric CHP system matrices are correct.")

if __name__ == '__main__':
    unittest.main()
