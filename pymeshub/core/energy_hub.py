import sympy
import numpy as np # Re-add numpy import
from typing import Dict, List, Any, Tuple
from ..components.base import Component

class EnergyHub:
    """
    Represents an Energy Hub, managing its components and system-level matrices.
    """
    def __init__(self, name: str = "MyEnergyHub"):
        self.name = name
        self.components: Dict[str, Component] = {}
        self.global_branches: List[str] = [] # Ordered list of all unique branches
        # (comp_name, port_name) -> global_branch_index
        self.port_to_global_branch_map: Dict[Tuple[str, str], int] = {}
        self.hub_input_branch_indices: List[int] = []
        self.hub_output_branch_indices: List[int] = []

        self.X_matrix: sympy.Matrix = None
        self.Y_matrix: sympy.Matrix = None
        self.Z_matrix: sympy.Matrix = None

    def add_component(self, component: Component):
        """
        Adds a component to the energy hub.
        """
        if component.name in self.components:
            raise ValueError(f"Component with name '{component.name}' already exists.")
        self.components[component.name] = component

    def load_config(self, config: Dict[str, Any], component_types: Dict[str, type]):
        """
        Loads the energy hub configuration from a dictionary.
        component_types: A dictionary mapping component type names (str) to their classes.
        """
        # 1. Instantiate components
        for comp_config in config.get('components', []):
            comp_name = comp_config['name']
            comp_type_str = comp_config['type']
            comp_params = comp_config.get('params', {})

            if comp_type_str not in component_types:
                raise ValueError(f"Unknown component type: {comp_type_str}")
            comp_class = component_types[comp_type_str]
            component_instance = comp_class(name=comp_name, **comp_params)
            self.add_component(component_instance)

        # 2. Identify global branches and map ports
        self.global_branches = config.get('branches', [])
        if not self.global_branches:
            raise ValueError("No global branches defined in config.")

        # Create a mapping from branch name to its index
        branch_name_to_index = {name: i for i, name in enumerate(self.global_branches)}

        for comp_name, port_mappings in config.get('port_mappings', {}).items():
            if comp_name not in self.components:
                raise ValueError(f"Port mapping for unknown component: {comp_name}")
            for port_name, branch_name in port_mappings.items():
                if branch_name not in branch_name_to_index:
                    raise ValueError(f"Unknown branch '{branch_name}' in port mapping for {comp_name}.{port_name}")
                self.port_to_global_branch_map[(comp_name, port_name)] = branch_name_to_index[branch_name]

        # 3. Identify hub inputs and outputs
        for hub_input_branch_name in config.get('hub_inputs', []):
            if hub_input_branch_name not in branch_name_to_index:
                raise ValueError(f"Unknown hub input branch: {hub_input_branch_name}")
            self.hub_input_branch_indices.append(branch_name_to_index[hub_input_branch_name])

        for hub_output_branch_name in config.get('hub_outputs', []):
            if hub_output_branch_name not in branch_name_to_index:
                raise ValueError(f"Unknown hub output branch: {hub_output_branch_name}")
            self.hub_output_branch_indices.append(branch_name_to_index[hub_output_branch_name])

    def set_system_matrices(self, X: sympy.Matrix, Y: sympy.Matrix, Z: sympy.Matrix):
        """
        Sets the assembled system matrices for the energy hub.
        """
        self.X_matrix = X
        self.Y_matrix = Y
        self.Z_matrix = Z

    def get_system_matrices(self) -> Tuple[sympy.Matrix, sympy.Matrix, sympy.Matrix]:
        """
        Returns the assembled system matrices (X, Y, Z).
        """
        return self.X_matrix, self.Y_matrix, self.Z_matrix

    def __repr__(self):
        return f"EnergyHub(name='{self.name}', components={list(self.components.keys())})"