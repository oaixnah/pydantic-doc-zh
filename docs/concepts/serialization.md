---
description: Pydantic 序列化文档全面介绍了如何将模型数据转换为字典或 JSON 格式，包括 Python 模式和 JSON 模式的序列化方法、自定义字段和模型序列化器、序列化上下文使用、子类序列化策略以及字段包含和排除的高级技巧。
---

除了通过字段名直接访问模型属性（例如 `model.foobar`）之外，模型可以通过多种方式进行转换、转储、序列化和导出。序列化可以针对整个模型进行自定义，也可以基于每个字段或每种类型进行定制。

??? abstract "序列化与转储"
    Pydantic 使用术语"序列化"和"转储"可以互换使用。两者都指将模型转换为字典或JSON编码字符串的过程。

    在 Pydantic 之外，单词"序列化"通常指将内存中的数据转换为字符串或字节。然而，在 Pydantic 的上下文中，将对象从更结构化的形式（如 Pydantic 模型、数据类等）转换为由 Python 内置类型（如 dict）组成的较不结构化形式之间存在非常密切的关系。

    虽然我们可以（并且有时确实）通过使用单词"转储"来区分这些场景（当转换为基本类型时）和使用"序列化"（当转换为字符串时），但出于实际目的，我们经常使用单词"序列化"来指代这两种情况，即使它并不总是意味着转换为字符串或字节。

!!! tip
    想要快速跳转到相关的序列化器部分？

    <div class="grid cards" markdown>

    *   字段序列化器

        ---

        * [字段 *plain* 序列化器](#field-plain-serializer)
        * [字段 *wrap* 序列化器](#field-wrap-serializer)

    *   模型序列化器

        ---

        * [模型 *plain* 序列化器](#model-plain-serializer)
        * [模型 *wrap* 序列化器](#model-wrap-serializer)

    </div>

## 序列化数据 {#serializing-data}

Pydantic 允许模型（以及使用[类型适配器](./type_adapter.md)的任何其他类型）以*两种*模式进行序列化：[Python模式](#python-mode)和[JSON模式](#json-mode)。Python输出可能包含不可JSON序列化的数据（尽管这可以模拟）。

<!-- old anchor added for backwards compatibility -->
<!-- markdownlint-disable-next-line no-empty-links -->
[](){#modelmodel_dump}

### Python 模式 {#python-mode}

当使用 Python 模式时，Pydantic 模型（以及类似模型的类型，如 [dataclasses][]）（1）将被（递归地）转换为字典。这可以通过使用[`model_dump()`][pydantic.BaseModel.model_dump]方法实现：
{ .annotate }

1. 除了[根模型](./models.md#rootmodel-and-custom-root-types)，其中根值直接转储。

```python {group="python-dump"}
from typing import Optional

from pydantic import BaseModel, Field


class BarModel(BaseModel):
    whatever: tuple[int, ...]


class FooBarModel(BaseModel):
    banana: Optional[float] = 1.1
    foo: str = Field(serialization_alias='foo_alias')
    bar: BarModel


m = FooBarModel(banana=3.14, foo='hello', bar={'whatever': (1, 2)})

# returns a dictionary:
print(m.model_dump())
#> {'banana': 3.14, 'foo': 'hello', 'bar': {'whatever': (1, 2)}}

print(m.model_dump(by_alias=True))
#> {'banana': 3.14, 'foo_alias': 'hello', 'bar': {'whatever': (1, 2)}}
```

请注意，`whatever` 的值被转储为元组，这不是已知的 JSON 类型。可以将 `mode` 参数设置为 `'json'` 以确保使用JSON兼容的类型：

```python {group="python-dump"}
print(m.model_dump(mode='json'))
#> {'banana': 3.14, 'foo': 'hello', 'bar': {'whatever': [1, 2]}}
```

!!! info "另请参阅"
    当*不*处理 Pydantic 模型时，[`TypeAdapter.dump_python()`][pydantic.TypeAdapter.dump_python]方法很有用。

<!-- old anchor added for backwards compatibility -->
<!-- markdownlint-disable-next-line no-empty-links -->
[](){#modelmodel_dump_json}

### JSON 模式 {#json-mode}

Pydantic 允许数据直接序列化为 JSON 编码的字符串，通过尽力将 Python 值转换为有效的 JSON 数据。这可以通过使用 [`model_dump_json()`][pydantic.BaseModel.model_dump_json] 方法实现：

```python
from datetime import datetime

from pydantic import BaseModel


class BarModel(BaseModel):
    whatever: tuple[int, ...]


class FooBarModel(BaseModel):
    foo: datetime
    bar: BarModel


m = FooBarModel(foo=datetime(2032, 6, 1, 12, 13, 14), bar={'whatever': (1, 2)})

print(m.model_dump_json(indent=2))
"""
{
  "foo": "2032-06-01T12:13:14",
  "bar": {
    "whatever": [
      1,
      2
    ]
  }
}
"""
```

除了标准库 [`json`][] 模块支持的[类型][json.JSONEncoder]之外，Pydantic还支持多种类型（[日期和时间类型][datetime]、[`UUID`][uuid.UUID] 对象、[集合][set]等）。如果使用了不支持的类型且无法序列化为 JSON，则会引发 [`PydanticSerializationError`][pydantic_core.PydanticSerializationError] 异常。

!!! info "另请参阅"
    当*不*处理 Pydantic 模型时，[`TypeAdapter.dump_json()`][pydantic.TypeAdapter.dump_json] 方法很有用。

<!-- old anchor added for backwards compatibility -->
<!-- markdownlint-disable-next-line no-empty-links -->
[](){#dictmodel-and-iteration}

## 迭代模型

Pydantic 模型也可以被迭代，产生 `(字段名, 字段值)` 对。请注意，字段值保持原样，因此子模型*不会*被转换为字典：

```python {group="iterating-model"}
from pydantic import BaseModel


class BarModel(BaseModel):
    whatever: int


class FooBarModel(BaseModel):
    banana: float
    foo: str
    bar: BarModel


m = FooBarModel(banana=3.14, foo='hello', bar={'whatever': 123})

for name, value in m:
    print(f'{name}: {value}')
    #> banana: 3.14
    #> foo: hello
    #> bar: whatever=123
```

这意味着在模型上调用 [`dict()`][dict] 可以用于构造模型的字典：

```python {group="iterating-model"}
print(dict(m))
#> {'banana': 3.14, 'foo': 'hello', 'bar': BarModel(whatever=123)}
```

!!! note
    [根模型](models.md#rootmodel-and-custom-root-types)*确实*会被转换为带有键 `'root'` 的字典。

<!-- old anchor added for backwards compatibility -->
<!-- markdownlint-disable-next-line no-empty-links -->
[](){#pickledumpsmodel}

## Pickling 支持

Pydantic 模型支持高效的 pickling 和 unpickling 。

<!-- TODO need to get pickling doctest to work -->
```python {test="skip"}
import pickle

from pydantic import BaseModel


class FooBarModel(BaseModel):
    a: str
    b: int


m = FooBarModel(a='hello', b=123)
print(m)
#> a='hello' b=123
data = pickle.dumps(m)
print(data[:20])
#> b'\x80\x04\x95\x95\x00\x00\x00\x00\x00\x00\x00\x8c\x08__main_'
m2 = pickle.loads(data)
print(m2)
#> a='hello' b=123
```

<!-- old anchor added for backwards compatibility -->
<!-- markdownlint-disable-next-line no-empty-links -->
[](){#custom-serializers}

## 序列化器 {#serializers}

类似于[自定义验证器](./validators.md)，您可以在字段和模型级别利用自定义序列化器来进一步控制序列化行为。

!!! warning
    每个字段/模型只能定义*一个*序列化器。不可能将多个序列化器组合在一起（包括 *plain* 和 *wrap* 序列化器）。

### 字段序列化器 {#field-serializers}

??? api "API 文档"
    [`pydantic.functional_serializers.PlainSerializer`][pydantic.functional_serializers.PlainSerializer]<br>
    [`pydantic.functional_serializers.WrapSerializer`][pydantic.functional_serializers.WrapSerializer]<br>
    [`pydantic.functional_serializers.field_serializer`][pydantic.functional_serializers.field_serializer]<br>

在最简单的形式中，字段序列化器是一个可调用对象，将要序列化的值作为参数并**返回序列化后的值**。

如果向序列化器提供了 `return_type` 参数（或者序列化器函数上有可用的返回类型注解），它将用于构建额外的序列化器，以确保序列化的字段值符合此返回类型。

可以使用**两种**不同类型的序列化器。它们都可以使用[注解模式](./fields.md#the-annotated-pattern)或使用 [`@field_serializer`][pydantic.field_serializer] 装饰器来定义，应用于实例或[静态方法][staticmethod]。

* ***Plain* 序列化器**：无条件调用以序列化字段。Pydantic支持的类型的序列化逻辑将*不会*被调用。使用此类序列化器对于指定任意类型的逻辑也很有用。
  {#field-plain-serializer}

    === "注解模式"

        ```python
        from typing import Annotated, Any

        from pydantic import BaseModel, PlainSerializer


        def ser_number(value: Any) -> Any:
            if isinstance(value, int):
                return value * 2
            else:
                return value


        class Model(BaseModel):
            number: Annotated[int, PlainSerializer(ser_number)]


        print(Model(number=4).model_dump())
        #> {'number': 8}
        m = Model(number=1)
        m.number = 'invalid'
        print(m.model_dump())  # (1)!
        #> {'number': 'invalid'}
        ```

        1. Pydantic 将*不会*验证序列化后的值是否符合 `int` 类型。

    === "装饰器"

        ```python
        from typing import Any

        from pydantic import BaseModel, field_serializer


        class Model(BaseModel):
            number: int

            @field_serializer('number', mode='plain')  # (1)!
            def ser_number(self, value: Any) -> Any:
                if isinstance(value, int):
                    return value * 2
                else:
                    return value


        print(Model(number=4).model_dump())
        #> {'number': 8}
        m = Model(number=1)
        m.number = 'invalid'
        print(m.model_dump())  # (2)!
        #> {'number': 'invalid'}
        ```

        1. `'plain'` 是装饰器的默认模式，可以省略。
        2. Pydantic 将*不会*验证序列化后的值是否符合 `int` 类型。

* ***Wrap* 序列化器**：提供更大的灵活性来自定义序列化行为。您可以在 Pydantic 序列化逻辑之前或之后运行代码。
  {#field-wrap-serializer}

    此类序列化器必须定义**强制性的**额外*handler*参数：一个可调用对象，将要序列化的值作为参数。在内部，此*handler*将把值的序列化委托给 Pydantic。您可以完全*不*调用 *handler*。

    === "注解模式"

        ```python
        from typing import Annotated, Any

        from pydantic import BaseModel, SerializerFunctionWrapHandler, WrapSerializer


        def ser_number(value: Any, handler: SerializerFunctionWrapHandler) -> int:
            return handler(value) + 1


        class Model(BaseModel):
            number: Annotated[int, WrapSerializer(ser_number)]


        print(Model(number=4).model_dump())
        #> {'number': 5}
        ```

    === "装饰器"

        ```python
        from typing import Any

        from pydantic import BaseModel, SerializerFunctionWrapHandler, field_serializer


        class Model(BaseModel):
            number: int

            @field_serializer('number', mode='wrap')
            def ser_number(
                self, value: Any, handler: SerializerFunctionWrapHandler
            ) -> int:
                return handler(value) + 1


        print(Model(number=4).model_dump())
        #> {'number': 5}
        ```

<!-- 注意：保持此部分与[验证器部分](./validators.md#which-validator-pattern-to-use)同步更新 -->

#### 使用哪种序列化器模式

虽然两种方法可以实现相同的事情，但每种模式都提供不同的好处。

##### 使用注解模式

使用[注解模式](./fields.md#the-annotated-pattern)的主要好处之一是使序列化器可重用：

```python
from typing import Annotated

from pydantic import BaseModel, Field, PlainSerializer

DoubleNumber = Annotated[int, PlainSerializer(lambda v: v * 2)]


class Model1(BaseModel):
    my_number: DoubleNumber


class Model2(BaseModel):
    other_number: Annotated[DoubleNumber, Field(description='我的其他数字')]


class Model3(BaseModel):
    list_of_even_numbers: list[DoubleNumber]  # (1)!
```

1. 如[注解模式](./fields.md#the-annotated-pattern)文档中所述，我们还可以对注解的特定部分使用序列化器（在这种情况下，序列化应用于列表项，而不是整个列表）。

通过查看字段注解，也更容易理解哪些序列化器应用于类型。

##### 使用装饰器模式

使用 [`@field_serializer`][pydantic.field_serializer] 装饰器的主要好处之一是将函数应用于多个字段：

```python
from pydantic import BaseModel, field_serializer


class Model(BaseModel):
    f1: str
    f2: str

    @field_serializer('f1', 'f2', mode='plain')
    def capitalize(self, value: str) -> str:
        return value.capitalize()
```

以下是关于装饰器用法的一些额外说明：

* 如果您希望序列化器应用于所有字段（包括子类中定义的字段），可以将 `'*'` 作为字段名参数传递。
* 默认情况下，装饰器将确保提供的字段名在模型上定义。如果要在类创建期间禁用此检查，可以通过将 `False` 传递给 `check_fields` 参数来实现。当字段序列化器在基类上定义，并且期望字段存在于子类上时，这很有用。

### 模型序列化器

??? api "API 文档"
    [`pydantic.functional_serializers.model_serializer`][pydantic.functional_serializers.model_serializer]<br>

也可以使用 [`@model_serializer`][pydantic.model_serializer] 装饰器在整个模型上自定义序列化。

如果向 [`@model_serializer`][pydantic.model_serializer] 装饰器提供了 `return_type` 参数（或者序列化器函数上有可用的返回类型注解），它将用于构建额外的序列化器，以确保序列化的模型值符合此返回类型。

与[字段序列化器](#field-serializers)一样，可以使用**两种**不同类型的模型序列化器：

* ***Plain* 序列化器**：无条件调用以序列化模型。
  {#model-plain-serializer}

    ```python
    from pydantic import BaseModel, model_serializer


    class UserModel(BaseModel):
        username: str
        password: str

        @model_serializer(mode='plain')  # (1)!
        def serialize_model(self) -> str:  # (2)!
            return f'{self.username} - {self.password}'


    print(UserModel(username='foo', password='bar').model_dump())
    #> foo - bar
    ```

      1. `'plain'` 是装饰器的默认模式，可以省略。
      2. 您可以自由返回一个*不是*字典的值。

* ***Wrap* 序列化器**：提供更大的灵活性来自定义序列化行为。您可以在 Pydantic 序列化逻辑之前或之后运行代码。
  {#model-wrap-serializer}

    此类序列化器必须定义**强制**的额外参数 `*handler*` ：一个接受模型实例作为参数的可调用对象。在内部，此 handler 将模型的序列化委托给 Pydantic。您可以完全*不*调用 handler。

      ```python
      from pydantic import BaseModel, SerializerFunctionWrapHandler, model_serializer


      class UserModel(BaseModel):
          username: str
          password: str

          @model_serializer(mode='wrap')
          def serialize_model(
              self, handler: SerializerFunctionWrapHandler
          ) -> dict[str, object]:
              serialized = handler(self)
              serialized['fields'] = list(serialized)
              return serialized


      print(UserModel(username='foo', password='bar').model_dump())
      #> {'username': 'foo', 'password': 'bar', 'fields': ['username', 'password']}
      ```

## 序列化信息

字段和模型序列化器可调用对象（在所有模式下）都可以选择性地接受一个额外的参数 `info` ，提供有用的额外信息，例如：

* [用户定义的上下文](#serialization-context)
* 当前序列化模式：`'python'` 或 `'json'`（参见 [`mode`][pydantic.SerializationInfo.mode] 属性）
* 使用[序列化方法](#serializing-data)在序列化期间设置的各种参数
  （例如 [`exclude_unset`][pydantic.SerializationInfo.exclude_unset]、[`serialize_as_any`][pydantic.SerializationInfo.serialize_as_any]）
* 当前字段名，如果使用[字段序列化器](#field-serializers)（参见 [`field_name`][pydantic.FieldSerializationInfo.field_name] 属性）。

### 序列化上下文 {#serialization-context}

您可以向[序列化方法](#serializing-data)传递一个上下文对象，可以在序列化器函数内部使用 [`context`][pydantic.SerializationInfo.context] 属性访问：

```python
from pydantic import BaseModel, FieldSerializationInfo, field_serializer


class Model(BaseModel):
    text: str

    @field_serializer('text', mode='plain')
    @classmethod
    def remove_stopwords(cls, v: str, info: FieldSerializationInfo) -> str:
        if isinstance(info.context, dict):
            stopwords = info.context.get('stopwords', set())
            v = ' '.join(w for w in v.split() if w.lower() not in stopwords)
        return v


model = Model(text='This is an example document')
print(model.model_dump())  # 无上下文
#> {'text': 'This is an example document'}
print(model.model_dump(context={'stopwords': ['this', 'is', 'an']}))
#> {'text': 'example document'}
```

类似地，您可以[使用上下文进行验证](../concepts/validators.md#validation-context)。

## 序列化子类

<!-- old anchor added for backwards compatibility -->
<!-- markdownlint-disable-next-line no-empty-links -->
[](){#subclasses-of-standard-types}

### 支持类型的子类

支持类型的子类根据其超类进行序列化：

```python
from datetime import date

from pydantic import BaseModel


class MyDate(date):
    @property
    def my_date_format(self) -> str:
        return self.strftime('%d/%m/%Y')


class FooModel(BaseModel):
    date: date


m = FooModel(date=MyDate(2023, 1, 1))
print(m.model_dump_json())
#> {"date":"2023-01-01"}
```

<!-- old anchor added for backwards compatibility -->
<!-- markdownlint-disable-next-line no-empty-links -->
[](){#subclass-instances-for-fields-of-basemodel-dataclasses-typeddict}

### 类模型类型的子类 {#subclasses-of-model-like-types}

当使用模型类（Pydantic 模型、数据类等）作为字段注解时，默认行为是将字段值序列化为该类的实例，即使它是子类。更具体地说，只有类型注解上声明的字段才会包含在序列化结果中：

```python
from pydantic import BaseModel


class User(BaseModel):
    name: str


class UserLogin(User):
    password: str


class OuterModel(BaseModel):
    user: User


user = UserLogin(name='pydantic', password='hunter2')

m = OuterModel(user=user)
print(m)
#> user=UserLogin(name='pydantic', password='hunter2')
print(m.model_dump())  # (1)!
#> {'user': {'name': 'pydantic'}}
```

1. 注意：password 字段未包含

!!! warning "迁移警告"
    此行为与 Pydantic V1 的工作方式不同，在 V1 中，我们总是会在递归序列化模型到字典时包含所有（子类）字段。此行为更改背后的动机是，它有助于确保您确切知道在序列化时可能包含哪些字段，即使在实例化对象时传递了子类。特别是，这有助于防止在将敏感信息（如密码）作为子类字段添加时出现意外。要启用旧的 V1 行为，请参阅下一节。

### 使用鸭子类型序列化 🦆

鸭子类型序列化是基于实际字段值而不是字段定义来序列化模型实例的行为。这意味着对于使用模型类注解的字段，此类子类中存在的所有字段都将包含在序列化输出中。

此行为可以在字段级别和运行时配置，用于特定的序列化调用：

* 字段级别：使用 [`SerializeAsAny`][pydantic.functional_serializers.SerializeAsAny] 注解。
* 运行时级别：在调用[序列化方法](#serializing-data)时使用 `serialize_as_any` 参数。

我们在下面更详细地讨论这些选项：

#### `SerializeAsAny` 注解 {#serializeasany-annotation}

如果您想要鸭子类型序列化行为，可以在类型上使用 [`SerializeAsAny`][pydantic.functional_serializers.SerializeAsAny] 注解：

```python
from pydantic import BaseModel, SerializeAsAny


class User(BaseModel):
    name: str


class UserLogin(User):
    password: str


class OuterModel(BaseModel):
    as_any: SerializeAsAny[User]
    as_user: User


user = UserLogin(name='pydantic', password='password')

print(OuterModel(as_any=user, as_user=user).model_dump())
"""
{
    'as_any': {'name': 'pydantic', 'password': 'password'},
    'as_user': {'name': 'pydantic'},
}
"""
```

当类型被注解为 [`SerializeAsAny[<type>]`][pydantic.functional_serializers.SerializeAsAny] 时，验证行为将与注解为 `<type>` 相同，静态类型检查器将把注解视为简单的 `<type>`。在序列化时，字段将被序列化，就好像字段的类型提示是 [`Any`][typing.Any]，这就是名称的由来。

#### `serialize_as_any` 运行时设置

`serialize_as_any` 运行时设置可用于序列化模型数据，无论是否使用鸭子类型序列化行为。`serialize_as_any` 可以作为关键字参数传递给各种[序列化方法](#serializing-data)（例如Pydantic模型上的 [`model_dump()`][pydantic.BaseModel.model_dump] 和 [`model_dump_json()`][pydantic.BaseModel.model_dump_json]）。

```python
from pydantic import BaseModel


class User(BaseModel):
    name: str


class UserLogin(User):
    password: str


class OuterModel(BaseModel):
    user1: User
    user2: User


user = UserLogin(name='pydantic', password='password')

outer_model = OuterModel(user1=user, user2=user)
print(outer_model.model_dump(serialize_as_any=True))  # (1)!
"""
{
    'user1': {'name': 'pydantic', 'password': 'password'},
    'user2': {'name': 'pydantic', 'password': 'password'},
}
"""

print(outer_model.model_dump(serialize_as_any=False))  # (2)!
#> {'user1': {'name': 'pydantic'}, 'user2': {'name': 'pydantic'}}
```

1. 当 `serialize_as_any` 设置为 `True` 时，结果与 V1 匹配。
2. 当 `serialize_as_any` 设置为 `False`（V2 默认值）时，子类中存在但基类中不存在的字段不会包含在序列化中。

<!-- old anchor added for backwards compatibility -->
<!-- markdownlint-disable-next-line no-empty-links -->
[](){#advanced-include-and-exclude}
<!-- markdownlint-disable-next-line no-empty-links -->
[](){#model-and-field-level-include-and-exclude}

## 字段包含和排除

对于序列化，字段包含和排除可以通过两种方式配置：

* 在字段级别，使用 [`Field()` 函数](fields.md) 上的 `exclude` 和 `exclude_if` 参数。
* 使用[序列化方法](#serializing-data)上的各种序列化参数。

### 在字段级别

在字段级别，可以使用 `exclude` 和 `exclude_if` 参数：

```python
from pydantic import BaseModel, Field


class Transaction(BaseModel):
    id: int
    private_id: int = Field(exclude=True)
    value: int = Field(ge=0, exclude_if=lambda v: v == 0)


print(Transaction(id=1, private_id=2, value=0).model_dump())
#> {'id': 1}
```

字段级别的排除优先于下面描述的 `include` 序列化参数。

### 作为序列化方法的参数

当使用[序列化方法](#serializing-data)（例如 [`model_dump()`][pydantic.BaseModel.model_dump]）时，
可以使用几个参数来排除或包含字段。

#### 排除和包含特定字段

考虑以下模型：

```python {group="simple-exclude-include"}
from pydantic import BaseModel, Field, SecretStr


class User(BaseModel):
    id: int
    username: str
    password: SecretStr


class Transaction(BaseModel):
    id: str
    private_id: str = Field(exclude=True)
    user: User
    value: int


t = Transaction(
    id='1234567890',
    private_id='123',
    user=User(id=42, username='JohnDoe', password='hashedpassword'),
    value=9876543210,
)
```

`exclude` 参数可用于指定应排除哪些字段（包括其他字段），反之亦然，使用 `include` 参数。

```python {group="simple-exclude-include"}
# 使用集合：
print(t.model_dump(exclude={'user', 'value'}))
#> {'id': '1234567890'}

# 使用字典：
print(t.model_dump(exclude={'user': {'username', 'password'}, 'value': True}))
#> {'id': '1234567890', 'user': {'id': 42}}

# 使用`include`的相同配置：
print(t.model_dump(include={'id': True, 'user': {'id'}}))
#> {'id': '1234567890', 'user': {'id': 42}}
```

请注意，不支持使用 `False` 在 `exclude` 中*包含*字段（或在 `include` 中*排除*字段）。

也可以从序列和字典中排除或包含特定项：

```python {group="advanced-include-exclude"}
from pydantic import BaseModel


class Hobby(BaseModel):
    name: str
    info: str


class User(BaseModel):
    hobbies: list[Hobby]


user = User(
    hobbies=[
        Hobby(name='Programming', info='Writing code and stuff'),
        Hobby(name='Gaming', info='Hell Yeah!!!'),
    ],
)

print(user.model_dump(exclude={'hobbies': {-1: {'info'}}}))  # (1)!
"""
{
    'hobbies': [
        {'name': 'Programming', 'info': 'Writing code and stuff'},
        {'name': 'Gaming'},
    ]
}
"""
```

1. 使用 `include` 的等效调用为：

     ```python {lint="skip" group="advanced-include-exclude"}
     user.model_dump(
        include={'hobbies': {0: True, -1: {'name'}}}
     )
     ```

特殊键 `'__all__'` 可用于将排除/包含模式应用于所有成员：

```python {group="advanced-include-exclude"}
print(user.model_dump(exclude={'hobbies': {'__all__': {'info'}}}))
#> {'hobbies': [{'name': 'Programming'}, {'name': 'Gaming'}]}
```

#### 基于字段值排除和包含字段

当使用[序列化方法](#serializing-data)时，可以根据字段值排除字段，使用以下参数：

* `exclude_defaults`：排除所有值等于默认值的字段（使用相等（`==`）比较运算符）。
* `exclude_none`：排除所有值为 `None` 的字段。
* `exclude_unset`：Pydantic 跟踪在实例化期间*显式*设置的字段（使用 [`model_fields_set`][pydantic.BaseModel.model_fields_set] 属性）。使用 `exclude_unset`，任何未显式提供的字段将被排除：

    ```python {group="exclude-unset"}
    from pydantic import BaseModel


    class UserModel(BaseModel):
        name: str
        age: int = 18


    user = UserModel(name='John')
    print(user.model_fields_set)
    #> {'name'}

    print(user.model_dump(exclude_unset=True))
    #> {'name': 'John'}
    ```

    请注意，在实例创建*之后*修改字段会将其从未设置的字段中移除：

    ```python {group="exclude-unset"}
    user.age = 21

    print(user.model_dump(exclude_unset=True))
    #> {'name': 'John', 'age': 21}
    ```

    !!! tip
        实验性的 [`MISSING` 哨兵](./experimental.md#missing-sentinel) 可以用作 `exclude_unset` 的替代方案。
        任何值为 `MISSING` 的字段都会自动从序列化输出中排除。
