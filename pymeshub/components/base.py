from abc import ABC, abstractmethod
import sympy
from abc import ABC, abstractmethod
from typing import Union

class Component(ABC):
    """
    Abstract base class for all energy hub components.
    Defines the interface for components to provide their
    port-branch incidence matrix (Ag) and characteristic matrix (Hg).
    """
    def __init__(self, name: str):
        self.name = name
        self.input_ports = {}  # {port_name: port_index}
        self.output_ports = {} # {port_name: port_index}
        self.parameters = {}   # {param_name: value}

    @abstractmethod
    def get_port_branch_matrix(self) -> sympy.Matrix:
        """
        Returns the port-branch incidence matrix (Ag) for the component.
        This matrix defines the connections between the component's ports
        and its internal branches.
        """
        pass

    @abstractmethod
    def get_characteristic_matrix(self) -> sympy.Matrix:
        """
        Returns the characteristic matrix (Hg) for the component.
        This matrix defines the energy conversion characteristics of the component.
        """
        pass

    def add_input_port(self, port_name: str, port_index: int):
        """Adds an input port to the component."""
        self.input_ports[port_name] = port_index

    def add_output_port(self, port_name: str, port_index: int):
        """Adds an output port to the component."""
        self.output_ports[port_name] = port_index

    def set_parameter(self, param_name: str, value):
        """Sets a parameter for the component."""
        self.parameters[param_name] = value

    def get_parameter(self, param_name: str):
        """Gets a parameter value for the component."""
        return self.parameters.get(param_name)

    def __repr__(self):
        return f"{self.__class__.__name__}(name='{self.name}')"
