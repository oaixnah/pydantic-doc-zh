---
description: Pydantic TypeAdapter 是一个强大的工具，用于验证非 BaseModel 类型的数据，支持数据类、原始类型和复杂类型如 list[SomeModel]。它提供类型验证、序列化和 JSON 模式生成功能，无需创建 BaseModel。TypeAdapter 可以解析数据到指定类型，支持延迟模式构建以提高性能，适用于临时数据验证场景。
---

您可能有一些不是 `BaseModel` 的类型，但您想要验证数据是否符合这些类型。或者您可能想要验证 `list[SomeModel]`，或者将其转储为 JSON。

??? api "API 文档"
    [`pydantic.type_adapter.TypeAdapter`][pydantic.type_adapter.TypeAdapter]<br>

对于这样的使用场景，Pydantic 提供了 [`TypeAdapter`][pydantic.type_adapter.TypeAdapter]，
它可以用于类型验证、序列化和 JSON 模式生成，而无需创建
[`BaseModel`][pydantic.main.BaseModel]。

一个 [`TypeAdapter`][pydantic.type_adapter.TypeAdapter] 实例暴露了来自
[`BaseModel`][pydantic.main.BaseModel] 实例方法的一些功能，适用于那些没有此类方法的类型
（例如数据类、原始类型等）：

```python
from typing_extensions import TypedDict

from pydantic import TypeAdapter, ValidationError


class User(TypedDict):
    name: str
    id: int


user_list_adapter = TypeAdapter(list[User])
user_list = user_list_adapter.validate_python([{'name': 'Fred', 'id': '3'}])
print(repr(user_list))
#> [{'name': 'Fred', 'id': 3}]

try:
    user_list_adapter.validate_python(
        [{'name': 'Fred', 'id': 'wrong', 'other': 'no'}]
    )
except ValidationError as e:
    print(e)
    """
    1 validation error for list[User]
    0.id
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='wrong', input_type=str]
    """

print(repr(user_list_adapter.dump_json(user_list)))
#> b'[{"name":"Fred","id":3}]'
```

!!! info "`dump_json` 返回 `bytes`"
    `TypeAdapter` 的 `dump_json` 方法返回一个 `bytes` 对象，这与 `BaseModel` 的对应方法 `model_dump_json` 不同，后者返回一个 `str`。
    这种差异的原因是，在 V1 中，模型转储返回的是 str 类型，因此在 V2 中保留了这种行为以保持向后兼容性。
    对于 `BaseModel` 的情况，`bytes` 被强制转换为 `str` 类型，但 `bytes` 通常是所需的最终类型。
    因此，对于 V2 中的新 `TypeAdapter` 类，返回类型只是 `bytes`，如果需要可以轻松地强制转换为 `str` 类型。

!!! note
    尽管与 [`RootModel`][pydantic.root_model.RootModel] 在使用场景上有一些重叠，
    [`TypeAdapter`][pydantic.type_adapter.TypeAdapter] 不应被用作类型注解来
    指定 `BaseModel` 的字段等。

## 解析数据到指定类型

[`TypeAdapter`][pydantic.type_adapter.TypeAdapter] 可用于以更临时的方式应用解析逻辑来填充 Pydantic 模型。
此函数的行为类似于
[`BaseModel.model_validate`][pydantic.main.BaseModel.model_validate]，
但适用于任意 Pydantic 兼容的类型。

当您想要将结果解析为不是 [`BaseModel`][pydantic.main.BaseModel] 直接子类的类型时，这尤其有用。例如：

```python
from pydantic import BaseModel, TypeAdapter


class Item(BaseModel):
    id: int
    name: str


# `item_data` 可能来自 API 调用，例如通过类似以下方式：
# item_data = requests.get('https://my-api.com/items').json()
item_data = [{'id': 1, 'name': 'My Item'}]

items = TypeAdapter(list[Item]).validate_python(item_data)
print(items)
#> [Item(id=1, name='My Item')]
```

[`TypeAdapter`][pydantic.type_adapter.TypeAdapter] 能够将数据解析为 Pydantic 可以
作为 [`BaseModel`][pydantic.main.BaseModel] 字段处理的任何类型。

!!! info "性能考虑"
    当创建 [`TypeAdapter`][pydantic.type_adapter.TypeAdapter] 实例时，提供的类型必须被分析并转换为 pydantic-core
    模式。这会带来一些不小的开销，因此建议为给定类型只创建一次 `TypeAdapter`
    并在循环或其他性能关键代码中重复使用它。

## 重建 `TypeAdapter` 的模式

在 v2.10+ 中，[`TypeAdapter`][pydantic.type_adapter.TypeAdapter] 支持延迟模式构建和手动重建。这对于以下情况很有帮助：

* 具有前向引用的类型
* 核心模式构建成本较高的类型

当您使用类型初始化 [`TypeAdapter`][pydantic.type_adapter.TypeAdapter] 时，Pydantic 会分析该类型并为其创建核心模式。
此核心模式包含验证和序列化该类型数据所需的信息。
有关核心模式的更多信息，请参阅[架构文档](../internals/architecture.md)。

如果在初始化 `TypeAdapter` 时将 [`defer_build`][pydantic.config.ConfigDict.defer_build] 设置为 `True`，
Pydantic 将延迟构建核心模式，直到第一次需要它时（用于验证或序列化）。

为了手动触发核心模式的构建，您可以调用
[`TypeAdapter`][pydantic.type_adapter.TypeAdapter] 实例上的 [`rebuild`][pydantic.type_adapter.TypeAdapter.rebuild] 方法：

```python
from pydantic import ConfigDict, TypeAdapter

ta = TypeAdapter('MyInt', config=ConfigDict(defer_build=True))

# 一段时间后，前向引用被定义
MyInt = int

ta.rebuild()
assert ta.validate_python(1) == 1
```