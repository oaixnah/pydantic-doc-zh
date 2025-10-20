---
description: Pydantic 别名功能详解：字段别名、验证别名、序列化别名的使用方法，包括 AliasPath、AliasChoices 和别名生成器，支持数据序列化和反序列化的灵活字段映射。
---

别名是字段的替代名称，在序列化和反序列化数据时使用。

您可以通过以下方式指定别名：

* 在 [`Field`][pydantic.fields.Field] 上使用 `alias`
    * 必须是一个 `str`
* 在 [`Field`][pydantic.fields.Field] 上使用 `validation_alias`
    * 可以是 `str`、[`AliasPath`][pydantic.aliases.AliasPath] 或 [`AliasChoices`][pydantic.aliases.AliasChoices] 的实例
* 在 [`Field`][pydantic.fields.Field] 上使用 `serialization_alias`
    * 必须是一个 `str`
* 在 [`Config`][pydantic.config.ConfigDict.alias_generator] 上使用 `alias_generator`
    * 可以是一个可调用对象或 [`AliasGenerator`][pydantic.aliases.AliasGenerator] 的实例

有关如何使用 `alias`、`validation_alias` 和 `serialization_alias` 的示例，请参阅 [字段别名](../concepts/fields.md#field-aliases)。

## `AliasPath` 和 `AliasChoices` {#aliaspath-and-aliaschoices}

??? api "API 文档"

    [`pydantic.aliases.AliasPath`][pydantic.aliases.AliasPath]<br>
    [`pydantic.aliases.AliasChoices`][pydantic.aliases.AliasChoices]<br>

Pydantic 提供了两种特殊类型，方便在使用 `validation_alias` 时使用：`AliasPath` 和 `AliasChoices`。

`AliasPath` 用于使用别名指定字段的路径。例如：

```python {lint="skip"}
from pydantic import BaseModel, Field, AliasPath


class User(BaseModel):
    first_name: str = Field(validation_alias=AliasPath('names', 0))
    last_name: str = Field(validation_alias=AliasPath('names', 1))

user = User.model_validate({'names': ['John', 'Doe']})  # (1)!
print(user)
#> first_name='John' last_name='Doe'
```

1. 我们使用 `model_validate` 来使用字段别名验证字典。

    您可以在 API 参考中查看更多关于 [`model_validate`][pydantic.main.BaseModel.model_validate] 的详细信息。

在 `'first_name'` 字段中，我们使用别名 `'names'` 和索引 `0` 来指定名字的路径。
在 `'last_name'` 字段中，我们使用别名 `'names'` 和索引 `1` 来指定姓氏的路径。

`AliasChoices` 用于指定别名的选择。例如：

```python {lint="skip"}
from pydantic import BaseModel, Field, AliasChoices


class User(BaseModel):
    first_name: str = Field(validation_alias=AliasChoices('first_name', 'fname'))
    last_name: str = Field(validation_alias=AliasChoices('last_name', 'lname'))

user = User.model_validate({'fname': 'John', 'lname': 'Doe'})  # (1)!
print(user)
#> first_name='John' last_name='Doe'
user = User.model_validate({'first_name': 'John', 'lname': 'Doe'})  # (2)!
print(user)
#> first_name='John' last_name='Doe'
```

1. 我们为两个字段都使用了第二个别名选择。
2. 我们为字段 `'first_name'` 使用了第一个别名选择，为字段 `'last_name'` 使用了第二个别名选择。

您也可以将 `AliasChoices` 与 `AliasPath` 一起使用：

```python {lint="skip"}
from pydantic import BaseModel, Field, AliasPath, AliasChoices


class User(BaseModel):
    first_name: str = Field(validation_alias=AliasChoices('first_name', AliasPath('names', 0)))
    last_name: str = Field(validation_alias=AliasChoices('last_name', AliasPath('names', 1)))


user = User.model_validate({'first_name': 'John', 'last_name': 'Doe'})
print(user)
#> first_name='John' last_name='Doe'
user = User.model_validate({'names': ['John', 'Doe']})
print(user)
#> first_name='John' last_name='Doe'
user = User.model_validate({'names': ['John'], 'last_name': 'Doe'})
print(user)
#> first_name='John' last_name='Doe'
```

## 使用别名生成器 {#using-alias-generators}

您可以使用 [`Config`][pydantic.config.ConfigDict.alias_generator] 的 `alias_generator` 参数来指定一个可调用对象（或通过 `AliasGenerator` 指定一组可调用对象），该对象将为模型中的所有字段生成别名。
如果您想为模型中的所有字段使用一致的命名约定，但不想为每个字段单独指定别名，这将非常有用。

!!! note
    Pydantic 提供了三个内置的别名生成器，您可以开箱即用：

    [`to_pascal`][pydantic.alias_generators.to_pascal]<br>
    [`to_camel`][pydantic.alias_generators.to_camel]<br>
    [`to_snake`][pydantic.alias_generators.to_snake]<br>

### 使用可调用对象

这是一个使用可调用对象的基本示例：

```python
from pydantic import BaseModel, ConfigDict


class Tree(BaseModel):
    model_config = ConfigDict(
        alias_generator=lambda field_name: field_name.upper()
    )

    age: int
    height: float
    kind: str


t = Tree.model_validate({'AGE': 12, 'HEIGHT': 1.2, 'KIND': 'oak'})
print(t.model_dump(by_alias=True))
#> {'AGE': 12, 'HEIGHT': 1.2, 'KIND': 'oak'}
```

### 使用 `AliasGenerator`

??? api "API 文档"

    [`pydantic.aliases.AliasGenerator`][pydantic.aliases.AliasGenerator]<br>

`AliasGenerator` 是一个类，允许您为模型指定多个别名生成器。
您可以使用 `AliasGenerator` 为验证和序列化指定不同的别名生成器。

如果您需要为加载和保存数据使用不同的命名约定，但不想为每个字段单独指定验证和序列化别名，这将特别有用。

例如：

```python
from pydantic import AliasGenerator, BaseModel, ConfigDict


class Tree(BaseModel):
    model_config = ConfigDict(
        alias_generator=AliasGenerator(
            validation_alias=lambda field_name: field_name.upper(),
            serialization_alias=lambda field_name: field_name.title(),
        )
    )

    age: int
    height: float
    kind: str


t = Tree.model_validate({'AGE': 12, 'HEIGHT': 1.2, 'KIND': 'oak'})
print(t.model_dump(by_alias=True))
#> {'Age': 12, 'Height': 1.2, 'Kind': 'oak'}
```

## 别名优先级 {#alias-precedence}

如果您在 [`Field`][pydantic.fields.Field] 上指定了 `alias`，默认情况下它将优先于生成的别名：

```python
from pydantic import BaseModel, ConfigDict, Field


def to_camel(string: str) -> str:
    return ''.join(word.capitalize() for word in string.split('_'))


class Voice(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel)

    name: str
    language_code: str = Field(alias='lang')


voice = Voice(Name='Filiz', lang='tr-TR')
print(voice.language_code)
#> tr-TR
print(voice.model_dump(by_alias=True))
#> {'Name': 'Filiz', 'lang': 'tr-TR'}
```

### 别名优先级

您可以在字段上设置 `alias_priority` 来改变此行为：

* `alias_priority=2` 别名将*不会*被别名生成器覆盖。
* `alias_priority=1` 别名*将*被别名生成器覆盖。
* 未设置 `alias_priority`：
    * 如果设置了别名：别名将*不会*被别名生成器覆盖。
    * 如果未设置别名：别名*将*被别名生成器覆盖。

相同的优先级规则适用于 `validation_alias` 和 `serialization_alias`。
有关不同字段别名的更多信息，请参阅 [字段别名](../concepts/fields.md#field-aliases)。

## 别名配置

您可以使用 [`ConfigDict`](./config.md) 设置或运行时验证/序列化设置来控制是否使用别名。

### `ConfigDict` 设置 {#configdict-settings}

您可以使用 [配置设置](./config.md) 在模型级别控制是否使用别名进行验证和序列化。如果您想为嵌套模型/跨越配置模型边界控制此行为，请使用 [运行时设置](#runtime-settings)。

#### 验证

在验证数据时，您可以按属性名称、别名或两者启用属性填充。
**默认情况下**，Pydantic 使用别名进行验证。可通过以下方式进一步配置：

* [`ConfigDict.validate_by_alias`][pydantic.config.ConfigDict.validate_by_alias]：默认为 `True`
* [`ConfigDict.validate_by_name`][pydantic.config.ConfigDict.validate_by_name]：默认为 `False`

=== "`validate_by_alias`"

    ```python
    from pydantic import BaseModel, ConfigDict, Field


    class Model(BaseModel):
        my_field: str = Field(validation_alias='my_alias')

        model_config = ConfigDict(validate_by_alias=True, validate_by_name=False)


    print(repr(Model(my_alias='foo')))  # (1)!
    #> Model(my_field='foo')
    ```

    1. 使用别名 `my_alias` 进行验证。

=== "`validate_by_name`"

    ```python
    from pydantic import BaseModel, ConfigDict, Field


    class Model(BaseModel):
        my_field: str = Field(validation_alias='my_alias')

        model_config = ConfigDict(validate_by_alias=False, validate_by_name=True)


    print(repr(Model(my_field='foo')))  # (1)!
    #> Model(my_field='foo')
    ```

    1. 使用属性标识符 `my_field` 进行验证。

=== "`validate_by_alias` 和 `validate_by_name`"

    ```python
    from pydantic import BaseModel, ConfigDict, Field


    class Model(BaseModel):
        my_field: str = Field(validation_alias='my_alias')

        model_config = ConfigDict(validate_by_alias=True, validate_by_name=True)


    print(repr(Model(my_alias='foo')))  # (1)!
    #> Model(my_field='foo')

    print(repr(Model(my_field='foo')))  # (2)!
    #> Model(my_field='foo')
    ```

    1. 使用别名 `my_alias` 进行验证。
    2. 使用属性标识符 `my_field` 进行验证。

!!! warning
    您不能同时将 `validate_by_alias` 和 `validate_by_name` 设置为 `False`。
    在这种情况下会引发 [用户错误](../errors/usage_errors.md#validate-by-alias-and-name-false)。

#### 序列化

在序列化数据时，您可以启用按别名序列化，默认情况下是禁用的。
有关更多详细信息，请参阅 [`ConfigDict.serialize_by_alias`][pydantic.config.ConfigDict.serialize_by_alias] API 文档。

```python
from pydantic import BaseModel, ConfigDict, Field


class Model(BaseModel):
    my_field: str = Field(serialization_alias='my_alias')

    model_config = ConfigDict(serialize_by_alias=True)


m = Model(my_field='foo')
print(m.model_dump())  # (1)!
#> {'my_alias': 'foo'}
```

1. 使用别名 `my_alias` 进行序列化。

!!! note
    按别名序列化默认禁用的事实与验证的默认设置（默认使用别名）明显不一致。我们预计在 V3 中更改此默认设置。

### 运行时设置 {#runtime-settings}

您可以使用运行时别名标志来控制每次调用时别名的使用，用于验证和序列化。
如果您想在模型级别控制此行为，请使用 [`ConfigDict` 设置](#configdict-settings)。

#### 验证

在验证数据时，您可以按属性名称、别名或两者启用属性填充。

`by_alias` 和 `by_name` 标志可在 [`model_validate()`][pydantic.main.BaseModel.model_validate]、
[`model_validate_json()`][pydantic.main.BaseModel.model_validate_json] 和 [`model_validate_strings()`][pydantic.main.BaseModel.model_validate_strings] 方法以及 [`TypeAdapter`][pydantic.type_adapter.TypeAdapter] 验证方法上使用。

默认情况下：

* `by_alias` 为 `True`
* `by_name` 为 `False`

=== "`by_alias`"

    ```python
    from pydantic import BaseModel, Field


    class Model(BaseModel):
        my_field: str = Field(validation_alias='my_alias')


    m = Model.model_validate(
        {'my_alias': 'foo'},  # (1)!
        by_alias=True,
        by_name=False,
    )
    print(repr(m))
    #> Model(my_field='foo')
    ```

    1. 使用别名 `my_alias` 进行验证。

=== "`by_name`"

    ```python
    from pydantic import BaseModel, Field


    class Model(BaseModel):
        my_field: str = Field(validation_alias='my_alias')


    m = Model.model_validate(
        {'my_field': 'foo'}, by_alias=False, by_name=True  # (1)!
    )
    print(repr(m))
    #> Model(my_field='foo')
    ```

    1. 使用属性名称 `my_field` 进行验证。

=== "`validate_by_alias` 和 `validate_by_name`"

    ```python
    from pydantic import BaseModel, Field


    class Model(BaseModel):
        my_field: str = Field(validation_alias='my_alias')


    m = Model.model_validate(
        {'my_alias': 'foo'}, by_alias=True, by_name=True  # (1)!
    )
    print(repr(m))
    #> Model(my_field='foo')

    m = Model.model_validate(
        {'my_field': 'foo'}, by_alias=True, by_name=True  # (2)!
    )
    print(repr(m))
    #> Model(my_field='foo')
    ```

    1. 使用别名 `my_alias` 进行验证。
    2. 使用属性名称 `my_field` 进行验证。

!!! warning
    您不能同时将 `by_alias` 和 `by_name` 设置为 `False`。
    在这种情况下会引发 [用户错误](../errors/usage_errors.md#validate-by-alias-and-name-false)。

#### 序列化

在序列化数据时，您可以通过 `by_alias` 标志启用按别名序列化，
该标志可在 [`model_dump()`][pydantic.main.BaseModel.model_dump] 和
[`model_dump_json()`][pydantic.main.BaseModel.model_dump_json] 方法以及
[`TypeAdapter`][pydantic.type_adapter.TypeAdapter] 方法上使用。

默认情况下，`by_alias` 为 `False`。

```py
from pydantic import BaseModel, Field


class Model(BaseModel):
    my_field: str = Field(serialization_alias='my_alias')


m = Model(my_field='foo')
print(m.model_dump(by_alias=True))  # (1)!
#> {'my_alias': 'foo'}
```

1. 使用别名 `my_alias` 进行序列化。

!!! note
    按别名序列化默认禁用的事实与验证的默认设置（默认使用别名）明显不一致。我们预计在 V3 中更改此默认设置。