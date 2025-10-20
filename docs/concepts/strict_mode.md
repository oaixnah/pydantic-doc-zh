---
description: Pydantic 严格模式允许开发者控制数据验证行为，禁用自动类型转换，确保数据类型严格匹配。本文档详细介绍如何在验证参数、字段级别和配置级别启用严格模式，包括使用 Strict() 元数据类和 Field(strict=True) 方法，以及严格模式与宽松模式的验证差异对比。
---

??? api "API 文档"
    [`pydantic.types.Strict`][pydantic.types.Strict]<br>

默认情况下，Pydantic 会尝试在可能时将值强制转换为所需的类型。
例如，您可以将字符串 `'123'` 作为 [`int` 数字类型](../api/standard_library_types.md#integers) 的输入，
它将被转换为值 `123`。
这种强制转换行为在许多场景中很有用——想想：UUID、URL 参数、HTTP 头、环境变量、
日期等。

然而，在某些情况下这是不可取的，您希望 Pydantic 报错而不是强制转换数据。

为了更好地支持这种用例，Pydantic 提供了"严格模式"。当启用严格模式时，Pydantic 在强制转换数据时会
更加严格，如果数据不是正确的类型，则会报错。

大多数情况下，严格模式只允许提供类型的实例，尽管对 JSON 输入可能适用更宽松的规则
（例如，[日期和时间类型](../api/standard_library_types.md#date-and-time-types) 即使在严格模式下也允许字符串）。

每种类型的严格行为可以在 [标准库类型](../api/standard_library_types.md) 文档中找到，
并在 [转换表](./conversion_table.md) 中进行了总结。

以下是一个简要示例，展示了严格模式和默认宽松模式下的验证行为差异：

```python
from pydantic import BaseModel, ValidationError


class MyModel(BaseModel):
    x: int


print(MyModel.model_validate({'x': '123'}))  # 宽松模式
#> x=123

try:
    MyModel.model_validate({'x': '123'}, strict=True)  # 严格模式
except ValidationError as exc:
    print(exc)
    """
    1 validation error for MyModel
    x
      Input should be a valid integer [type=int_type, input_value='123', input_type=str]
    """
```

严格模式可以通过多种方式启用：

* [作为验证参数](#as-a-validation-parameter)，例如在使用 Pydantic 模型上的 [`model_validate()`][pydantic.BaseModel.model_validate] 时。
* [在字段级别](#at-the-field-level)。
* [在配置级别](#as-a-configuration-value)（可以在字段级别覆盖）。

<!-- old anchor added for backwards compatibility -->
<!-- markdownlint-disable-next-line no-empty-links -->
[](){#strict-mode-in-method-calls}

## 作为验证参数 {#as-a-validation-parameter}

严格模式可以在每次验证调用时启用，当使用 [Pydantic 模型](./models.md) 和 [类型适配器](./type_adapter.md) 上的 [验证方法](./models.md#validating-data) 时。

```python
from datetime import date

from pydantic import TypeAdapter, ValidationError

print(TypeAdapter(date).validate_python('2000-01-01'))  # 正常：宽松模式
#> 2000-01-01

try:
    # 不正常：严格模式：
    TypeAdapter(date).validate_python('2000-01-01', strict=True)
except ValidationError as exc:
    print(exc)
    """
    1 validation error for date
      Input should be a valid date [type=date_type, input_value='2000-01-01', input_type=str]
    """

TypeAdapter(date).validate_json('"2000-01-01"', strict=True)  # (1)!
#> 2000-01-01
```

1. 如前所述，从 JSON 验证时严格模式更宽松。

<!-- old anchor added for backwards compatibility -->
<!-- markdownlint-disable-next-line no-empty-links -->
[](){#strict-mode-with-field}

## 在字段级别 {#at-the-field-level}

严格模式可以在特定字段上启用，通过将 [`Field()`][pydantic.Field] 函数的 `strict` 参数设置为 `True`。
严格模式将应用于这些字段，即使 [验证方法](./models.md#validating-data) 在宽松模式下调用。

```python
from pydantic import BaseModel, Field, ValidationError


class User(BaseModel):
    name: str
    age: int = Field(strict=True)  # (1)!


user = User(name='John', age=42)
print(user)
#> name='John' age=42


try:
    another_user = User(name='John', age='42')
except ValidationError as e:
    print(e)
    """
    1 validation error for User
    age
      Input should be a valid integer [type=int_type, input_value='42', input_type=str]
    """
```

1. 严格约束也可以使用 [注解模式](./fields.md#the-annotated-pattern) 应用：
   `Annotated[int, Field(strict=True)]`

<!-- old anchor added for backwards compatibility -->
<!-- markdownlint-disable-next-line no-empty-links -->
[](){#strict-mode-with-annotated-strict}

### 使用 `Strict()` 元数据类 {#using-the-strict-metadata-class}

??? api "API 文档"
    [`pydantic.types.Strict`][pydantic.types.Strict]<br>

作为 [`Field()`][pydantic.Field] 函数的替代方案，Pydantic 提供了 [`Strict`][pydantic.types.Strict]
元数据类，旨在与 [注解模式](./fields.md#the-annotated-pattern) 一起使用。它还提供了
最常见类型的便捷别名（即 [`StrictBool`][pydantic.types.StrictBool]、
[`StrictInt`][pydantic.types.StrictInt]、[`StrictFloat`][pydantic.types.StrictFloat]、[`StrictStr`][pydantic.types.StrictStr]
和 [`StrictBytes`][pydantic.types.StrictBytes]）。

```python
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Strict, StrictInt


class User(BaseModel):
    id: Annotated[UUID, Strict()]
    age: StrictInt  # (1)!
```

1. 等同于 `Annotated[int, Strict()]`。

<!-- old anchor added for backwards compatibility -->
<!-- markdownlint-disable-next-line no-empty-links -->
[](){#strict-mode-with-configdict}

## 作为配置值 {#as-a-configuration-value}

严格模式行为可以在 [配置](./config.md) 级别控制。当在 Pydantic 模型（或类似模型的类，如 [数据类](./dataclasses.md)）上使用时，
严格性仍然可以在 [字段级别](#at-the-field-level) 被覆盖：

```python
from pydantic import BaseModel, ConfigDict, Field


class User(BaseModel):
    model_config = ConfigDict(strict=True)

    name: str
    age: int = Field(strict=False)


print(User(name='John', age='18'))
#> name='John' age=18
```