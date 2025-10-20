---
description: Pydantic 数据类提供了在标准 Python dataclasses 上添加强大数据验证功能的解决方案。本文档详细介绍了如何使用 @pydantic.dataclasses.dataclass 装饰器，包括数据类配置选项、验证器应用、与 BaseModel 的异同点，以及如何处理嵌套类和泛型。内容涵盖从基础用法到高级特性，如字段验证、自定义类型处理、继承标准库数据类、在 BaseModel 中使用数据类等。还提供了丰富的代码示例，帮助开发者快速掌握 Pydantic 数据类的完整功能，实现高效的数据验证和管理。
---

??? api "API 文档"
    [`@pydantic.dataclasses.dataclass`][pydantic.dataclasses.dataclass]<br>

如果您不想使用 Pydantic 的 [`BaseModel`][pydantic.BaseModel]，您可以在标准 [dataclasses][dataclasses] 上获得相同的数据验证。

```python
from datetime import datetime
from typing import Optional

from pydantic.dataclasses import dataclass


@dataclass
class User:
    id: int
    name: str = 'John Doe'
    signup_ts: Optional[datetime] = None


user = User(id='42', signup_ts='2032-06-21T12:00')
print(user)
"""
User(id=42, name='John Doe', signup_ts=datetime.datetime(2032, 6, 21, 12, 0))
"""
```

!!! note
    请记住，Pydantic 数据类**不是** [Pydantic 模型](../concepts/models.md) 的替代品。
    它们提供了与标准库数据类类似的功能，但增加了 Pydantic 验证。

    在某些情况下，使用 Pydantic 模型进行子类化是更好的选择。

    更多信息和讨论请参见
    [pydantic/pydantic#710](https://github.com/pydantic/pydantic/issues/710)。

Pydantic 数据类和模型之间的相似性包括对以下内容的支持：

* [配置](#dataclass-config) 支持
* [嵌套](./models.md#nested-models) 类
* [泛型](./models.md#generic-models)

Pydantic 数据类和模型之间的一些差异包括：

* [验证器](#validators-and-initialization-hooks)
* 与 [`extra`][pydantic.ConfigDict.extra] 配置值的行为

与 Pydantic 模型类似，用于实例化数据类的参数会被[复制](./models.md#attribute-copies)。

要使用[各种方法](./models.md#model-methods-and-properties)来验证、转储和生成 JSON 模式，
您可以使用 [`TypeAdapter`][pydantic.type_adapter.TypeAdapter] 包装数据类并利用其方法。

您可以使用 Pydantic 的 [`Field()`][pydantic.Field] 和标准库的 [`field()`][dataclasses.field] 函数：

```python
import dataclasses
from typing import Optional

from pydantic import Field
from pydantic.dataclasses import dataclass


@dataclass
class User:
    id: int
    name: str = 'John Doe'
    friends: list[int] = dataclasses.field(default_factory=lambda: [0])
    age: Optional[int] = dataclasses.field(
        default=None,
        metadata={'title': 'The age of the user', 'description': 'do not lie!'},
    )
    height: Optional[int] = Field(
        default=None, title='The height in cm', ge=50, le=300
    )


user = User(id='42', height='250')
print(user)
#> User(id=42, name='John Doe', friends=[0], age=None, height=250)
```

Pydantic [`@dataclass`][pydantic.dataclasses.dataclass] 装饰器接受与标准装饰器相同的参数，
但额外增加了一个 `config` 参数。

## 数据类配置 {#dataclass-config}

如果您想像使用 [`BaseModel`][pydantic.BaseModel] 一样修改配置，您有两个选项：

* 使用装饰器的 `config` 参数。
* 使用 `__pydantic_config__` 属性定义配置。

```python
from pydantic import ConfigDict
from pydantic.dataclasses import dataclass


# 选项 1 -- 使用装饰器参数：
@dataclass(config=ConfigDict(validate_assignment=True))  # (1)!
class MyDataclass1:
    a: int


# 选项 2 -- 使用属性：
@dataclass
class MyDataclass2:
    a: int

    __pydantic_config__ = ConfigDict(validate_assignment=True)
```

1. 您可以在 [API 参考][pydantic.config.ConfigDict.validate_assignment] 中阅读更多关于 `validate_assignment` 的信息。

!!! note
    虽然 Pydantic 数据类支持 [`extra`][pydantic.config.ConfigDict.extra] 配置值，但标准库数据类的某些默认
    行为可能会占主导地位。例如，在 Pydantic 数据类上存在的任何额外字段（当 [`extra`][pydantic.config.ConfigDict.extra]
    设置为 `'allow'` 时）在数据类的字符串表示中会被省略。
    也没有办法[使用 `__pydantic_extra__` 属性](./models.md#extra-data)提供验证。

## 重建数据类模式

[`rebuild_dataclass()`][pydantic.dataclasses.rebuild_dataclass] 函数可用于重建数据类的核心模式。
有关更多详细信息，请参阅[重建模型模式](./models.md#rebuilding-model-schema)部分。

## 标准库数据类和 Pydantic 数据类

### 从标准库数据类继承

标准库数据类（嵌套或不嵌套）也可以被继承，Pydantic 将自动验证所有继承的字段。

```python
import dataclasses

import pydantic


@dataclasses.dataclass
class Z:
    z: int


@dataclasses.dataclass
class Y(Z):
    y: int = 0


@pydantic.dataclasses.dataclass
class X(Y):
    x: int = 0


foo = X(x=b'1', y='2', z='3')
print(foo)
#> X(z=3, y=2, x=1)

try:
    X(z='pika')
except pydantic.ValidationError as e:
    print(e)
    """
    1 validation error for X
    z
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='pika', input_type=str]
    """
```

装饰器也可以直接应用于标准库数据类，在这种情况下将创建一个新的子类：

```python
import dataclasses

import pydantic


@dataclasses.dataclass
class A:
    a: int


PydanticA = pydantic.dataclasses.dataclass(A)
print(PydanticA(a='1'))
#> A(a=1)
```

### 在 `BaseModel` 中使用标准库数据类

当标准库数据类在 Pydantic 模型、Pydantic 数据类或 [`TypeAdapter`][pydantic.TypeAdapter] 中使用时，
将应用验证（并且[配置](#dataclass-config)保持不变）。这意味着使用标准库或 Pydantic 数据类作为字段注释在功能上是等效的。

```python
import dataclasses
from typing import Optional

from pydantic import BaseModel, ConfigDict, ValidationError


@dataclasses.dataclass(frozen=True)
class User:
    name: str


class Foo(BaseModel):
    # 必需，以便 pydantic 重新验证模型属性：
    model_config = ConfigDict(revalidate_instances='always')

    user: Optional[User] = None


# 如预期的那样，没有进行验证：
user = User(name=['not', 'a', 'string'])
print(user)
#> User(name=['not', 'a', 'string'])


try:
    Foo(user=user)
except ValidationError as e:
    print(e)
    """
    1 validation error for Foo
    user.name
      Input should be a valid string [type=string_type, input_value=['not', 'a', 'string'], input_type=list]
    """

foo = Foo(user=User(name='pika'))
try:
    foo.user.name = 'bulbi'
except dataclasses.FrozenInstanceError as e:
    print(e)
    #> cannot assign to field 'name'
```

### 使用自定义类型

如上所述，验证应用于标准库数据类。如果您使用自定义类型，在尝试引用数据类时会出错。要规避
此问题，您可以在数据类上设置 [`arbitrary_types_allowed`][pydantic.ConfigDict.arbitrary_types_allowed]
配置值：

```python
import dataclasses

from pydantic import BaseModel, ConfigDict
from pydantic.errors import PydanticSchemaGenerationError


class ArbitraryType:
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f'ArbitraryType(value={self.value!r})'


@dataclasses.dataclass
class DC:
    a: ArbitraryType
    b: str


# 有效，因为它是没有验证的标准库数据类：
my_dc = DC(a=ArbitraryType(value=3), b='qwe')

try:

    class Model(BaseModel):
        dc: DC
        other: str

    # 无效，因为 dc 现在使用 pydantic 进行验证，而 ArbitraryType 不是已知类型
    Model(dc=my_dc, other='other')

except PydanticSchemaGenerationError as e:
    print(e.message)
    """
    Unable to generate pydantic-core schema for <class '__main__.ArbitraryType'>. Set `arbitrary_types_allowed=True` in the model_config to ignore this error or implement `__get_pydantic_core_schema__` on your type to fully support it.

    If you got this error by calling handler(<some type>) within `__get_pydantic_core_schema__` then you likely need to call `handler.generate_schema(<some type>)` since we do not call `__get_pydantic_core_schema__` on `<some type>` otherwise to avoid infinite recursion.
    """


# 有效，因为我们设置了 arbitrary_types_allowed=True，并且该配置会传递到嵌套的普通数据类
class Model(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    dc: DC
    other: str


m = Model(dc=my_dc, other='other')
print(repr(m))
#> Model(dc=DC(a=ArbitraryType(value=3), b='qwe'), other='other')
```

### 检查数据类是否为 Pydantic 数据类

Pydantic 数据类仍然被认为是数据类，因此使用 [`dataclasses.is_dataclass()`][dataclasses.is_dataclass]
将返回 `True`。要检查类型是否特定为 Pydantic 数据类，您可以使用
[`is_pydantic_dataclass()`][pydantic.dataclasses.is_pydantic_dataclass] 函数。

```python
import dataclasses

import pydantic


@dataclasses.dataclass
class StdLibDataclass:
    id: int


PydanticDataclass = pydantic.dataclasses.dataclass(StdLibDataclass)

print(dataclasses.is_dataclass(StdLibDataclass))
#> True
print(pydantic.dataclasses.is_pydantic_dataclass(StdLibDataclass))
#> False

print(dataclasses.is_dataclass(PydanticDataclass))
#> True
print(pydantic.dataclasses.is_pydantic_dataclass(PydanticDataclass))
#> True
```

## 验证器和初始化钩子 {#validators-and-initialization-hooks}

验证器也适用于 Pydantic 数据类：

```python
from pydantic import field_validator
from pydantic.dataclasses import dataclass


@dataclass
class DemoDataclass:
    product_id: str  # 应该是一个五位数字符串，可能有前导零

    @field_validator('product_id', mode='before')
    @classmethod
    def convert_int_serial(cls, v):
        if isinstance(v, int):
            v = str(v).zfill(5)
        return v


print(DemoDataclass(product_id='01234'))
#> DemoDataclass(product_id='01234')
print(DemoDataclass(product_id=2468))
#> DemoDataclass(product_id='02468')
```

<!-- markdownlint-disable-next-line strong-style -->
数据类的 [`__post_init__()`][dataclasses.__post_init__] 方法也受支持，并且将在
*before* 和 *after* 模型验证器调用之间被调用。

??? example

    ```python
    from pydantic_core import ArgsKwargs
    from typing_extensions import Self

    from pydantic import model_validator
    from pydantic.dataclasses import dataclass


    @dataclass
    class Birth:
        year: int
        month: int
        day: int


    @dataclass
    class User:
        birth: Birth

        @model_validator(mode='before')
        @classmethod
        def before(cls, values: ArgsKwargs) -> ArgsKwargs:
            print(f'First: {values}')  # (1)!
            """
            First: ArgsKwargs((), {'birth': {'year': 1995, 'month': 3, 'day': 2}})
            """
            return values

        @model_validator(mode='after')
        def after(self) -> Self:
            print(f'Third: {self}')
            #> Third: User(birth=Birth(year=1995, month=3, day=2))
            return self

        def __post_init__(self):
            print(f'Second: {self.birth}')
            #> Second: Birth(year=1995, month=3, day=2)


    user = User(**{'birth': {'year': 1995, 'month': 3, 'day': 2}})
    ```

    1. 与 Pydantic 模型不同，`values` 参数的类型是 [`ArgsKwargs`][pydantic_core.ArgsKwargs]