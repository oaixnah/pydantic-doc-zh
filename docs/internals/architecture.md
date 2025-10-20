---
subtitle: 架构
---

!!! note
    本节是*内部*文档的一部分，主要面向贡献者。

从 Pydantic V2 开始，部分代码库使用 Rust 编写，并放在一个名为 `pydantic-core` 的独立包中。
这样做主要是为了提高验证和序列化的性能（代价是内部逻辑的自定义性和可扩展性有限）。

本架构文档将首先介绍 `pydantic` 和 `pydantic-core` 这两个包如何交互，
然后详细介绍各种模式的架构细节（模型定义、验证、序列化、JSON Schema）。

Pydantic 库的使用可以分为两个部分：

* 模型定义，在 `pydantic` 包中完成。
* 模型验证和序列化，在 `pydantic-core` 包中完成。

## 模型定义

每当定义一个 Pydantic [`BaseModel`][pydantic.main.BaseModel] 时，元类
会分析模型的主体以收集多个元素：

* 定义的注解以构建模型字段（收集在 [`model_fields`][pydantic.main.BaseModel.model_fields] 属性中）。
* 模型配置，通过 [`model_config`][pydantic.main.BaseModel.model_config] 设置。
* 额外的验证器/序列化器。
* 私有属性、类变量、泛型参数化的识别等。

### `pydantic` 和 `pydantic-core` 之间的通信：核心模式 {#communicating-between-pydantic-and-pydantic-core-the-core-schema}

我们需要一种方式将模型定义中收集的信息传递给 `pydantic-core`，
以便相应地执行验证和序列化。为此，Pydantic 使用了核心模式的概念：
一个结构化的（可序列化的）Python 字典（使用 [`TypedDict`][typing.TypedDict] 定义表示），
描述特定的验证和序列化逻辑。它是 `pydantic` 和 `pydantic-core` 包之间通信的核心数据结构。
每个核心模式都有一个必需的 `type` 键，以及根据此 `type` 的额外属性。

核心模式的生成由 `GenerateSchema` 类在单个地方处理
（无论是用于 Pydantic 模型还是其他任何东西）。

!!! note
    无法定义自定义核心模式。核心模式需要被 `pydantic-core` 包理解，
    因此我们只支持固定数量的核心模式类型。
    这也是 `GenerateSchema` 没有真正公开和适当文档化的部分原因。

    核心模式定义可以在 [`pydantic_core.core_schema`][] 模块中找到。

对于 Pydantic 模型，将构建一个核心模式并设置为
[`__pydantic_core_schema__`][pydantic.main.BaseModel.__pydantic_core_schema__] 属性。

为了说明核心模式的样子，我们将以 [`bool`][pydantic_core.core_schema.bool_schema] 核心模式为例：

```python {lint="skip" test="skip"}
class BoolSchema(TypedDict, total=False):
    type: Required[Literal['bool']]
    strict: bool
    ref: str
    metadata: Any
    serialization: SerSchema
```

当定义一个带有布尔字段的 Pydantic 模型时：

```python
from pydantic import BaseModel, Field


class Model(BaseModel):
    foo: bool = Field(strict=True)
```

`foo` 字段的核心模式将如下所示：

```python
{
    'type': 'bool',
    'strict': True,
}
```

如 [`BoolSchema`][pydantic_core.core_schema.bool_schema] 定义所示，
序列化逻辑也在核心模式中定义。
如果我们要为 `foo` 定义一个自定义序列化函数 (1)，`serialization` 键将如下所示：
{ .annotate }

1. 例如使用 [`field_serializer`][pydantic.functional_serializers.field_serializer] 装饰器：

    ```python {test="skip" lint="skip"}
    class Model(BaseModel):
        foo: bool = Field(strict=True)

        @field_serializer('foo', mode='plain')
        def serialize_foo(self, value: bool) -> Any:
            ...
    ```

```python {lint="skip" test="skip"}
{
    'type': 'function-plain',
    'function': <function Model.serialize_foo at 0x111>,
    'is_field_serializer': True,
    'info_arg': False,
    'return_schema': {'type': 'int'},
}
```

请注意，这也是一个核心模式定义，只是它仅在序列化期间与 `pydantic-core` 相关。

核心模式涵盖广泛的范围，并且在我们想要在 Python 和 Rust 端之间通信时使用。
虽然前面的示例与验证和序列化相关，但理论上它可以用于任何事情：
错误管理、额外元数据等。

### JSON Schema 生成

您可能已经注意到，之前的序列化核心模式有一个 `return_schema` 键。
这是因为核心模式也用于生成相应的 JSON Schema。

与核心模式的生成类似，JSON Schema 的生成由
[`GenerateJsonSchema`][pydantic.json_schema.GenerateJsonSchema] 类处理。
[`generate`][pydantic.json_schema.GenerateJsonSchema.generate] 方法
是主要入口点，并接收该模型的核心模式。

回到我们的 `bool` 字段示例，[`bool_schema`][pydantic.json_schema.GenerateJsonSchema.bool_schema]
方法将接收先前生成的[布尔核心模式][pydantic_core.core_schema.bool_schema]
并返回以下 JSON Schema：

```json
{
    {"type": "boolean"}
}
```

### 自定义核心模式和 JSON 模式

!!! abstract "使用文档"
    [自定义类型](../concepts/types.md#custom-types)

    [实现 `__get_pydantic_core_schema__`](../concepts/json_schema.md#implementing_get_pydantic_core_schema)

    [实现 `__get_pydantic_json_schema__`](../concepts/json_schema.md#implementing_get_pydantic_json_schema)

虽然 `GenerateSchema` 和 [`GenerateJsonSchema`][pydantic.json_schema.GenerateJsonSchema] 类处理
相应模式的创建，但 Pydantic 在某些情况下提供了一种自定义它们的方式，遵循包装器模式。
这种自定义通过 `__get_pydantic_core_schema__` 和 `__get_pydantic_json_schema__` 方法完成。

为了理解这种包装器模式，我们将以与 [`Annotated`][typing.Annotated] 一起使用的元数据类为例，
其中可以使用 `__get_pydantic_core_schema__` 方法：

```python
from typing import Annotated, Any

from pydantic_core import CoreSchema

from pydantic import GetCoreSchemaHandler, TypeAdapter


class MyStrict:
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        schema = handler(source)  # (1)!
        schema['strict'] = True
        return schema


class MyGt:
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        schema = handler(source)  # (2)!
        schema['gt'] = 1
        return schema


ta = TypeAdapter(Annotated[int, MyStrict(), MyGt()])
```

1. `MyStrict` 是要应用的第一个注解。此时，`schema = {'type': 'int'}`。
2. `MyGt` 是要应用的最后一个注解。此时，`schema = {'type': 'int', 'strict': True}`。

当 `GenerateSchema` 类为 `Annotated[int, MyStrict(), MyGt()]` 构建核心模式时，它将
创建一个 `GetCoreSchemaHandler` 实例传递给 `MyGt.__get_pydantic_core_schema__` 方法。(1)
{ .annotate }

1. 在我们的 [`Annotated`][typing.Annotated] 模式的情况下，`GetCoreSchemaHandler` 是以嵌套方式定义的。
    调用它将递归调用其他 `__get_pydantic_core_schema__` 方法，直到达到 `int` 注解，
    此时返回一个简单的 `{'type': 'int'}` 模式。

`source` 参数取决于核心模式生成模式。在 [`Annotated`][typing.Annotated] 的情况下，
`source` 将是被注解的类型。当[定义自定义类型](../concepts/types.md#as-a-method-on-a-custom-type)时，
`source` 将是实际定义 `__get_pydantic_core_schema__` 的类。

## 模型验证和序列化

虽然模型定义是在*类*级别（即定义模型时）进行的，但模型验证
和序列化发生在*实例*级别。这两个概念都在 `pydantic-core` 中处理
（与 Pydantic V1 相比，性能提高了 5 到 20 倍），通过使用先前构建的核心模式。

`pydantic-core` 公开了 [`SchemaValidator`][pydantic_core.SchemaValidator] 和
[`SchemaSerializer`][pydantic_core.SchemaSerializer] 类来执行这些任务：

```python
from pydantic import BaseModel


class Model(BaseModel):
    foo: int


model = Model.model_validate({'foo': 1})  # (1)!
dumped = model.model_dump()  # (2)!
```

1. 提供的数据通过使用 [`SchemaValidator.validate_python`][pydantic_core.SchemaValidator.validate_python] 方法发送到 `pydantic-core`。
   `pydantic-core` 将验证（遵循模型的核心模式）数据并填充
   模型的 `__dict__` 属性。
2. `model` 实例通过使用 [`SchemaSerializer.to_python`][pydantic_core.SchemaSerializer.to_python] 方法发送到 `pydantic-core`。
   `pydantic-core` 将读取实例的 `__dict__` 属性并构建适当的结果
   （再次遵循模型的核心模式）。