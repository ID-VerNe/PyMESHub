import sympy
from typing import Tuple, Dict, Type
from ..components.base import Component
from .energy_hub import EnergyHub

class MatrixBuilder:
    """
    Builds the system-level X, Y, Z matrices for an EnergyHub instance.
    """
    def __init__(self, energy_hub: EnergyHub):
        self.energy_hub = energy_hub

    def build_system_matrices(self) -> Tuple[sympy.Matrix, sympy.Matrix, sympy.Matrix]:
        """
        Assembles the system-level X, Y, Z symbolic matrices based on the EnergyHub's configuration.
        """
        B = len(self.energy_hub.global_branches)
        if B == 0:
            raise ValueError("No global branches defined in the EnergyHub.")

        Z_blocks = []

        # 1. Build Z matrix
        for comp_name, component in self.energy_hub.components.items():
            Hg = component.get_characteristic_matrix()
            Kg = Hg.shape[0] # Number of rows in Hg (number of conversion processes)
            # Note: Hg.shape[1] is the number of ports for this component

            # Create global Ag for this component (Kg_ports x B)
            # The Ag_global should have dimensions (number of ports of component, total number of branches)
            # The local_port_index corresponds to the column index in Hg
            num_comp_ports = Hg.shape[1]
            Ag_global = sympy.zeros(num_comp_ports, B)

            # Populate Ag_global based on port_to_global_branch_map
            # Iterate through all possible ports (input and output) of the component
            # and find their global branch index.
            
            # For input ports
            for port_name, local_port_index in component.input_ports.items():
                global_branch_index = self.energy_hub.port_to_global_branch_map.get((comp_name, port_name))
                if global_branch_index is not None:
                    Ag_global[local_port_index, global_branch_index] = 1
                else:
                    raise ValueError(f"Input port '{port_name}' of component '{comp_name}' not mapped to a global branch.")

            # For output ports
            for port_name, local_port_index in component.output_ports.items():
                global_branch_index = self.energy_hub.port_to_global_branch_map.get((comp_name, port_name))
                if global_branch_index is not None:
                    Ag_global[local_port_index, global_branch_index] = -1
                else:
                    raise ValueError(f"Output port '{port_name}' of component '{comp_name}' not mapped to a global branch.")

            Zg = Hg * Ag_global
            Z_blocks.append(Zg)
        
        if not Z_blocks:
            Z_matrix = sympy.zeros(0, B) # Empty Z if no components
        else:
            Z_matrix = sympy.Matrix.vstack(*Z_blocks)

        # 2. Build X matrix
        num_hub_inputs = len(self.energy_hub.hub_input_branch_indices)
        X_matrix = sympy.zeros(num_hub_inputs, B)
        for i, branch_index in enumerate(self.energy_hub.hub_input_branch_indices):
            X_matrix[i, branch_index] = 1

        # 3. Build Y matrix
        num_hub_outputs = len(self.energy_hub.hub_output_branch_indices)
        Y_matrix = sympy.zeros(num_hub_outputs, B)
        for i, branch_index in enumerate(self.energy_hub.hub_output_branch_indices):
            Y_matrix[i, branch_index] = 1

        self.energy_hub.set_system_matrices(X_matrix, Y_matrix, Z_matrix)
        return X_matrix, Y_matrix, Z_matrix