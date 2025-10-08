import sympy
from ..core.energy_hub import EnergyHub
from typing import Tuple, List, Callable

class SymbolicAnalyzer:
    """
    Performs symbolic analysis on an EnergyHub model to derive the coupling matrix C.
    """
    def __init__(self, energy_hub: EnergyHub):
        self.energy_hub = energy_hub
        self.C_matrix: sympy.Matrix = None

    def derive_coupling_matrix(self) -> sympy.Matrix:
        """
        Derives the coupling matrix C (V_out = C * V_in) from the system matrices X, Y, Z.
        Assumes the system is invertible (Q matrix is square and non-singular).
        """
        X = self.energy_hub.X_matrix
        Y = self.energy_hub.Y_matrix
        Z = self.energy_hub.Z_matrix

        if X is None or Y is None or Z is None:
            raise ValueError("EnergyHub matrices (X, Y, Z) are not set. Build them first.")

        # Construct Q and R matrices as per PPT P40
        # Q = [X; Z]
        # R = [-I; 0]
        Q = sympy.Matrix.vstack(X, Z)
        
        # Number of hub inputs (rows in X)
        num_hub_inputs = X.shape[0]
        # Number of rows in Z
        num_Z_rows = Z.shape[0]

        R = sympy.Matrix.vstack(
            -sympy.eye(num_hub_inputs), 
            sympy.zeros(num_Z_rows, num_hub_inputs)
        )

        # Check if Q is square and invertible
        if Q.rows != Q.cols:
            raise ValueError(f"Q matrix is not square ({Q.rows}x{Q.cols}), cannot invert.")
        
        try:
            Q_inv = Q.inv()
        except ValueError as e:
            raise ValueError(f"Q matrix is singular, cannot invert: {e}")

        # C = -Y * Q_inv * R
        self.C_matrix = -Y * Q_inv * R
        return self.C_matrix

    def pretty_print_results(self, matrix: sympy.Matrix, name: str = "Matrix"):
        """
        Prints a sympy matrix in a readable format.
        """
        print(f"\n--- {name} ---")
        sympy.pprint(matrix)

    def get_numeric_function(self, symbolic_matrix: sympy.Matrix, args: List[sympy.Symbol]) -> Callable:
        """
        Converts a symbolic matrix into a callable numeric function using sympy.lambdify.
        The returned function takes numeric values for 'args' and returns a numpy array.
        :param symbolic_matrix: The sympy.Matrix to convert.
        :param args: A list of sympy.Symbol objects that are the arguments of the function.
                     These should be the symbolic parameters (e.g., efficiencies) in the matrix.
        :return: A callable function that takes numeric values for 'args' and returns a numpy array.
        """
        if not isinstance(symbolic_matrix, sympy.Matrix):
            raise TypeError("Input must be a sympy.Matrix.")
        if not all(isinstance(arg, sympy.Symbol) for arg in args):
            raise TypeError("All arguments in 'args' must be sympy.Symbol objects.")

        # Extract all free symbols from the matrix
        free_symbols = list(symbolic_matrix.free_symbols)
        
        # Ensure all provided args are actually free symbols in the matrix
        if not set(args).issubset(set(free_symbols)):
            # This is a warning, not an error, as lambdify can still work, but might not be what user expects
            print(f"Warning: Some provided arguments {set(args) - set(free_symbols)} are not free symbols in the matrix.")
        
        # sympy.lambdify can convert a sympy expression into a lambda function
        # that can be evaluated numerically. It can return a numpy-compatible function.
        numeric_func = sympy.lambdify(args, symbolic_matrix, "numpy")
        
        return numeric_func