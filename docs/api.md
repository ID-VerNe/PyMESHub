# PyMESHub 详细接口文档

本文档详细介绍了 PyMESHub 框架的核心概念、API使用方法以及如何进行扩展。

## 1. 核心概念：标准化矩阵建模

本框架严格遵循标准化矩阵建模理论。一个能源枢纽系统被抽象为三组核心方程：

1.  **能量转换与平衡**: `Z * V = 0`
    *   `Z` 是系统能量转换矩阵，描述了能量在每个组件内部如何从输入端口转换为输出端口。
    *   `V` 是系统中所有能量流（即支路）的向量。
    *   此方程确保了每个组件内部的能量守恒。

2.  **枢纽输入**: `V_in = X * V`
    *   `X` 是输入关联矩阵，它从所有能量流 `V` 中挑选出作为整个系统输入的能量流。

3.  **枢纽输出**: `V_out = Y * V`
    *   `Y` 是输出关联矩阵，它从所有能量流 `V` 中挑选出作为整个系统输出的能量流。

`PyMESHub` 的核心价值在于，您只需要通过图的方式定义系统拓扑，框架会自动为您推导出 `X`, `Y`, `Z` 三个关键矩阵，无论是数值形式还是符号形式。

---

## 2. `GraphEnergyHub` API详解

`GraphEnergyHub` 是用户与框架交互的主要入口。它提供了一套直观的方法来“绘制”您的能源系统。

### `__init__(self, name: str)`

*   **功能**: 创建一个新的、空的能源枢纽图模型。
*   **参数**:
    *   `name` (str): 为您的能源枢纽命名。

### `add_component(self, name: str, component_type: str, **params)`

*   **功能**: 在图中添加一个能源转换或存储组件（例如，一个CHP或锅炉）。
*   **参数**:
    *   `name` (str): 组件的唯一名称，例如 `'CHP1'`。
    *   `component_type` (str): 组件的类型，必须是框架中已注册的类型。当前支持：`'CHPBackPressure'`, `'Boiler'`, `'Storage'`。
    *   `**params`: 一个关键字参数字典，用于定义该组件的物理属性。例如，对于 `CHPBackPressure`，您需要提供 `eta_q` 和 `eta_w`。

### `add_io_node(self, name: str, io_type: str)`

*   **功能**: 添加一个输入或输出节点，代表系统的外部边界。
*   **参数**:
    *   `name` (str): IO节点的唯一名称，例如 `'GasInput'` 或 `'ElecLoad'`。
    *   `io_type` (str): 必须是 `'input'` 或 `'output'`。

### `connect(self, from_node: str, from_port: str, to_node: str, to_port: str)`

*   **功能**: 连接两个节点，在它们之间创建一条能量流（支路）。这是定义系统拓扑最核心的方法。
*   **参数**:
    *   `from_node` (str): 源节点的名称。
    *   `from_port` (str): 源节点上的输出端口名称。
    *   `to_node` (str): 目标节点的名称。
    *   `to_port` (str): 目标节点上的输入端口名称。

### `visualize(self)`

*   **功能**: 使用 `matplotlib` 和 `networkx` 绘制能源枢纽的拓扑图，并以分层、结构化的方式显示。

### `build(self) -> EnergyHub`

*   **功能**: “编译”用户通过 `connect` 等方法定义的图。它会遍历图，自动生成配置字典，并最终创建一个包含所有系统矩阵 (`X`, `Y`, `Z`) 的 `EnergyHub` 实例。
*   **返回**: 一个功能完备的 `EnergyHub` 对象，可用于后续的分析或优化。

---

## 3. 如何自定义能源组件

扩展 `PyMESHub` 的最佳方式就是添加您自己的组件。这非常简单，只需要遵循以下步骤：

**目标**: 创建一个代表光伏板（PV）的新组件。

1.  **创建文件**: 在 `pymeshub/components/` 目录下创建一个新文件，例如 `sources.py`。

2.  **编写类定义**: 在 `sources.py` 中，创建一个继承自 `pymeshub.components.base.Component` 的新类。

    ```python
    import sympy
    from .base import Component

    class PV(Component):
        """
        光伏板组件。
        它没有能量输入端口，只有一个输出端口。
        在模型中，它的输出通常被视为一个不受控制的、给定的输入（负荷）。
        但为了模型的完整性，我们将其建模为一个只有输出的转换器。
        """
        def __init__(self, name: str):
            super().__init__(name)
            # 光伏板只有一个输出端口
            self.add_output_port('elec_out', 0)

        def get_port_branch_matrix(self) -> sympy.Matrix:
            """
            定义端口与内部支路的关联矩阵 (Ag)。
            对于只有一个端口的组件，这通常是一个 1x1 的矩阵。
            端口 'elec_out' (索引0) 是从内部支路0的输出。
            """
            return sympy.Matrix([[-1]])

        def get_characteristic_matrix(self) -> sympy.Matrix:
            """
            定义组件的特性矩阵 (Hg)。
            对于PV这种源，它没有输入-输出转换关系，因此其能量平衡方程是 V_out = P_pv。
            在我们的框架中，这通过在优化阶段直接约束该支路的值来实现。
            因此，Hg 是一个空的矩阵，表示没有内部转换约束。
            """
            return sympy.Matrix([])
    ```

3.  **注册新组件**

    为了让 `GraphEnergyHub` 能够通过字符串 `'PV'` 找到您的新类，您需要在使用它之前进行注册。最简单的方法是在您的主脚本中手动注册：

    ```python
    from pymeshub.graph.builder import GraphEnergyHub
    from pymeshub.components.sources import PV # 假设您创建了该文件

    # ...
    graph_hub = GraphEnergyHub()
    graph_hub._component_types['PV'] = PV # 手动注册

    graph_hub.add_component(name='PV_array_1', component_type='PV')
    # ...
    ```

通过以上三个步骤，您就可以将任何自定义的能源设备无缝集成到 `PyMESHub` 框架中，并利用其强大的建模和分析能力。
