from collections import defaultdict
from typing import Dict, Type

import matplotlib.pyplot as plt
import networkx as nx

from ..components.base import Component
from pymeshub.components.converters import (
    CHPBackPressure, Boiler, ConvertibleLoad, ElectricBoiler, 
    HeatPump, AbsorptionChiller, Transformer, PowerToGas
)
from pymeshub.components.storage import Storage
from ..core.energy_hub import EnergyHub
from ..core.matrix_builder import MatrixBuilder  # Import for building matrices


class GraphEnergyHub:
    """
    A graph-based API for building energy hub systems.
    Uses networkx to represent the topology and facilitates component connection.
    """

    def __init__(self, name: str = "GraphEnergyHub"):
        self.name = name
        self.graph = nx.DiGraph()
        self.component_instances: Dict[str, Component] = {}
        self.component_init_args: Dict[str, Dict] = {}  # Store original init args 
        self.io_nodes: Dict[str, str] = {}  # {node_name: io_type ('input' or 'output')} 

        # Register available component types for instantiation
        self._component_types: Dict[str, Type[Component]] = {
            "CHPBackPressure": CHPBackPressure,
            "Boiler": Boiler,
            "Storage": Storage,
            "ConvertibleLoad": ConvertibleLoad,
            "ElectricBoiler": ElectricBoiler,
            "HeatPump": HeatPump,
            "AbsorptionChiller": AbsorptionChiller,
            "Transformer": Transformer,
            "PowerToGas": PowerToGas,
        }
    def add_component(self, name: str, component_type: str, **params):
        """
        Adds an energy component to the graph.
        :param name: Unique name for the component node.
        :param component_type: String identifier for the component class (e.g., "CHPBackPressure").
        :param params: Parameters to initialize the component instance.
        """
        if name in self.graph:
            raise ValueError(f"Node with name '{name}' already exists in the graph.")
        if component_type not in self._component_types:
            raise ValueError(
                f"Unknown component type: '{component_type}'. Available types: {list(self._component_types.keys())}")

        # Store init args for build() method
        self.component_init_args[name] = params

        comp_class = self._component_types[component_type]
        component_instance = comp_class(name=name, **params)
        self.component_instances[name] = component_instance

        self.graph.add_node(name, type="component", component_instance=component_instance)
        print(f"Added component '{name}' of type '{component_type}'.")

    def add_io_node(self, name: str, io_type: str):
        """
        Adds an input/output node to the graph, representing external connections.
        :param name: Unique name for the IO node.
        :param io_type: "input" or "output".
        """
        if name in self.graph:
            raise ValueError(f"Node with name '{name}' already exists in the graph.")
        if io_type not in ["input", "output"]:
            raise ValueError(f"io_type must be 'input' or 'output', got '{io_type}'.")

        self.graph.add_node(name, type="io", io_type=io_type)
        self.io_nodes[name] = io_type
        print(f"Added {io_type} node '{name}'.")

    def connect(self, from_node: str, from_port: str, to_node: str, to_port: str):
        """
        Connects a port of one node (component or IO) to a port of another node.
        This creates a 'branch' in the energy hub model.
        :param from_node: Name of the source node.
        :param from_port: Name of the output port on the source node.
        :param to_node: Name of the destination node.
        :param to_port: Name of the input port on the destination node.
        """
        if from_node not in self.graph:
            raise ValueError(f"Source node '{from_node}' not found.")
        if to_node not in self.graph:
            raise ValueError(f"Destination node '{to_node}' not found.")

        # Validate ports for components
        from_node_type = self.graph.nodes[from_node]['type']
        to_node_type = self.graph.nodes[to_node]['type']

        if from_node_type == "component":
            comp = self.component_instances[from_node]
            if from_port not in comp.output_ports:
                raise ValueError(f"Port '{from_port}' is not an output port of component '{from_node}'.")
        elif from_node_type == "io" and self.io_nodes[from_node] != "input":
            raise ValueError(f"IO node '{from_node}' is not an input node, cannot be a source.")

        if to_node_type == "component":
            comp = self.component_instances[to_node]
            if to_port not in comp.input_ports:
                raise ValueError(f"Port '{to_port}' is not an input port of component '{to_node}'.")
        elif to_node_type == "io" and self.io_nodes[to_node] != "output":
            raise ValueError(f"IO node '{to_node}' is not an output node, cannot be a destination.")

        # Add edge to graph representing the connection (branch)
        # The edge key will be the branch name, which we'll generate uniquely
        branch_name = f"{from_node}_{from_port}_to_{to_node}_{to_port}"
        self.graph.add_edge(from_node, to_node, from_port=from_port, to_port=to_port, branch_name=branch_name)
        print(f"Connected {from_node}.{from_port} to {to_node}.{to_port} via branch '{branch_name}'.")

    def visualize(self):
        """
        Draws the energy hub topology using a structured, layered layout similar to Simulink.
        """
        if not self.graph.nodes:
            print("Graph is empty, nothing to visualize.")
            return

        # --- 1. Manually calculate node positions for a layered layout ---
        pos = {}
        nodes_by_layer = defaultdict(list)

        # Use a robust method to determine layers
        for node in nx.topological_sort(self.graph):
            is_input = not any(self.graph.predecessors(node))
            if is_input:
                layer = 0
            else:
                layer = 1 + max(
                    [nodes_by_layer[l].index(pred) for l in nodes_by_layer for pred in self.graph.predecessors(node) if
                     pred in nodes_by_layer[l]]
                )

            # A more robust layering by finding the longest path from any source node
            layer = 0
            for source_node in [n for n, d in self.graph.in_degree() if d == 0]:
                try:
                    path_len = len(nx.shortest_path(self.graph, source=source_node, target=node)) - 1
                    layer = max(layer, path_len)
                except nx.NetworkXNoPath:
                    continue
            nodes_by_layer[layer].append(node)

        # Assign positions based on layers
        x_spacing = 2.0
        y_spacing = 1.5
        for layer, nodes in nodes_by_layer.items():
            num_nodes_in_layer = len(nodes)
            for i, node in enumerate(nodes):
                pos[node] = (layer * x_spacing, (num_nodes_in_layer / 2 - i) * y_spacing)

        # --- 2. Define node styles ---
        node_size = 5000
        component_nodes = [n for n, d in self.graph.nodes(data=True) if d['type'] == 'component']
        input_nodes = [n for n, d in self.graph.nodes(data=True) if d.get('io_type') == 'input']
        output_nodes = [n for n, d in self.graph.nodes(data=True) if d.get('io_type') == 'output']

        plt.figure(figsize=(12, 8))

        # --- 3. Draw components ---
        # Nodes with borders
        nx.draw_networkx_nodes(self.graph, pos, nodelist=component_nodes, node_color='skyblue', node_shape='s',
                               node_size=node_size, edgecolors='black', linewidths=1.5)
        nx.draw_networkx_nodes(self.graph, pos, nodelist=input_nodes, node_color='lightgreen', node_shape='>',
                               node_size=node_size, edgecolors='black', linewidths=1.5)
        nx.draw_networkx_nodes(self.graph, pos, nodelist=output_nodes, node_color='lightcoral', node_shape='<',
                               node_size=node_size, edgecolors='black', linewidths=1.5)

        # Edges pointing to the node border
        nx.draw_networkx_edges(self.graph, pos, arrowstyle='->', arrowsize=20, edge_color='black', width=2,
                               node_size=node_size + 1200)  # node_size helps adjust arrow start/end

        # Node labels
        nx.draw_networkx_labels(self.graph, pos, font_size=12, font_weight='bold')

        # Edge labels
        edge_labels = {}
        for u, v, data in self.graph.edges(data=True):
            from_port = data.get('from_port', 'out')
            to_port = data.get('to_port', 'in')
            edge_labels[(u, v)] = f"{from_port} -> {to_port}"

        nx.draw_networkx_edge_labels(self.graph, pos, edge_labels=edge_labels, font_color='#555555', font_size=9,
                                     bbox=dict(facecolor='white', alpha=0.6, edgecolor='none', pad=1))

        plt.title(f"Energy Hub Topology: {self.name}", size=18, pad=20)
        plt.tight_layout()
        plt.axis('off')
        plt.show()

    def build(self) -> EnergyHub:
        """
        Compiles the graph representation into an EnergyHub instance with assembled matrices.
        This method implements Task 3 of Phase 2.
        """
        print("\n--- Building EnergyHub from Graph ---")
        config = {
            'components': [],
            'branches': [],
            'port_mappings': defaultdict(dict),
            'hub_inputs': [],
            'hub_outputs': []
        }

        # 1. Populate config['components']
        for comp_name, comp_instance in self.component_instances.items():
            config['components'].append({
                'name': comp_name,
                'type': comp_instance.__class__.__name__,
                'params': self.component_init_args[comp_name]  # Use original init args
            })

        # 2. Identify branches and port_mappings, hub_inputs/outputs
        for u, v, edge_data in self.graph.edges(data=True):
            branch_name = edge_data['branch_name']
            config['branches'].append(branch_name)

            # Map component ports to this branch
            if self.graph.nodes[u]['type'] == 'component':
                from_port = edge_data['from_port']
                config['port_mappings'][u][from_port] = branch_name

            if self.graph.nodes[v]['type'] == 'component':
                to_port = edge_data['to_port']
                config['port_mappings'][v][to_port] = branch_name

            # Identify hub inputs/outputs
            if self.graph.nodes[u]['type'] == 'io' and self.graph.nodes[u]['io_type'] == 'input':
                config['hub_inputs'].append(branch_name)
            if self.graph.nodes[v]['type'] == 'io' and self.graph.nodes[v]['io_type'] == 'output':
                config['hub_outputs'].append(branch_name)

        # Handle virtual ports for Storage components
        for comp_name, comp_instance in self.component_instances.items():
            if isinstance(comp_instance, Storage):
                # Assuming 'delta_soc' is the virtual port for Storage
                virtual_port_name = 'delta_soc'
                virtual_branch_name = f"{comp_name}_{virtual_port_name}_branch"

                # Add virtual branch to config
                config['branches'].append(virtual_branch_name)

                # Map virtual port to virtual branch
                config['port_mappings'][comp_name][virtual_port_name] = virtual_branch_name

        # Ensure branches are unique and ordered consistently
        config['branches'] = sorted(list(set(config['branches'])))
        config['hub_inputs'] = sorted(list(set(config['hub_inputs'])))
        config['hub_outputs'] = sorted(list(set(config['hub_outputs'])))

        print("Generated Configuration:")
        print(config)

        # 3. Create and populate EnergyHub
        hub = EnergyHub(self.name)
        hub.load_config(config, self._component_types)

        # 4. Build system matrices using MatrixBuilder
        builder = MatrixBuilder(hub)
        builder.build_system_matrices()

        print("EnergyHub built successfully with matrices.")
        return hub
