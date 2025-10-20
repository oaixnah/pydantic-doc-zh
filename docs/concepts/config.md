---
description: Pydantic 配置指南：全面了解如何使用 ConfigDict 控制 Pydantic 行为。详细介绍了在 Pydantic 模型、数据类、TypeAdapter 和其他支持类型上设置配置的方法，包括 model_config 类属性、类参数、配置继承和配置传播规则。掌握 Pydantic 配置技巧，提升数据验证和类型检查的灵活性。
---

Pydantic 的行为可以通过多种配置值来控制，这些配置值记录在 [`ConfigDict`][pydantic.ConfigDict] 类中。本页描述了如何为 Pydantic 支持的类型指定配置。

## Pydantic 模型上的配置

在 Pydantic 模型上，可以通过两种方式指定配置：

* 使用 [`model_config`][pydantic.BaseModel.model_config] 类属性：

    ```python
    from pydantic import BaseModel, ConfigDict, ValidationError


    class Model(BaseModel):
        model_config = ConfigDict(str_max_length=5)  # (1)!

        v: str


    try:
        m = Model(v='abcdef')
    except ValidationError as e:
        print(e)
        """
        1 validation error for Model
        v
          String should have at most 5 characters [type=string_too_long, input_value='abcdef', input_type=str]
        """
    ```

    1. 也可以使用普通字典（即 `{'str_max_length': 5}`）。

    !!! note
        在 Pydantic V1 中，使用了 `Config` 类。这仍然受支持，但**已弃用**。

* 使用类参数：

    ```python
    from pydantic import BaseModel


    class Model(BaseModel, frozen=True):
        a: str
    ```

  与 [`model_config`][pydantic.BaseModel.model_config] 类属性不同，
  静态类型检查器将识别类参数。对于 `frozen`，任何实例
  突变都将被标记为类型检查错误。

## Pydantic 数据类上的配置

[Pydantic 数据类](./dataclasses.md) 也支持配置（更多信息请参阅
[专用章节](./dataclasses.md#dataclass-config)）。

```python
from pydantic import ConfigDict, ValidationError
from pydantic.dataclasses import dataclass


@dataclass(config=ConfigDict(str_max_length=10, validate_assignment=True))
class User:
    name: str


user = User(name='John Doe')
try:
    user.name = 'x' * 20
except ValidationError as e:
    print(e)
    """
    1 validation error for User
    name
      String should have at most 10 characters [type=string_too_long, input_value='xxxxxxxxxxxxxxxxxxxx', input_type=str]
    """
```

## `TypeAdapter` 上的配置

[类型适配器](./type_adapter.md)（使用 [`TypeAdapter`][pydantic.TypeAdapter] 类）支持配置，
通过提供 `config` 参数。

```python
from pydantic import ConfigDict, TypeAdapter

ta = TypeAdapter(list[str], config=ConfigDict(coerce_numbers_to_str=True))

print(ta.validate_python([1, 2]))
#> ['1', '2']
```

如果类型适配器直接包装支持配置的类型，则无法提供配置，并且在这种情况下会引发
[使用错误](../errors/usage_errors.md)。
[配置传播](#configuration-propagation) 规则也适用。

## 其他支持类型上的配置 {#configuration-on-other-supported-types}

如果您使用 [标准库数据类][dataclasses] 或 [`TypedDict`][typing.TypedDict] 类，
可以通过两种方式设置配置：

* 使用 `__pydantic_config__` 类属性：

    ```python
    from dataclasses import dataclass

    from pydantic import ConfigDict


    @dataclass
    class User:
        __pydantic_config__ = ConfigDict(strict=True)

        id: int
        name: str = 'John Doe'
    ```

* 使用 [`@with_config`][pydantic.config.with_config] 装饰器（这可以避免与
  [`TypedDict`][typing.TypedDict] 相关的静态类型检查错误）：

    ```python
    from typing_extensions import TypedDict

    from pydantic import ConfigDict, with_config


    @with_config(ConfigDict(str_to_lower=True))
    class Model(TypedDict):
        x: str
    ```

## `@validate_call` 装饰器上的配置

[`@validate_call`](./validation_decorator.md) 装饰器也支持设置自定义配置。更多详细信息请参阅
[专用章节](./validation_decorator.md#custom-configuration)。

## 全局更改行为

如果您希望全局更改 Pydantic 的行为，可以创建自己的自定义父类
并设置自定义配置，因为配置是可继承的：

```python
from pydantic import BaseModel, ConfigDict


class Parent(BaseModel):
    model_config = ConfigDict(extra='allow')


class Model(Parent):
    x: str


m = Model(x='foo', y='bar')
print(m.model_dump())
#> {'x': 'foo', 'y': 'bar'}
```

如果您为子类提供配置，它将与父配置*合并*：

```python
from pydantic import BaseModel, ConfigDict


class Parent(BaseModel):
    model_config = ConfigDict(extra='allow', str_to_lower=False)


class Model(Parent):
    model_config = ConfigDict(str_to_lower=True)

    x: str


m = Model(x='FOO', y='bar')
print(m.model_dump())
#> {'x': 'foo', 'y': 'bar'}
print(Model.model_config)
#> {'extra': 'allow', 'str_to_lower': True}
```

!!! warning
    如果您的模型继承自多个基类，Pydantic 目前*不*遵循
    [MRO]。更多详细信息，请参阅[此问题](https://github.com/pydantic/pydantic/issues/9992)。

    [MRO]: https://docs.python.org/3/glossary.html#term-method-resolution-order

## 配置传播 {#configuration-propagation}

当使用支持配置的类型作为字段注解时，配置可能不会被传播：

* 对于 Pydantic 模型和数据类，配置将*不会*被传播，每个模型都有自己的
  "配置边界"：

    ```python
    from pydantic import BaseModel, ConfigDict


    class User(BaseModel):
        name: str


    class Parent(BaseModel):
        user: User

        model_config = ConfigDict(str_to_lower=True)


    print(Parent(user={'name': 'JOHN'}))
    #> user=User(name='JOHN')
    ```

* 对于标准库类型（数据类和类型化字典），配置将被传播，除非
  该类型有自己的配置设置：

    ```python
    from dataclasses import dataclass

    from pydantic import BaseModel, ConfigDict, with_config


    @dataclass
    class UserWithoutConfig:
        name: str


    @dataclass
    @with_config(str_to_lower=False)
    class UserWithConfig:
        name: str


    class Parent(BaseModel):
        user_1: UserWithoutConfig
        user_2: UserWithConfig

        model_config = ConfigDict(str_to_lower=True)


    print(Parent(user_1={'name': 'JOHN'}, user_2={'name': 'JOHN'}))
    #> user_1=UserWithoutConfig(name='john') user_2=UserWithConfig(name='JOHN')
    ```