---
description: Pydantic JSON Schema 文档：学习如何从 Pydantic 模型自动生成和自定义 JSON Schema，包括字段级别和模型级别的自定义选项、TypeAdapter 使用、JSON Schema 模式配置、自定义类型处理以及完整的 JSON Schema 生成过程控制。符合 JSON Schema Draft 2020-12和OpenAPI Specification v3.1.0 标准。
---

??? api "API 文档"
    [`pydantic.json_schema`][pydantic.json_schema]<br>

Pydantic 允许从模型自动创建和自定义 JSON 模式。
生成的 JSON 模式符合以下规范：

* [JSON Schema Draft 2020-12](https://json-schema.org/draft/2020-12/release-notes.html)
* [OpenAPI Specification v3.1.0](https://github.com/OAI/OpenAPI-Specification)

## 生成 JSON 模式

使用以下函数生成 JSON 模式：

* [`BaseModel.model_json_schema`][pydantic.main.BaseModel.model_json_schema] 返回模型模式的可 JSON 化字典
* [`TypeAdapter.json_schema`][pydantic.type_adapter.TypeAdapter.json_schema] 返回适配类型的可 JSON 化字典

!!! note
    这些方法不要与 [`BaseModel.model_dump_json`][pydantic.main.BaseModel.model_dump_json]
    和 [`TypeAdapter.dump_json`][pydantic.type_adapter.TypeAdapter.dump_json] 混淆，后者分别序列化模型或适配类型的实例。
    这些方法返回 JSON 字符串。相比之下，
    [`BaseModel.model_json_schema`][pydantic.main.BaseModel.model_json_schema] 和
    [`TypeAdapter.json_schema`][pydantic.type_adapter.TypeAdapter.json_schema] 返回表示模型或适配类型 JSON 模式的可 JSON 化字典。

!!! note "关于 JSON 模式的"可 JSON 化"特性"
    关于 [`model_json_schema`][pydantic.main.BaseModel.model_json_schema] 结果的"可 JSON 化"特性，
    在某些 `BaseModel` `m` 上调用 `json.dumps(m.model_json_schema())` 会返回有效的 JSON 字符串。类似地，对于
    [`TypeAdapter.json_schema`][pydantic.type_adapter.TypeAdapter.json_schema]，调用
    `json.dumps(TypeAdapter(<some_type>).json_schema())` 也会返回有效的 JSON 字符串。

!!! tip
    Pydantic 提供对以下两者的支持：

    1. [自定义 JSON 模式](#customizing-json-schema)
    2. [自定义 JSON 模式生成过程](#customizing-the-json-schema-generation-process)

    第一种方法通常范围较窄，允许为更具体的用例和类型自定义 JSON 模式。
    第二种方法通常范围更广，允许自定义整个 JSON 模式生成过程。
    两种方法都可以实现相同的效果，但根据您的用例，一种方法可能比另一种提供更简单的解决方案。

以下是从 `BaseModel` 生成 JSON 模式的示例：

```python {output="json"}
import json
from enum import Enum
from typing import Annotated, Union

from pydantic import BaseModel, Field
from pydantic.config import ConfigDict


class FooBar(BaseModel):
    count: int
    size: Union[float, None] = None


class Gender(str, Enum):
    male = 'male'
    female = 'female'
    other = 'other'
    not_given = 'not_given'


class MainModel(BaseModel):
    """
    This is the description of the main model
    """

    model_config = ConfigDict(title='Main')

    foo_bar: FooBar
    gender: Annotated[Union[Gender, None], Field(alias='Gender')] = None
    snap: int = Field(
        default=42,
        title='The Snap',
        description='this is the value of snap',
        gt=30,
        lt=50,
    )


main_model_schema = MainModel.model_json_schema()  # (1)!
print(json.dumps(main_model_schema, indent=2))  # (2)!
"""
{
  "$defs": {
    "FooBar": {
      "properties": {
        "count": {
          "title": "Count",
          "type": "integer"
        },
        "size": {
          "anyOf": [
            {
              "type": "number"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Size"
        }
      },
      "required": [
        "count"
      ],
      "title": "FooBar",
      "type": "object"
    },
    "Gender": {
      "enum": [
        "male",
        "female",
        "other",
        "not_given"
      ],
      "title": "Gender",
      "type": "string"
    }
  },
  "description": "This is the description of the main model",
  "properties": {
    "foo_bar": {
      "$ref": "#/$defs/FooBar"
    },
    "Gender": {
      "anyOf": [
        {
          "$ref": "#/$defs/Gender"
        },
        {
          "type": "null"
        }
      ],
      "default": null
    },
    "snap": {
      "default": 42,
      "description": "this is the value of snap",
      "exclusiveMaximum": 50,
      "exclusiveMinimum": 30,
      "title": "The Snap",
      "type": "integer"
    }
  },
  "required": [
    "foo_bar"
  ],
  "title": "Main",
  "type": "object"
}
"""
```

1. 这会生成 `MainModel` 模式的"可 JSON 化"字典。
2. 在模式字典上调用 `json.dumps` 会生成 JSON 字符串。

[`TypeAdapter`][pydantic.type_adapter.TypeAdapter] 类允许您创建一个对象，该对象具有验证、序列化和为任意类型生成 JSON 模式的方法。
这完全替代了 Pydantic V1 中的 `schema_of`（现已弃用）。

以下是从 [`TypeAdapter`][pydantic.type_adapter.TypeAdapter] 生成 JSON 模式的示例：

```python
from pydantic import TypeAdapter

adapter = TypeAdapter(list[int])
print(adapter.json_schema())
#> {'items': {'type': 'integer'}, 'type': 'array'}
```

您还可以为 [`BaseModel`s][pydantic.main.BaseModel] 和 [`TypeAdapter`s][pydantic.type_adapter.TypeAdapter] 的组合生成 JSON 模式，
如以下示例所示：

```python {output="json"}
import json
from typing import Union

from pydantic import BaseModel, TypeAdapter


class Cat(BaseModel):
    name: str
    color: str


class Dog(BaseModel):
    name: str
    breed: str


ta = TypeAdapter(Union[Cat, Dog])
ta_schema = ta.json_schema()
print(json.dumps(ta_schema, indent=2))
"""
{
  "$defs": {
    "Cat": {
      "properties": {
        "name": {
          "title": "Name",
          "type": "string"
        },
        "color": {
          "title": "Color",
          "type": "string"
        }
      },
      "required": [
        "name",
        "color"
      ],
      "title": "Cat",
      "type": "object"
    },
    "Dog": {
      "properties": {
        "name": {
          "title": "Name",
          "type": "string"
        },
        "breed": {
          "title": "Breed",
          "type": "string"
        }
      },
      "required": [
        "name",
        "breed"
      ],
      "title": "Dog",
      "type": "object"
    }
  },
  "anyOf": [
    {
      "$ref": "#/$defs/Cat"
    },
    {
      "$ref": "#/$defs/Dog"
    }
  ]
}
"""
```

### 配置 `JsonSchemaMode`

通过 [`model_json_schema`][pydantic.main.BaseModel.model_json_schema] 和
[`TypeAdapter.json_schema`][pydantic.type_adapter.TypeAdapter.json_schema] 方法中的 `mode` 参数指定 JSON 模式生成模式。
默认情况下，模式设置为 `'validation'`，这会生成与模型验证模式对应的 JSON 模式。

[`JsonSchemaMode`][pydantic.json_schema.JsonSchemaMode] 是一个类型别名，表示 `mode` 参数的可用选项：

* `'validation'`
* `'serialization'`

以下是如何指定 `mode` 参数以及它如何影响生成的 JSON 模式的示例：

```python
from decimal import Decimal

from pydantic import BaseModel


class Model(BaseModel):
    a: Decimal = Decimal('12.34')


print(Model.model_json_schema(mode='validation'))
"""
{
    'properties': {
        'a': {
            'anyOf': [
                {'type': 'number'},
                {
                    'pattern': '^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$',
                    'type': 'string',
                },
            ],
            'default': '12.34',
            'title': 'A',
        }
    },
    'title': 'Model',
    'type': 'object',
}
"""

print(Model.model_json_schema(mode='serialization'))
"""
{
    'properties': {
        'a': {
            'default': '12.34',
            'pattern': '^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$',
            'title': 'A',
            'type': 'string',
        }
    },
    'title': 'Model',
    'type': 'object',
}
"""
```

## 自定义 JSON 模式 {#customizing-json-schema}

生成的 JSON 模式可以通过以下方式在字段级别和模型级别进行自定义：

1. [字段级别自定义](#field-level-customization) 使用 [`Field`][pydantic.fields.Field] 构造函数
2. [模型级别自定义](#model-level-customization) 使用 [`model_config`][pydantic.config.ConfigDict]

在字段和模型级别，您都可以使用 `json_schema_extra` 选项向 JSON 模式添加额外信息。
下面的 [使用 `json_schema_extra`](#using-json_schema_extra) 部分提供了有关此选项的更多详细信息。

对于自定义类型，Pydantic 提供了其他用于自定义 JSON 模式生成的工具：

1. [`WithJsonSchema` 注解](#withjsonschema-annotation)
2. [`SkipJsonSchema` 注解](#skipjsonschema-annotation)
3. [实现 `__get_pydantic_core_schema__`](#implementing_get_pydantic_core_schema)
4. [实现 `__get_pydantic_json_schema__`](#implementing_get_pydantic_json_schema)

### 字段级别自定义 {#field-level-customization}

可选地，可以使用 [`Field`][pydantic.fields.Field] 函数提供有关字段和验证的额外信息。

一些字段参数专门用于自定义生成的 JSON 模式：

* `title`: 字段的标题
* `description`: 字段的描述
* `examples`: 字段的示例
* `json_schema_extra`: 要添加到字段的额外 JSON 模式属性
* `field_title_generator`: 根据字段名称和信息以编程方式设置字段标题的函数

以下是一个示例：

```python {output="json"}
import json

from pydantic import BaseModel, EmailStr, Field, SecretStr


class User(BaseModel):
    age: int = Field(description='Age of the user')
    email: EmailStr = Field(examples=['marcelo@mail.com'])
    name: str = Field(title='Username')
    password: SecretStr = Field(
        json_schema_extra={
            'title': 'Password',
            'description': 'Password of the user',
            'examples': ['123456'],
        }
    )


print(json.dumps(User.model_json_schema(), indent=2))
"""
{
  "properties": {
    "age": {
      "description": "Age of the user",
      "title": "Age",
      "type": "integer"
    },
    "email": {
      "examples": [
        "marcelo@mail.com"
      ],
      "format": "email",
      "title": "Email",
      "type": "string"
    },
    "name": {
      "title": "Username",
      "type": "string"
    },
    "password": {
      "description": "Password of the user",
      "examples": [
        "123456"
      ],
      "format": "password",
      "title": "Password",
      "type": "string",
      "writeOnly": true
    }
  },
  "required": [
    "age",
    "email",
    "name",
    "password"
  ],
  "title": "User",
  "type": "object"
}
"""
```

#### 未强制执行的 `Field` 约束

如果 Pydantic 发现未强制执行的约束，将引发错误。如果您希望约束出现在模式中，即使解析时未检查，
可以使用带有原始模式属性名称的 [`Field`][pydantic.fields.Field] 的可变参数：

```python
from pydantic import BaseModel, Field, PositiveInt

try:
    # 这不会起作用，因为 `PositiveInt` 优先于 `Field` 中定义的约束，意味着它们被忽略
    class Model(BaseModel):
        foo: PositiveInt = Field(lt=10)

except ValueError as e:
    print(e)


# 如果您需要这样做，另一种方法是在 `Field` 中声明约束（或者可以使用 `conint()`）
# 这里两个约束都将被强制执行：
class ModelB(BaseModel):
    # 这里两个约束都将被应用，模式将正确生成
    foo: int = Field(gt=0, lt=10)


print(ModelB.model_json_schema())
"""
{
    'properties': {
        'foo': {
            'exclusiveMaximum': 10,
            'exclusiveMinimum': 0,
            'title': 'Foo',
            'type': 'integer',
        }
    },
    'required': ['foo'],
    'title': 'ModelB',
    'type': 'object',
}
"""
```

您也可以通过 [`typing.Annotated`][] 使用 [`Field`][pydantic.fields.Field] 构造函数指定 JSON 模式修改：

```python {output="json"}
import json
from typing import Annotated
from uuid import uuid4

from pydantic import BaseModel, Field


class Foo(BaseModel):
    id: Annotated[str, Field(default_factory=lambda: uuid4().hex)]
    name: Annotated[str, Field(max_length=256)] = Field(
        'Bar', title='CustomName'
    )


print(json.dumps(Foo.model_json_schema(), indent=2))
"""
{
  "properties": {
    "id": {
      "title": "Id",
      "type": "string"
    },
    "name": {
      "default": "Bar",
      "maxLength": 256,
      "title": "CustomName",
      "type": "string"
    }
  },
  "title": "Foo",
  "type": "object"
}
"""
```

### 编程式字段标题生成

`field_title_generator` 参数可用于根据字段名称和信息以编程方式生成字段标题。

请参阅以下示例：

```python
import json

from pydantic import BaseModel, Field
from pydantic.fields import FieldInfo


def make_title(field_name: str, field_info: FieldInfo) -> str:
    return field_name.upper()


class Person(BaseModel):
    name: str = Field(field_title_generator=make_title)
    age: int = Field(field_title_generator=make_title)


print(json.dumps(Person.model_json_schema(), indent=2))
"""
{
  "properties": {
    "name": {
      "title": "NAME",
      "type": "string"
    },
    "age": {
      "title": "AGE",
      "type": "integer"
    }
  },
  "required": [
    "name",
    "age"
  ],
  "title": "Person",
  "type": "object"
}
"""
```

### 模型级自定义 {#model-level-customization}

您还可以使用[模型配置][pydantic.config.ConfigDict]在模型级别自定义 JSON 模式生成。
具体来说，以下配置选项相关：

* [`title`][pydantic.config.ConfigDict.title]
* [`json_schema_extra`][pydantic.config.ConfigDict.json_schema_extra]
* [`json_schema_mode_override`][pydantic.config.ConfigDict.json_schema_mode_override]
* [`field_title_generator`][pydantic.config.ConfigDict.field_title_generator]
* [`model_title_generator`][pydantic.config.ConfigDict.model_title_generator]

### 使用 `json_schema_extra` {#using-json_schema_extra}

`json_schema_extra` 选项可用于向 JSON 模式添加额外信息，可以在
[字段级别](#field-level-customization) 或 [模型级别](#model-level-customization)。
您可以传递一个 `dict` 或 `Callable` 给 `json_schema_extra`。

#### 使用 `json_schema_extra` 与 `dict`

您可以传递一个 `dict` 给 `json_schema_extra` 来向 JSON 模式添加额外信息：

```python {output="json"}
import json

from pydantic import BaseModel, ConfigDict


class Model(BaseModel):
    a: str

    model_config = ConfigDict(json_schema_extra={'examples': [{'a': 'Foo'}]})


print(json.dumps(Model.model_json_schema(), indent=2))
"""
{
  "examples": [
    {
      "a": "Foo"
    }
  ],
  "properties": {
    "a": {
      "title": "A",
      "type": "string"
    }
  },
  "required": [
    "a"
  ],
  "title": "Model",
  "type": "object"
}
"""
```

#### 使用 `json_schema_extra` 与 `Callable`

您可以传递一个 `Callable` 给 `json_schema_extra`，通过函数修改 JSON 模式：

```python {output="json"}
import json

from pydantic import BaseModel, Field


def pop_default(s):
    s.pop('default')


class Model(BaseModel):
    a: int = Field(default=1, json_schema_extra=pop_default)


print(json.dumps(Model.model_json_schema(), indent=2))
"""
{
  "properties": {
    "a": {
      "title": "A",
      "type": "integer"
    }
  },
  "title": "Model",
  "type": "object"
}
"""
```

#### Merging `json_schema_extra`

自 v2.9 起，Pydantic 会合并来自注解类型的 `json_schema_extra` 字典。
这种模式提供了一种更增量的合并方法，而不是之前的覆盖行为。
这对于在多个类型中重用 JSON 模式额外信息的情况非常有帮助。

我们主要将此更改视为错误修复，因为它解决了 `BaseModel` 和 `TypeAdapter` 实例之间 `json_schema_extra` 合并行为的意外差异 - 有关更多详细信息，请参阅[此问题](https://github.com/pydantic/pydantic/issues/9210)。

```python
import json
from typing import Annotated

from typing_extensions import TypeAlias

from pydantic import Field, TypeAdapter

ExternalType: TypeAlias = Annotated[
    int, Field(json_schema_extra={'key1': 'value1'})
]

ta = TypeAdapter(
    Annotated[ExternalType, Field(json_schema_extra={'key2': 'value2'})]
)
print(json.dumps(ta.json_schema(), indent=2))
"""
{
  "key1": "value1",
  "key2": "value2",
  "type": "integer"
}
"""
```

!!! note
    我们不再（也从未完全）支持组合 `dict` 和 `callable` 类型的 `json_schema_extra` 规范。
    如果这对您的用例是必需的，请[打开一个 pydantic issue](https://github.com/pydantic/pydantic/issues/new/choose) 并解释您的情况 - 当我们看到有说服力的案例时，我们很乐意重新考虑这个决定。

### `WithJsonSchema` 注解 {#withjsonschema-annotation}

??? api "API 文档"
    [`pydantic.json_schema.WithJsonSchema`][pydantic.json_schema.WithJsonSchema]<br>

!!! tip
    对于自定义类型，使用 [`WithJsonSchema`][pydantic.json_schema.WithJsonSchema] 比
    [实现 `__get_pydantic_json_schema__`](#implementing_get_pydantic_json_schema) 更受推荐，
    因为它更简单且更不容易出错。

[`WithJsonSchema`][pydantic.json_schema.WithJsonSchema] 注解可用于覆盖给定类型的生成（基础）
JSON 模式，而无需在类型本身上实现 `__get_pydantic_core_schema__`
或 `__get_pydantic_json_schema__`。请注意，这会覆盖字段的整个 JSON 模式生成过程
（在以下示例中，还需要提供 `'type'`）。

```python {output="json"}
import json
from typing import Annotated

from pydantic import BaseModel, WithJsonSchema

MyInt = Annotated[
    int,
    WithJsonSchema({'type': 'integer', 'examples': [1, 0, -1]}),
]


class Model(BaseModel):
    a: MyInt


print(json.dumps(Model.model_json_schema(), indent=2))
"""
{
  "properties": {
    "a": {
      "examples": [
        1,
        0,
        -1
      ],
      "title": "A",
      "type": "integer"
    }
  },
  "required": [
    "a"
  ],
  "title": "Model",
  "type": "object"
}
"""
```

!!! note
    您可能会想使用 [`WithJsonSchema`][pydantic.json_schema.WithJsonSchema] 注解
    来微调带有[验证器](./validators.md)的字段的 JSON Schema。相反，
    建议使用 [`json_schema_input_type` 参数](./validators.md#json-schema-and-field-validators)。

### `SkipJsonSchema` 注解 {#skipjsonschema-annotation}

??? api "API 文档"
    [`pydantic.json_schema.SkipJsonSchema`][pydantic.json_schema.SkipJsonSchema]<br>

[`SkipJsonSchema`][pydantic.json_schema.SkipJsonSchema] 注解可用于跳过生成包含字段（或字段规范的一部分）的 JSON 模式。
有关更多详细信息，请参阅 API 文档。

### 实现 `__get_pydantic_core_schema__` 方法 {#implementing_get_pydantic_core_schema}

自定义类型（用作 `field_name: TheType` 或 `field_name: Annotated[TheType, ...]`）以及 `Annotated` 元数据
（用作 `field_name: Annotated[int, SomeMetadata]`）
可以通过实现 `__get_pydantic_core_schema__` 来修改或覆盖生成的模式。
此方法接收两个位置参数：

1. 与此类型对应的类型注解（例如，对于 `TheType[T][int]`，它将是 `TheType[int]`）。
2. 一个处理程序/回调函数，用于调用 `__get_pydantic_core_schema__` 的下一个实现者。

处理程序系统的工作方式类似于 [*wrap* 字段验证器](validators.md#field-wrap-validator)。
在这种情况下，输入是类型，输出是一个 `core_schema`。

以下是一个自定义类型的示例，它*覆盖*了生成的 `core_schema`：

```python
from dataclasses import dataclass
from typing import Any

from pydantic_core import core_schema

from pydantic import BaseModel, GetCoreSchemaHandler


@dataclass
class CompressedString:
    dictionary: dict[int, str]
    text: list[int]

    def build(self) -> str:
        return ' '.join([self.dictionary[key] for key in self.text])

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source: type[Any], handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        assert source is CompressedString
        return core_schema.no_info_after_validator_function(
            cls._validate,
            core_schema.str_schema(),
            serialization=core_schema.plain_serializer_function_ser_schema(
                cls._serialize,
                info_arg=False,
                return_schema=core_schema.str_schema(),
            ),
        )

    @staticmethod
    def _validate(value: str) -> 'CompressedString':
        inverse_dictionary: dict[str, int] = {}
        text: list[int] = []
        for word in value.split(' '):
            if word not in inverse_dictionary:
                inverse_dictionary[word] = len(inverse_dictionary)
            text.append(inverse_dictionary[word])
        return CompressedString(
            {v: k for k, v in inverse_dictionary.items()}, text
        )

    @staticmethod
    def _serialize(value: 'CompressedString') -> str:
        return value.build()


class MyModel(BaseModel):
    value: CompressedString


print(MyModel.model_json_schema())
"""
{
    'properties': {'value': {'title': 'Value', 'type': 'string'}},
    'required': ['value'],
    'title': 'MyModel',
    'type': 'object',
}
"""
print(MyModel(value='fox fox fox dog fox'))
"""
value = CompressedString(dictionary={0: 'fox', 1: 'dog'}, text=[0, 0, 0, 1, 0])
"""

print(MyModel(value='fox fox fox dog fox').model_dump(mode='json'))
#> {'value': 'fox fox fox dog fox'}
```

由于 Pydantic 不知道如何为 `CompressedString` 生成模式，如果您在其 `__get_pydantic_core_schema__` 方法中调用 `handler(source)`，您将得到一个 `pydantic.errors.PydanticSchemaGenerationError` 错误。
对于大多数自定义类型来说都是这种情况，因此您几乎从不希望为自定义类型调用 `handler`。

`Annotated` 元数据的过程大致相同，只是您通常可以调用 `handler` 让 Pydantic 处理模式生成。

```python
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Annotated, Any

from pydantic_core import core_schema

from pydantic import BaseModel, GetCoreSchemaHandler, ValidationError


@dataclass
class RestrictCharacters:
    alphabet: Sequence[str]

    def __get_pydantic_core_schema__(
        self, source: type[Any], handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        if not self.alphabet:
            raise ValueError('Alphabet may not be empty')
        schema = handler(
            source
        )  # get the CoreSchema from the type / inner constraints
        if schema['type'] != 'str':
            raise TypeError('RestrictCharacters can only be applied to strings')
        return core_schema.no_info_after_validator_function(
            self.validate,
            schema,
        )

    def validate(self, value: str) -> str:
        if any(c not in self.alphabet for c in value):
            raise ValueError(
                f'{value!r} is not restricted to {self.alphabet!r}'
            )
        return value


class MyModel(BaseModel):
    value: Annotated[str, RestrictCharacters('ABC')]


print(MyModel.model_json_schema())
"""
{
    'properties': {'value': {'title': 'Value', 'type': 'string'}},
    'required': ['value'],
    'title': 'MyModel',
    'type': 'object',
}
"""
print(MyModel(value='CBA'))
#> value='CBA'

try:
    MyModel(value='XYZ')
except ValidationError as e:
    print(e)
    """
    1 validation error for MyModel
    value
      Value error, 'XYZ' is not restricted to 'ABC' [type=value_error, input_value='XYZ', input_type=str]
    """
```

到目前为止，我们一直在包装模式，但如果您只想*修改*它或*忽略*它，也可以这样做。

要修改模式，首先调用处理程序，然后修改结果：

```python
from typing import Annotated, Any

from pydantic_core import ValidationError, core_schema

from pydantic import BaseModel, GetCoreSchemaHandler


class SmallString:
    def __get_pydantic_core_schema__(
        self,
        source: type[Any],
        handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        schema = handler(source)
        assert schema['type'] == 'str'
        schema['max_length'] = 10  # 原地修改
        return schema


class MyModel(BaseModel):
    value: Annotated[str, SmallString()]


try:
    MyModel(value='too long!!!!!')
except ValidationError as e:
    print(e)
    """
    1 validation error for MyModel
    value
      String should have at most 10 characters [type=string_too_long, input_value='too long!!!!!', input_type=str]
    """
```

!!! tip
    请注意，您*必须*返回一个模式，即使您只是原地修改它。

要完全覆盖模式，不要调用处理程序，而是返回您自己的 `CoreSchema`：

```python
from typing import Annotated, Any

from pydantic_core import ValidationError, core_schema

from pydantic import BaseModel, GetCoreSchemaHandler


class AllowAnySubclass:
    def __get_pydantic_core_schema__(
        self, source: type[Any], handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        # 我们不能调用处理程序，因为它会因任意类型而失败
        def validate(value: Any) -> Any:
            if not isinstance(value, source):
                raise ValueError(
                    f'Expected an instance of {source}, got an instance of {type(value)}'
                )

        return core_schema.no_info_plain_validator_function(validate)


class Foo:
    pass


class Model(BaseModel):
    f: Annotated[Foo, AllowAnySubclass()]


print(Model(f=Foo()))
#> f=None


class NotFoo:
    pass


try:
    Model(f=NotFoo())
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    f
      Value error, Expected an instance of <class '__main__.Foo'>, got an instance of <class '__main__.NotFoo'> [type=value_error, input_value=<__main__.NotFoo object at 0x0123456789ab>, input_type=NotFoo]
    """
```

### 实现 `__get_pydantic_json_schema__` 方法 {#implementing_get_pydantic_json_schema}

您还可以实现 `__get_pydantic_json_schema__` 来修改或覆盖生成的 JSON 模式。
修改此方法仅影响 JSON 模式 - 它不影响用于验证和序列化的核心模式。

以下是修改生成的 JSON 模式的示例：

```python {output="json"}
import json
from typing import Any

from pydantic_core import core_schema as cs

from pydantic import GetCoreSchemaHandler, GetJsonSchemaHandler, TypeAdapter
from pydantic.json_schema import JsonSchemaValue


class Person:
    name: str
    age: int

    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> cs.CoreSchema:
        return cs.typed_dict_schema(
            {
                'name': cs.typed_dict_field(cs.str_schema()),
                'age': cs.typed_dict_field(cs.int_schema()),
            },
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, core_schema: cs.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        json_schema = handler(core_schema)
        json_schema = handler.resolve_ref_schema(json_schema)
        json_schema['examples'] = [
            {
                'name': 'John Doe',
                'age': 25,
            }
        ]
        json_schema['title'] = 'Person'
        return json_schema


print(json.dumps(TypeAdapter(Person).json_schema(), indent=2))
"""
{
  "examples": [
    {
      "age": 25,
      "name": "John Doe"
    }
  ],
  "properties": {
    "name": {
      "title": "Name",
      "type": "string"
    },
    "age": {
      "title": "Age",
      "type": "integer"
    }
  },
  "required": [
    "name",
    "age"
  ],
  "title": "Person",
  "type": "object"
}
"""
```

### 使用 `field_title_generator`

`field_title_generator` 参数可用于根据字段名称和信息以编程方式生成字段标题。
这类似于字段级别的 `field_title_generator`，但 `ConfigDict` 选项将应用于类的所有字段。

请参阅以下示例：

```python
import json

from pydantic import BaseModel, ConfigDict


class Person(BaseModel):
    model_config = ConfigDict(
        field_title_generator=lambda field_name, field_info: field_name.upper()
    )
    name: str
    age: int


print(json.dumps(Person.model_json_schema(), indent=2))
"""
{
  "properties": {
    "name": {
      "title": "NAME",
      "type": "string"
    },
    "age": {
      "title": "AGE",
      "type": "integer"
    }
  },
  "required": [
    "name",
    "age"
  ],
  "title": "Person",
  "type": "object"
}
"""
```

### 使用 `model_title_generator`

`model_title_generator` 配置选项类似于 `field_title_generator` 选项，但它应用于模型本身的标题，
并接受模型类作为输入。

请参阅以下示例：

```python
import json

from pydantic import BaseModel, ConfigDict


def make_title(model: type) -> str:
    return f'Title-{model.__name__}'


class Person(BaseModel):
    model_config = ConfigDict(model_title_generator=make_title)
    name: str
    age: int


print(json.dumps(Person.model_json_schema(), indent=2))
"""
{
  "properties": {
    "name": {
      "title": "Name",
      "type": "string"
    },
    "age": {
      "title": "Age",
      "type": "integer"
    }
  },
  "required": [
    "name",
    "age"
  ],
  "title": "Title-Person",
  "type": "object"
}
"""
```

## JSON Schema 类型

类型、自定义字段类型和约束（如 `max_length`）按照以下优先级顺序映射到相应的规范格式（当有等效项可用时）：

1. [JSON Schema Core](https://json-schema.org/draft/2020-12/json-schema-core)
2. [JSON Schema Validation](https://json-schema.org/draft/2020-12/json-schema-validation)
3. [OpenAPI Data Types](https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.2.md#data-types)
4. 标准的 `format` JSON 字段用于为更复杂的 `string` 子类型定义 Pydantic 扩展。

### JSON Schema 类型映射优先级

生成 JSON 模式时，Pydantic 使用以下优先级顺序来确定类型映射：

1. 具有 `__get_pydantic_json_schema__` 方法的自定义类型
2. 具有 `WithJsonSchema` 注解的自定义类型
3. 内置类型和标准库类型
4. 泛型类型
5. 联合类型
6. 可选类型

这意味着如果您有一个实现 `__get_pydantic_json_schema__` 的自定义类型，它将优先于内置类型映射。

从 Python 或 Pydantic 到 JSON 模式的字段模式映射如下：

{{ schema_mappings_table }}

## 顶层模式生成

您还可以生成一个顶层 JSON 模式，该模式仅在其 `$defs` 中包含模型列表和相关子模型：

```python {output="json"}
import json

from pydantic import BaseModel
from pydantic.json_schema import models_json_schema


class Foo(BaseModel):
    a: str = None


class Model(BaseModel):
    b: Foo


class Bar(BaseModel):
    c: int


_, top_level_schema = models_json_schema(
    [(Model, 'validation'), (Bar, 'validation')], title='My Schema'
)
print(json.dumps(top_level_schema, indent=2))
"""
{
  "$defs": {
    "Bar": {
      "properties": {
        "c": {
          "title": "C",
          "type": "integer"
        }
      },
      "required": [
        "c"
      ],
      "title": "Bar",
      "type": "object"
    },
    "Foo": {
      "properties": {
        "a": {
          "default": null,
          "title": "A",
          "type": "string"
        }
      },
      "title": "Foo",
      "type": "object"
    },
    "Model": {
      "properties": {
        "b": {
          "$ref": "#/$defs/Foo"
        }
      },
      "required": [
        "b"
      ],
      "title": "Model",
      "type": "object"
    }
  },
  "title": "My Schema"
}
"""
```

## 自定义 JSON Schema 生成过程 {#customizing-the-json-schema-generation-process}

??? api "API 文档"
    [`pydantic.json_schema`][pydantic.json_schema.GenerateJsonSchema]<br>

如果您需要自定义模式生成，可以使用 `schema_generator`，根据需要修改
[`GenerateJsonSchema`][pydantic.json_schema.GenerateJsonSchema] 类以适应您的应用程序。

各种可用于生成 JSON 模式的方法都接受关键字参数 `schema_generator: type[GenerateJsonSchema] = GenerateJsonSchema`，您可以将自定义子类传递给这些方法，以使用您自己的 JSON 模式生成方法。

`GenerateJsonSchema` 实现了将类型的 `pydantic-core` 模式转换为 JSON 模式的功能。
通过设计，该类将 JSON 模式生成过程分解为更小的方法，这些方法可以在子类中轻松重写，以修改生成 JSON 模式的"全局"方法。

```python
from pydantic import BaseModel
from pydantic.json_schema import GenerateJsonSchema


class MyGenerateJsonSchema(GenerateJsonSchema):
    def generate(self, schema, mode='validation'):
        json_schema = super().generate(schema, mode=mode)
        json_schema['title'] = 'Customize title'
        json_schema['$schema'] = self.schema_dialect
        return json_schema


class MyModel(BaseModel):
    x: int


print(MyModel.model_json_schema(schema_generator=MyGenerateJsonSchema))
"""
{
    'properties': {'x': {'title': 'X', 'type': 'integer'}},
    'required': ['x'],
    'title': 'Customize title',
    'type': 'object',
    '$schema': 'https://json-schema.org/draft/2020-12/schema',
}
"""
```

Below is an approach you can use to exclude any fields from the schema that don't have valid json schemas:

```python
from typing import Callable

from pydantic_core import PydanticOmit, core_schema

from pydantic import BaseModel
from pydantic.json_schema import GenerateJsonSchema, JsonSchemaValue


class MyGenerateJsonSchema(GenerateJsonSchema):
    def handle_invalid_for_json_schema(
        self, schema: core_schema.CoreSchema, error_info: str
    ) -> JsonSchemaValue:
        raise PydanticOmit


def example_callable():
    return 1


class Example(BaseModel):
    name: str = 'example'
    function: Callable = example_callable


instance_example = Example()

validation_schema = instance_example.model_json_schema(
    schema_generator=MyGenerateJsonSchema, mode='validation'
)
print(validation_schema)
"""
{
    'properties': {
        'name': {'default': 'example', 'title': 'Name', 'type': 'string'}
    },
    'title': 'Example',
    'type': 'object',
}
"""
```

### JSON Schema 排序

默认情况下，Pydantic 通过按字母顺序排序键来递归排序 JSON 模式。值得注意的是，Pydantic 跳过对 `properties` 键值的排序，
以保留字段在模型中定义的顺序。

如果您想自定义此行为，可以在自定义的 `GenerateJsonSchema` 子类中重写 `sort` 方法。以下示例
使用无操作的 `sort` 方法完全禁用排序，这反映在模型字段和 `json_schema_extra` 键的保留顺序中：

```python
import json
from typing import Optional

from pydantic import BaseModel, Field
from pydantic.json_schema import GenerateJsonSchema, JsonSchemaValue


class MyGenerateJsonSchema(GenerateJsonSchema):
    def sort(
        self, value: JsonSchemaValue, parent_key: Optional[str] = None
    ) -> JsonSchemaValue:
        """No-op, we don't want to sort schema values at all."""
        return value


class Bar(BaseModel):
    c: str
    b: str
    a: str = Field(json_schema_extra={'c': 'hi', 'b': 'hello', 'a': 'world'})


json_schema = Bar.model_json_schema(schema_generator=MyGenerateJsonSchema)
print(json.dumps(json_schema, indent=2))
"""
{
  "type": "object",
  "properties": {
    "c": {
      "type": "string",
      "title": "C"
    },
    "b": {
      "type": "string",
      "title": "B"
    },
    "a": {
      "type": "string",
      "c": "hi",
      "b": "hello",
      "a": "world",
      "title": "A"
    }
  },
  "required": [
    "c",
    "b",
    "a"
  ],
  "title": "Bar"
}
"""
```

## 自定义 JSON Schema 中的 `$ref`

可以通过调用 [`model_json_schema()`][pydantic.main.BaseModel.model_json_schema]
或 [`model_dump_json()`][pydantic.main.BaseModel.model_dump_json] 并传入 `ref_template` 关键字参数来更改 `$ref` 的格式。
定义始终存储在键 `$defs` 下，但可以为引用使用指定的前缀。

如果您需要扩展或修改 JSON 模式默认定义位置，这很有用。例如，对于 OpenAPI：

```python {output="json"}
import json

from pydantic import BaseModel
from pydantic.type_adapter import TypeAdapter


class Foo(BaseModel):
    a: int


class Model(BaseModel):
    a: Foo


adapter = TypeAdapter(Model)

print(
    json.dumps(
        adapter.json_schema(ref_template='#/components/schemas/{model}'),
        indent=2,
    )
)
"""
{
  "$defs": {
    "Foo": {
      "properties": {
        "a": {
          "title": "A",
          "type": "integer"
        }
      },
      "required": [
        "a"
      ],
      "title": "Foo",
      "type": "object"
    }
  },
  "properties": {
    "a": {
      "$ref": "#/components/schemas/Foo"
    }
  },
  "required": [
    "a"
  ],
  "title": "Model",
  "type": "object"
}
"""
```

## JSON Schema 生成的杂项说明

* `Optional` 字段的 JSON 模式表明允许值 `null`。
* `Decimal` 类型在 JSON 模式中（以及序列化时）以字符串形式暴露。
* 由于 JSON 中不存在 `namedtuple` 类型，模型的 JSON 模式不会将 `namedtuple` 保留为 `namedtuple`。
* 使用的子模型按照规范添加到 `$defs` JSON 属性中并被引用。
* 具有修改（通过 `Field` 类）的子模型，如自定义标题、描述或默认值，
    会被递归包含而不是被引用。
* 模型的 `description` 取自类的文档字符串或 `Field` 类的 `description` 参数。
* 默认情况下，模式使用别名作为键生成，但可以通过调用 [`model_json_schema()`][pydantic.main.BaseModel.model_json_schema] 或
    [`model_dump_json()`][pydantic.main.BaseModel.model_dump_json] 并传入 `by_alias=False` 关键字参数，使用模型属性名称生成模式。