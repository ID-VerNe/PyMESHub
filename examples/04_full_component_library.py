# examples/04_full_component_library.py

from pymeshub.graph.builder import GraphEnergyHub

if __name__ == "__main__":
    print("--- Running Full Component Library Example ---")

    # 1. Initialize the graph-based hub builder
    graph_hub = GraphEnergyHub(name="ComplexEnergyHub")

    # 2. Add components using the expanded library
    graph_hub.add_component(name='CHP', component_type='CHPBackPressure', eta_q=0.5, eta_w=0.4)
    graph_hub.add_component(name='GasBoiler', component_type='Boiler', eta=0.9)
    graph_hub.add_component(name='ElecBoiler', component_type='ElectricBoiler', eta=0.98)
    graph_hub.add_component(name='HeatPump', component_type='HeatPump', cop=3.5)
    graph_hub.add_component(name='AbsChiller', component_type='AbsorptionChiller', cop=0.8)
    graph_hub.add_component(name='Transformer', component_type='Transformer', eta=0.99)
    graph_hub.add_component(name='P2G', component_type='PowerToGas', eta=0.6)
    graph_hub.add_component(name='ElecStorage', component_type='Storage', eta_c=0.95, eta_d=0.92)

    # 3. Add IO nodes for various energy carriers
    graph_hub.add_io_node(name='GridElec', io_type='input')
    graph_hub.add_io_node(name='GasSource', io_type='input')
    graph_hub.add_io_node(name='DistrictHeat', io_type='input')

    graph_hub.add_io_node(name='ElecDemand', io_type='output')
    graph_hub.add_io_node(name='HeatDemand', io_type='output')
    graph_hub.add_io_node(name='CoolDemand', io_type='output')
    graph_hub.add_io_node(name='GasDemand', io_type='output')

    # 4. Connect the components in a logical way
    # Inputs to converters
    graph_hub.connect('GasSource', 'out', 'CHP', 'fuel_in')
    graph_hub.connect('GasSource', 'out', 'GasBoiler', 'fuel_in')
    graph_hub.connect('GridElec', 'out', 'Transformer', 'elec_in')
    graph_hub.connect('Transformer', 'elec_out', 'HeatPump', 'elec_in')
    graph_hub.connect('Transformer', 'elec_out', 'ElecBoiler', 'elec_in')
    graph_hub.connect('Transformer', 'elec_out', 'P2G', 'elec_in')
    graph_hub.connect('Transformer', 'elec_out', 'ElecStorage', 'energy_in')
    graph_hub.connect('DistrictHeat', 'out', 'AbsChiller', 'heat_in')

    # Converters to demands
    graph_hub.connect('CHP', 'heat_out', 'HeatDemand', 'in')
    graph_hub.connect('GasBoiler', 'heat_out', 'HeatDemand', 'in')
    graph_hub.connect('ElecBoiler', 'heat_out', 'HeatDemand', 'in')
    graph_hub.connect('HeatPump', 'heat_out', 'HeatDemand', 'in')
    graph_hub.connect('CHP', 'elec_out', 'ElecDemand', 'in')
    graph_hub.connect('ElecStorage', 'energy_out', 'ElecDemand', 'in')
    graph_hub.connect('AbsChiller', 'cool_out', 'CoolDemand', 'in')
    graph_hub.connect('P2G', 'gas_out', 'GasDemand', 'in')

    # 5. Visualize the graph topology
    graph_hub.visualize()

    # 6. Build the EnergyHub instance (optional, for matrix generation)
    hub = graph_hub.build()
    X, Y, Z = hub.get_system_matrices()
    print("\nZ Matrix Shape:", Z.shape)
    # print("Z Matrix:\n", Z)

    print("\nComplex energy hub graph built and visualized successfully.")
