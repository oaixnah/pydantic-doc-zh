---
description: Pydantic 字段完整指南：学习如何使用 Field() 函数自定义模型字段，包括默认值设置、JSON Schema 元数据、字段约束、别名配置、严格验证、数据类字段、字段表示、鉴别器、不可变性、字段排除、弃用标记和计算字段等高级功能。掌握注解模式、字段验证和序列化的最佳实践，提升 Python 数据验证和类型安全的专业技能。
---

??? api "API 文档"
    [`pydantic.fields.Field`][pydantic.fields.Field]<br>

在本节中，我们将介绍可用于自定义 Pydantic 模型字段的机制：
[默认值](#default-values)、[JSON Schema 元数据](#customizing-json-schema)、
[约束](#field-constraints) 等。

为此，[`Field()`][pydantic.fields.Field] 函数被大量使用，其行为方式与
标准库的 [`field()`][dataclasses.field] 函数相同——通过分配给带注解的属性：

```python
from pydantic import BaseModel, Field


class Model(BaseModel):
    name: str = Field(frozen=True)
```

!!! note
    即使 `name` 被分配了一个值，它仍然是必需的且没有默认值。如果您想
    强调必须提供一个值，可以使用 [省略号][Ellipsis]：

    ```python {lint="skip" test="skip"}
    class Model(BaseModel):
        name: str = Field(..., frozen=True)
    ```

    但是，不鼓励使用这种方式，因为它与静态类型检查器配合不佳。

## 注解模式 {#the-annotated-pattern}

为了应用约束或将 [`Field()`][pydantic.fields.Field] 函数附加到模型字段，Pydantic
还支持使用 [`Annotated`][typing.Annotated] 类型构造来将元数据附加到注解：

```python
from typing import Annotated

from pydantic import BaseModel, Field, WithJsonSchema


class Model(BaseModel):
    name: Annotated[str, Field(strict=True), WithJsonSchema({'extra': 'data'})]
```

就静态类型检查器而言，`name` 仍然被类型化为 `str`，但 Pydantic 利用
可用的元数据来添加验证逻辑、类型约束等。

使用这种模式有一些优势：

* 使用 `f: <type> = Field(...)` 形式可能会令人困惑，并可能误导用户认为 `f`
  有默认值，而实际上它仍然是必需的。
* 您可以为字段提供任意数量的元数据元素。如上例所示，
  [`Field()`][pydantic.fields.Field] 函数仅支持有限的约束/元数据集，
  在某些情况下，您可能需要使用不同的 Pydantic 实用程序，例如 [`WithJsonSchema`][pydantic.WithJsonSchema]。
* 类型可以变得可重用（请参阅有关 [自定义类型](./types.md#using-the-annotated-pattern)
  使用此模式的文档）。

但是，请注意 [`Field()`][pydantic.fields.Field] 函数的某些参数（即 `default`、
`default_factory` 和 `alias`）会被静态类型检查器考虑以合成正确的
`__init__()` 方法。注解模式*不被*它们理解，因此您应该使用正常的
赋值形式。

!!! tip
    注解模式也可用于向类型的特定部分添加元数据。例如，
    [验证约束](#field-constraints) 可以通过这种方式添加：

    ```python
    from typing import Annotated

    from pydantic import BaseModel, Field


    class Model(BaseModel):
        int_list: list[Annotated[int, Field(gt=0)]]
        # 有效: [1, 3]
        # 无效: [-1, 2]
    ```

    注意不要混淆*字段*和*类型*元数据：

    ```python {test="skip" lint="skip"}
    class Model(BaseModel):
        field_bad: Annotated[int, Field(deprecated=True)] | None = None  # (1)!
        field_ok: Annotated[int | None, Field(deprecated=True)] = None  # (2)!
    ```

      1. [`Field()`][pydantic.fields.Field] 函数应用于 `int` 类型，因此
         `deprecated` 标志将不会产生任何效果。虽然这可能令人困惑，因为
         [`Field()`][pydantic.fields.Field] 函数的名称暗示它应该应用于字段，
         但该 API 是在此函数是提供元数据的唯一方式时设计的。您可以
         替代性地使用现在受 Pydantic 支持的 [`annotated_types`](https://github.com/annotated-types/annotated-types)
         库。

      2. [`Field()`][pydantic.fields.Field] 函数应用于"顶层"联合类型，
         因此 `deprecated` 标志将应用于字段。

## 默认值 {#default-values}

可以使用正常的赋值语法或通过向 `default` 参数提供值来为字段提供默认值：

```python
from pydantic import BaseModel, Field


class User(BaseModel):
    # 两个字段都不是必需的：
    name: str = 'John Doe'
    age: int = Field(default=20)
```

!!! warning
    [在 Pydantic V1 中](../migration.md#required-optional-and-nullable-fields)，被注解为 [`Any`][typing.Any]
    或被 [`Optional`][typing.Optional] 包装的类型即使没有明确指定默认值，也会被赋予隐式的 `None` 默认值。
    在 Pydantic V2 中不再是这样。

您还可以传递一个可调用对象给 `default_factory` 参数，该可调用对象将被调用来生成默认值：

```python
from uuid import uuid4

from pydantic import BaseModel, Field


class User(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
```

<!-- markdownlint-disable-next-line no-empty-links -->
[](){#default-factory-validated-data}

默认工厂也可以接受一个必需的参数，在这种情况下，已经验证的数据将作为字典传递。

```python
from pydantic import BaseModel, EmailStr, Field


class User(BaseModel):
    email: EmailStr
    username: str = Field(default_factory=lambda data: data['email'])


user = User(email='user@example.com')
print(user.username)
#> user@example.com
```

`data` 参数将*仅*包含已经验证的数据，基于 [模型字段的顺序](./models.md#field-ordering)
（如果 `username` 在 `email` 之前定义，上面的示例将失败）。

## 验证默认值 {#validate-default-values}

默认情况下，Pydantic *不会*验证默认值。可以使用 `validate_default` 字段参数
（或 [`validate_default`][pydantic.ConfigDict.validate_default] 配置值）来启用此行为：

```python
from pydantic import BaseModel, Field, ValidationError


class User(BaseModel):
    age: int = Field(default='twelve', validate_default=True)


try:
    user = User()
except ValidationError as e:
    print(e)
    """
    1 validation error for User
    age
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='twelve', input_type=str]
    """
```

### 可变默认值

Python 中一个常见的错误来源是使用可变对象作为函数或方法参数的默认值，
因为相同的实例最终会在每次调用中被重用。

[`dataclasses`][dataclasses] 模块实际上在这种情况下会引发错误，指示您应该使用
[默认工厂](https://docs.python.org/3/library/dataclasses.html#default-factory-functions) 替代。

虽然可以在 Pydantic 中做同样的事情，但这不是必需的。如果默认值不可哈希，
Pydantic 将在创建模型的每个实例时创建默认值的深拷贝：

```python
from pydantic import BaseModel


class Model(BaseModel):
    item_counts: list[dict[str, int]] = [{}]


m1 = Model()
m1.item_counts[0]['a'] = 1
print(m1.item_counts)
#> [{'a': 1}]


m2 = Model()
print(m2.item_counts)
#> [{}]
```

## 字段别名 {#field-aliases}

!!! tip
    在 [专用章节](./alias.md) 中阅读更多关于别名的信息。

对于验证和序列化，您可以为字段定义别名。

有三种定义别名的方式：

* `Field(alias='foo')`
* `Field(validation_alias='foo')`
* `Field(serialization_alias='foo')`

`alias` 参数用于验证*和*序列化。如果您想分别使用*不同*的别名进行验证和序列化，
可以使用 `validation_alias` 和 `serialization_alias` 参数，这些参数将仅在其各自的使用场景中应用。

以下是使用 `alias` 参数的示例：

```python
from pydantic import BaseModel, Field


class User(BaseModel):
    name: str = Field(alias='username')


user = User(username='johndoe')  # (1)!
print(user)
#> name='johndoe'
print(user.model_dump(by_alias=True))  # (2)!
#> {'username': 'johndoe'}
```

1. 别名 `'username'` 用于实例创建和验证。
2. 我们使用 [`model_dump()`][pydantic.main.BaseModel.model_dump] 将模型转换为可序列化的格式。

    请注意，`by_alias` 关键字参数默认为 `False`，必须明确指定才能使用字段（序列化）别名
    来转储模型。

    您还可以使用 [`ConfigDict.serialize_by_alias`][pydantic.config.ConfigDict.serialize_by_alias] 来
    在模型级别配置此行为。

    当 `by_alias=True` 时，别名 `'username'` 在序列化期间使用。

如果您想*仅*为验证使用别名，可以使用 `validation_alias` 参数：

```python
from pydantic import BaseModel, Field


class User(BaseModel):
    name: str = Field(validation_alias='username')


user = User(username='johndoe')  # (1)!
print(user)
#> name='johndoe'
print(user.model_dump(by_alias=True))  # (2)!
#> {'name': 'johndoe'}
```

1. 验证别名 `'username'` 在验证期间使用。
2. 字段名称 `'name'` 在序列化期间使用。

如果您只想为*序列化*定义别名，可以使用 `serialization_alias` 参数：

```python
from pydantic import BaseModel, Field


class User(BaseModel):
    name: str = Field(serialization_alias='username')


user = User(name='johndoe')  # (1)!
print(user)
#> name='johndoe'
print(user.model_dump(by_alias=True))  # (2)!
#> {'username': 'johndoe'}
```

1. 字段名称 `'name'` 用于验证。
2. 序列化别名 `'username'` 用于序列化。

!!! note "别名优先级"
    如果您同时使用 `alias` 和 `validation_alias` 或 `serialization_alias`，
    对于验证，`validation_alias` 将优先于 `alias`，对于序列化，`serialization_alias` 将优先于
    `alias`。

    如果您为 [`alias_generator`][pydantic.config.ConfigDict.alias_generator] 模型设置提供了值，
    您可以通过 `alias_priority` 字段参数控制字段别名和生成别名的优先级顺序。
    您可以在[这里](../concepts/alias.md#alias-precedence)阅读更多关于别名优先级的信息。

??? tip "静态类型检查/IDE 支持"
    如果您为 `alias` 字段参数提供了值，静态类型检查器将使用此别名而不是
    实际的字段名称来合成 `__init__` 方法：

    ```python
    from pydantic import BaseModel, Field


    class User(BaseModel):
        name: str = Field(alias='username')


    user = User(username='johndoe')  # (1)!
    ```

    1. 被类型检查器接受。

    这意味着当使用 [`validate_by_name`][pydantic.config.ConfigDict.validate_by_name] 模型设置（允许在模型验证期间使用字段名称和别名）时，
    类型检查器在使用实际字段名称时会报错：

    ```python
    from pydantic import BaseModel, ConfigDict, Field


    class User(BaseModel):
        model_config = ConfigDict(validate_by_name=True)

        name: str = Field(alias='username')


    user = User(name='johndoe')  # (1)!
    ```

    1. *不被*类型检查器接受。

    如果您仍然希望类型检查器使用字段名称而不是别名，可以使用 [注解模式](#the-annotated-pattern)
    （仅被 Pydantic 理解）：

    ```python
    from typing import Annotated

    from pydantic import BaseModel, ConfigDict, Field


    class User(BaseModel):
        model_config = ConfigDict(validate_by_name=True, validate_by_alias=True)

        name: Annotated[str, Field(alias='username')]


    user = User(name='johndoe')  # (1)!
    user = User(username='johndoe')  # (2)!
    ```

    1. 被类型检查器接受。
    2. *不被*类型检查器接受。

    <h3>验证别名</h3>

    尽管 Pydantic 在创建模型实例时将 `alias` 和 `validation_alias` 视为相同，但类型检查器
    仅理解 `alias` 字段参数。作为解决方法，您可以改为同时指定 `alias` 和
    `serialization_alias`（与字段名称相同），因为 `serialization_alias` 将在序列化期间覆盖 `alias`：

    ```python
    from pydantic import BaseModel, Field


    class MyModel(BaseModel):
        my_field: int = Field(validation_alias='myValidationAlias')
    ```

    替换为：

    ```python
    from pydantic import BaseModel, Field


    class MyModel(BaseModel):
        my_field: int = Field(
            alias='myValidationAlias',
            serialization_alias='my_field',
        )


    m = MyModel(myValidationAlias=1)
    print(m.model_dump(by_alias=True))
    #> {'my_field': 1}
    ```

<!-- old anchor added for backwards compatibility -->
<!-- markdownlint-disable-next-line no-empty-links -->
[](){#numeric-constraints}
<!-- markdownlint-disable-next-line no-empty-links -->
[](){#string-constraints}
<!-- markdownlint-disable-next-line no-empty-links -->
[](){#decimal-constraints}

## 字段约束 {#field-constraints}

[`Field()`][pydantic.Field] 函数也可用于向特定类型添加约束：

```python
from decimal import Decimal

from pydantic import BaseModel, Field


class Model(BaseModel):
    positive: int = Field(gt=0)
    short_str: str = Field(max_length=3)
    precise_decimal: Decimal = Field(max_digits=5, decimal_places=2)
```

每种类型可用的约束（以及它们影响 JSON Schema 的方式）在
[标准库类型](../api/standard_library_types.md) 文档中有描述。

<!-- old anchor added for backwards compatibility -->
<!-- markdownlint-disable-next-line no-empty-links -->
[](){#strict-mode}

## 严格字段

[`Field()`][pydantic.Field] 函数的 `strict` 参数指定字段是否应在
[严格模式](./strict_mode.md) 下进行验证。

```python
from pydantic import BaseModel, Field


class User(BaseModel):
    name: str = Field(strict=True)
    age: int = Field(strict=False)  # (1)!


user = User(name='John', age='42')  # (2)!
print(user)
#> name='John' age=42
```

1. 这是默认值。
2. `age` 字段在宽松模式下进行验证。因此，它可以被分配一个字符串。

[标准库类型](../api/standard_library_types.md) 文档描述了每种类型的严格行为。

<!-- old anchor added for backwards compatibility -->
<!-- markdownlint-disable-next-line no-empty-links -->
[](){#dataclass-constraints}

## 数据类字段

[`Field()`][pydantic.Field] 函数的一些参数可用于 [数据类](./dataclasses.md)：

* `init`：字段是否应包含在数据类的合成 `__init__()` 方法中。
* `init_var`：字段是否应为数据类中的 [仅初始化][dataclasses-init-only-variables] 字段。
* `kw_only`：字段是否应为数据类构造函数中的仅关键字参数。

以下是一个示例：

```python
from pydantic import BaseModel, Field
from pydantic.dataclasses import dataclass


@dataclass
class Foo:
    bar: str
    baz: str = Field(init_var=True)
    qux: str = Field(kw_only=True)


class Model(BaseModel):
    foo: Foo


model = Model(foo=Foo('bar', baz='baz', qux='qux'))
print(model.model_dump())  # (1)!
#> {'foo': {'bar': 'bar', 'qux': 'qux'}}
```

1. `baz` 字段不包含在序列化输出中，因为它是一个仅初始化字段。

## 字段表示

参数 `repr` 可用于控制字段是否应包含在模型的字符串表示中。

```python
from pydantic import BaseModel, Field


class User(BaseModel):
    name: str = Field(repr=True)  # (1)!
    age: int = Field(repr=False)


user = User(name='John', age=42)
print(user)
#> name='John'
```

1. 这是默认值。

## 鉴别器

参数 `discriminator` 可用于控制将用于区分联合中不同模型的字段。
它接受字段名称或 `Discriminator` 实例。当鉴别器字段对于 `Union` 中的所有模型
不完全相同时，`Discriminator` 方法可能很有用。

以下示例显示如何使用带有字段名称的 `discriminator`：

```python
from typing import Literal, Union

from pydantic import BaseModel, Field


class Cat(BaseModel):
    pet_type: Literal['cat']
    age: int


class Dog(BaseModel):
    pet_type: Literal['dog']
    age: int


class Model(BaseModel):
    pet: Union[Cat, Dog] = Field(discriminator='pet_type')


print(Model.model_validate({'pet': {'pet_type': 'cat', 'age': 12}}))  # (1)!
#> pet=Cat(pet_type='cat', age=12)
```

1. 在 [模型] 页面中查看更多关于 [验证数据] 的信息。

以下示例显示如何使用带有 `Discriminator` 实例的 `discriminator` 关键字参数：

```python
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Discriminator, Field, Tag


class Cat(BaseModel):
    pet_type: Literal['cat']
    age: int


class Dog(BaseModel):
    pet_kind: Literal['dog']
    age: int


def pet_discriminator(v):
    if isinstance(v, dict):
        return v.get('pet_type', v.get('pet_kind'))
    return getattr(v, 'pet_type', getattr(v, 'pet_kind', None))


class Model(BaseModel):
    pet: Union[Annotated[Cat, Tag('cat')], Annotated[Dog, Tag('dog')]] = Field(
        discriminator=Discriminator(pet_discriminator)
    )


print(repr(Model.model_validate({'pet': {'pet_type': 'cat', 'age': 12}})))
#> Model(pet=Cat(pet_type='cat', age=12))

print(repr(Model.model_validate({'pet': {'pet_kind': 'dog', 'age': 12}})))
#> Model(pet=Dog(pet_kind='dog', age=12))
```

您还可以利用 `Annotated` 来定义您的鉴别联合。
有关更多详细信息，请参阅 [鉴别联合] 文档。

## 不可变性

参数 `frozen` 用于模拟冻结数据类的行为。它用于防止在模型创建后为字段分配新值（不可变性）。

有关更多详细信息，请参阅 [冻结数据类文档]。

```python
from pydantic import BaseModel, Field, ValidationError


class User(BaseModel):
    name: str = Field(frozen=True)
    age: int


user = User(name='John', age=42)

try:
    user.name = 'Jane'  # (1)!
except ValidationError as e:
    print(e)
    """
    1 validation error for User
    name
      Field is frozen [type=frozen_field, input_value='Jane', input_type=str]
    """
```

1. 由于 `name` 字段被冻结，不允许赋值。

## 排除

`exclude` 参数可用于控制在导出模型时应从模型中排除哪些字段。

请参见以下示例：

```python
from pydantic import BaseModel, Field


class User(BaseModel):
    name: str
    age: int = Field(exclude=True)


user = User(name='John', age=42)
print(user.model_dump())  # (1)!
#> {'name': 'John'}
```

1. `age` 字段未包含在 `model_dump()` 输出中，因为它被排除了。

有关更多详细信息，请参阅 [序列化] 部分。

## 已弃用字段

`deprecated` 参数可用于将字段标记为已弃用。这样做将导致：

* 访问字段时发出运行时弃用警告。
* 在生成的 JSON Schema 中设置 [deprecated](https://json-schema.org/draft/2020-12/json-schema-validation#section-9.3) 关键字。

此参数接受不同的类型，如下所述。

### `deprecated` 作为字符串

该值将用作弃用消息。

```python
from typing import Annotated

from pydantic import BaseModel, Field


class Model(BaseModel):
    deprecated_field: Annotated[int, Field(deprecated='This is deprecated')]


print(Model.model_json_schema()['properties']['deprecated_field'])
#> {'deprecated': True, 'title': 'Deprecated Field', 'type': 'integer'}
```

### 通过 `@warnings.deprecated` 装饰器使用 `deprecated`

[`@warnings.deprecated`][warnings.deprecated] 装饰器（或在 Python 3.12 及更低版本上的
[`typing_extensions` 后备][typing_extensions.deprecated]）可用作实例。

<!-- TODO: tabs should be auto-generated if using Ruff (https://github.com/pydantic/pydantic/issues/10083) -->

=== "Python 3.9 及以上"

    ```python
    from typing import Annotated

    from typing_extensions import deprecated

    from pydantic import BaseModel, Field


    class Model(BaseModel):
        deprecated_field: Annotated[int, deprecated('This is deprecated')]

        # 或显式使用 `Field`：
        alt_form: Annotated[int, Field(deprecated=deprecated('This is deprecated'))]
    ```

=== "Python 3.13 及以上"

    ```python {requires="3.13"}
    from typing import Annotated
    from warnings import deprecated

    from pydantic import BaseModel, Field


    class Model(BaseModel):
        deprecated_field: Annotated[int, deprecated('This is deprecated')]

        # 或显式使用 `Field`：
        alt_form: Annotated[int, Field(deprecated=deprecated('This is deprecated'))]
    ```

!!! note "对 `category` 和 `stacklevel` 的支持"
    此功能的当前实现未考虑 `deprecated` 装饰器的 `category` 和 `stacklevel`
    参数。这可能会在未来的 Pydantic 版本中实现。

### `deprecated` 作为布尔值

```python
from typing import Annotated

from pydantic import BaseModel, Field


class Model(BaseModel):
    deprecated_field: Annotated[int, Field(deprecated=True)]


print(Model.model_json_schema()['properties']['deprecated_field'])
#> {'deprecated': True, 'title': 'Deprecated Field', 'type': 'integer'}
```

!!! warning "在验证器中访问已弃用字段"
    在验证器内部访问已弃用字段时，将发出弃用警告。您可以使用
    [`catch_warnings`][warnings.catch_warnings] 显式忽略它：

    ```python
    import warnings

    from typing_extensions import Self

    from pydantic import BaseModel, Field, model_validator


    class Model(BaseModel):
        deprecated_field: int = Field(deprecated='This is deprecated')

        @model_validator(mode='after')
        def validate_model(self) -> Self:
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', DeprecationWarning)
                self.deprecated_field = self.deprecated_field * 2
    ```

## 自定义 JSON Schema {#customizing-json-schema}

一些字段参数专门用于自定义生成的 JSON Schema。这些参数包括：

* `title`
* `description`
* `examples`
* `json_schema_extra`

有关使用字段自定义/修改 JSON Schema 的更多信息，请参阅 JSON Schema 文档中的 [自定义 JSON Schema] 部分。

## `computed_field` 装饰器

??? api "API 文档"
    [`computed_field`][pydantic.fields.computed_field]<br>

[`computed_field`][pydantic.fields.computed_field] 装饰器可用于在序列化模型或数据类时包含 [`property`][] 或
[`cached_property`][functools.cached_property] 属性。
该属性也将在 JSON Schema（序列化模式）中被考虑。

!!! note
    属性对于从其他字段计算的字段，或者计算成本高昂的字段（因此，如果使用 [`cached_property`][functools.cached_property] 则会被缓存）非常有用。

    但是，请注意 Pydantic 将*不会*对包装的属性执行任何额外的逻辑
    （验证、缓存失效等）。

以下是为带有计算字段的模型生成的 JSON Schema（序列化模式）示例：

```python
from pydantic import BaseModel, computed_field


class Box(BaseModel):
    width: float
    height: float
    depth: float

    @computed_field
    @property  # (1)!
    def volume(self) -> float:
        return self.width * self.height * self.depth


print(Box.model_json_schema(mode='serialization'))
"""
{
    'properties': {
        'width': {'title': 'Width', 'type': 'number'},
        'height': {'title': 'Height', 'type': 'number'},
        'depth': {'title': 'Depth', 'type': 'number'},
        'volume': {'readOnly': True, 'title': 'Volume', 'type': 'number'},
    },
    'required': ['width', 'height', 'depth', 'volume'],
    'title': 'Box',
    'type': 'object',
}
"""
```

1. 如果未指定，[`computed_field`][pydantic.fields.computed_field] 将隐式将方法
   转换为 [`property`][]。但是，为了类型检查目的，最好显式使用 [`@property`][property] 装饰器。

以下是一个使用 `model_dump` 方法和计算字段的示例：

```python
from pydantic import BaseModel, computed_field


class Box(BaseModel):
    width: float
    height: float
    depth: float

    @computed_field
    @property
    def volume(self) -> float:
        return self.width * self.height * self.depth


b = Box(width=1, height=2, depth=3)
print(b.model_dump())
#> {'width': 1.0, 'height': 2.0, 'depth': 3.0, 'volume': 6.0}
```

与常规字段一样，计算字段可以标记为已弃用：

```python
from typing_extensions import deprecated

from pydantic import BaseModel, computed_field


class Box(BaseModel):
    width: float
    height: float
    depth: float

    @computed_field
    @property
    @deprecated("'volume' is deprecated")
    def volume(self) -> float:
        return self.width * self.height * self.depth
```

[Discriminated Unions]: ../concepts/unions.md#discriminated-unions
[Validating data]: models.md#validating-data
[Models]: models.md
[frozen dataclass documentation]: https://docs.python.org/3/library/dataclasses.html#frozen-instances
[Customizing JSON Schema]: json_schema.md#field-level-customization