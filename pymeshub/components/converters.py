from typing import List

import sympy
from .base import Component

class CHPBackPressure(Component):
    """
    Combined Heat and Power (CHP) unit operating in back-pressure mode.
    Supports both a single default electricity port ('elec_out') or multiple user-defined electricity ports.
    """
    def __init__(self, name: str, eta_q: sympy.Expr, eta_w: sympy.Expr, **kwargs):
        super().__init__(name)
        
        self.set_parameter('eta_q', sympy.sympify(eta_q))
        self.set_parameter('eta_w', sympy.sympify(eta_w))

        # Flexible handling of electricity ports
        if 'elec_ports' in kwargs and kwargs['elec_ports']:
            self.elec_ports = kwargs['elec_ports']
        else:
            self.elec_ports = ['elec_out'] # Default to a single port

        # Define local port indices
        self.add_input_port('fuel_in', 0)
        self.add_output_port('heat_out', 1)
        for i, port_name in enumerate(self.elec_ports):
            self.add_output_port(port_name, 2 + i)

    def get_port_branch_matrix(self) -> sympy.Matrix:
        """
        Returns the local port-branch incidence matrix (Ag) for CHP.
        """
        num_ports = 2 + len(self.elec_ports)
        Ag = sympy.zeros(num_ports, num_ports)
        Ag[0, 0] = 1  # Fuel in
        Ag[1, 1] = -1 # Heat out
        for i in range(len(self.elec_ports)):
            Ag[2 + i, 2 + i] = -1 # Elec outs
        return Ag

    def get_characteristic_matrix(self) -> sympy.Matrix:
        """
        Returns the characteristic matrix (Hg) for CHP back-pressure mode.
        Correctly balances total energy against all outputs.
        """
        eta_q = self.get_parameter('eta_q')
        eta_w = self.get_parameter('eta_w')

        # Heat balance: eta_q * V_fuel - V_heat = 0
        heat_balance_row = [eta_q, -1] + [0] * len(self.elec_ports)

        # Electricity balance: eta_w * V_fuel - sum(V_elec_i) = 0
        elec_balance_row = [eta_w, 0] + [-1] * len(self.elec_ports)

        return sympy.Matrix([heat_balance_row, elec_balance_row])

class Boiler(Component):
    """
    A simple boiler component.
    Single input (fuel), single output (heat).
    """
    def __init__(self, name: str, eta: sympy.Expr):
        super().__init__(name)
        self.set_parameter('eta', sympy.sympify(eta)) # Efficiency

        # Define local port indices
        self.add_input_port('fuel_in', 0)
        self.add_output_port('heat_out', 1)

    def get_port_branch_matrix(self) -> sympy.Matrix:
        """
        Returns the local port-branch incidence matrix (Ag) for Boiler.
        Assumes 2 internal branches corresponding to fuel_in, heat_out.
        Ports: [fuel_in, heat_out]
        Branches: [b_fuel, b_heat]
        """
        return sympy.Matrix([
            [1, 0],  # Port 'fuel_in' (index 0) is input to internal branch 0
            [0, -1]  # Port 'heat_out' (index 1) is output from internal branch 1
        ])

    def get_characteristic_matrix(self) -> sympy.Matrix:
        """
        Returns the characteristic matrix (Hg) for Boiler.
        Ports order: [fuel_in, heat_out]
        """
        eta = self.get_parameter('eta')
        return sympy.Matrix([
            [eta, -1]  # eta * V_fuel_in - V_heat_out = 0
        ])

class ConvertibleLoad(Component):
    """
    A virtual component representing a flexible demand that can be satisfied
    by different energy forms (e.g., electricity or heat) with a substitution ratio.
    This is a Type 4 component (multiple inputs, multiple outputs) from PPT P29.
    """
    def __init__(self, name: str, substitution_ratio: sympy.Expr):
        super().__init__(name)
        self.set_parameter('substitution_ratio', sympy.sympify(substitution_ratio))

        # Define local port indices
        self.add_input_port('elec_supply', 0)
        self.add_input_port('heat_supply', 1)
        self.add_output_port('satisfied_demand', 2)

    def get_port_branch_matrix(self) -> sympy.Matrix:
        """
        Returns the local port-branch incidence matrix (Ag) for ConvertibleLoad.
        Ports: [elec_supply, heat_supply, satisfied_demand]
        Branches: [b_elec, b_heat, b_demand]
        """
        return sympy.Matrix([
            [1, 0, 0],  # Port 'elec_supply' (index 0) is input to internal branch 0
            [0, 1, 0],  # Port 'heat_supply' (index 1) is input to internal branch 1
            [0, 0, -1]  # Port 'satisfied_demand' (index 2) is output from internal branch 2
        ])

    def get_characteristic_matrix(self) -> sympy.Matrix:
        """
        Returns the characteristic matrix (Hg) for ConvertibleLoad.
        Ports order: [elec_supply, heat_supply, satisfied_demand]
        Equation: V_satisfied_demand = V_elec_supply + substitution_ratio * V_heat_supply
        So, Hg = [-1, -substitution_ratio, 1]
        """
        substitution_ratio = self.get_parameter('substitution_ratio')
        return sympy.Matrix([
            [-1, -substitution_ratio, 1]
        ])

# --- New Components based on PPT --- #

class ElectricBoiler(Component):
    """
    Electric Boiler: Converts electricity to heat.
    Type 1: single input, single output.
    """
    def __init__(self, name: str, eta: sympy.Expr):
        super().__init__(name)
        self.set_parameter('eta', sympy.sympify(eta))
        self.add_input_port('elec_in', 0)
        self.add_output_port('heat_out', 1)

    def get_port_branch_matrix(self) -> sympy.Matrix:
        return sympy.Matrix([[1, 0], [0, -1]])

    def get_characteristic_matrix(self) -> sympy.Matrix:
        eta = self.get_parameter('eta')
        return sympy.Matrix([[eta, -1]]) # eta * V_elec_in - V_heat_out = 0

class HeatPump(Component):
    """
    Heat Pump: Converts electricity to heat with a Coefficient of Performance (COP).
    Type 1: single input, single output.
    """
    def __init__(self, name: str, cop: sympy.Expr):
        super().__init__(name)
        self.set_parameter('cop', sympy.sympify(cop))
        self.add_input_port('elec_in', 0)
        self.add_output_port('heat_out', 1)

    def get_port_branch_matrix(self) -> sympy.Matrix:
        return sympy.Matrix([[1, 0], [0, -1]])

    def get_characteristic_matrix(self) -> sympy.Matrix:
        cop = self.get_parameter('cop')
        return sympy.Matrix([[cop, -1]]) # cop * V_elec_in - V_heat_out = 0

class AbsorptionChiller(Component):
    """
    Absorption Chiller: Converts heat to cooling.
    Type 1: single input, single output.
    """
    def __init__(self, name: str, cop: sympy.Expr):
        super().__init__(name)
        self.set_parameter('cop', sympy.sympify(cop))
        self.add_input_port('heat_in', 0)
        self.add_output_port('cool_out', 1)

    def get_port_branch_matrix(self) -> sympy.Matrix:
        return sympy.Matrix([[1, 0], [0, -1]])

    def get_characteristic_matrix(self) -> sympy.Matrix:
        cop = self.get_parameter('cop')
        return sympy.Matrix([[cop, -1]]) # cop * V_heat_in - V_cool_out = 0

class Transformer(Component):
    """
    Transformer: Converts electricity from one voltage level to another (modeled as a simple efficiency loss).
    Type 1: single input, single output.
    """
    def __init__(self, name: str, eta: sympy.Expr):
        super().__init__(name)
        self.set_parameter('eta', sympy.sympify(eta))
        self.add_input_port('elec_in', 0)
        self.add_output_port('elec_out', 1)

    def get_port_branch_matrix(self) -> sympy.Matrix:
        return sympy.Matrix([[1, 0], [0, -1]])

    def get_characteristic_matrix(self) -> sympy.Matrix:
        eta = self.get_parameter('eta')
        return sympy.Matrix([[eta, -1]]) # eta * V_elec_in - V_elec_out = 0

class PowerToGas(Component):
    """
    Power-to-Gas (P2G): Converts electricity to gas (e.g., hydrogen or methane).
    Type 1: single input, single output.
    """
    def __init__(self, name: str, eta: sympy.Expr):
        super().__init__(name)
        self.set_parameter('eta', sympy.sympify(eta))
        self.add_input_port('elec_in', 0)
        self.add_output_port('gas_out', 1)

    def get_port_branch_matrix(self) -> sympy.Matrix:
        return sympy.Matrix([[1, 0], [0, -1]])

    def get_characteristic_matrix(self) -> sympy.Matrix:
        eta = self.get_parameter('eta')
        return sympy.Matrix([[eta, -1]]) # eta * V_elec_in - V_gas_out = 0

