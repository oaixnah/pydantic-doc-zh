虽然 pydantic 可以与任何 IDE 开箱即用地良好配合，但 JetBrains 插件库中提供了一个 [PyCharm 插件](https://plugins.jetbrains.com/plugin/12861-pydantic)，可提供改进的 pydantic 集成。
您可以从插件市场免费安装该插件
(PyCharm 的 Preferences -> Plugin -> Marketplace -> 搜索 "pydantic")。

该插件目前支持以下功能：

* 对于 `pydantic.BaseModel.__init__`：
    * 检查
    * 自动补全
    * 类型检查

* 对于 `pydantic.BaseModel` 的字段：
    * 重构-重命名字段会更新 `__init__` 调用，并影响子类和超类
    * 重构-重命名 `__init__` 关键字参数会更新字段名称，并影响子类和超类

更多信息可以在
[官方插件页面](https://plugins.jetbrains.com/plugin/12861-pydantic)
和 [Github 仓库](https://github.com/koxudaxi/pydantic-pycharm-plugin) 上找到。