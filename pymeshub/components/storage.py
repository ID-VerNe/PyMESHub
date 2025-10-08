import sympy
from ..components.base import Component

class Storage(Component):
    """
    A generic energy storage component (e.g., Thermal Storage, Battery).
    It has an input port for charging, an output port for discharging,
    and a virtual port/branch for the change in State of Charge (SoC).
    """
    def __init__(self, name: str, eta_c: sympy.Expr, eta_d: sympy.Expr):
        super().__init__(name)
        self.set_parameter('eta_c', sympy.sympify(eta_c)) # Charging efficiency
        self.set_parameter('eta_d', sympy.sympify(eta_d)) # Discharging efficiency

        # Define local port indices
        self.add_input_port('energy_in', 0)
        self.add_output_port('energy_out', 1)
        # Virtual port for change in SoC. This is not a physical port but an internal variable.
        # We assign it a local index for matrix construction.
        self.add_input_port('delta_soc', 2) # Treat as an input for matrix construction

    def get_port_branch_matrix(self) -> sympy.Matrix:
        """
        Returns the local port-branch incidence matrix (Ag) for Storage.
        Ports: [energy_in, energy_out, delta_soc]
        Branches: [b_in, b_out, b_delta_soc]
        """
        return sympy.Matrix([
            [1, 0, 0],  # Port 'energy_in' (index 0) is input to internal branch 0
            [0, -1, 0], # Port 'energy_out' (index 1) is output from internal branch 1
            [0, 0, 1]   # Port 'delta_soc' (index 2) is input to internal branch 2 (representing energy stored)
        ])

    def get_characteristic_matrix(self) -> sympy.Matrix:
        """
        Returns the characteristic matrix (Hg) for Storage.
        From PPT P54: Hg = [eta_c, 1/eta_d, 1] for (V_charge, V_discharge, Delta E)
        Ports order: [energy_in, energy_out, delta_soc]
        Equation: eta_c * V_energy_in - (1/eta_d) * V_energy_out - Delta_E = 0
        (Assuming V_energy_in is positive for charging, V_energy_out is positive for discharging)
        """
        eta_c = self.get_parameter('eta_c')
        eta_d = self.get_parameter('eta_d')
        
        # The equation is: eta_c * V_in - V_out/eta_d - Delta_E = 0
        # So, Hg = [eta_c, -1/eta_d, -1]
        return sympy.Matrix([
            [eta_c, -1/eta_d, -1]
        ])
