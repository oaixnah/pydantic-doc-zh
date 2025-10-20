---
description: Pydantic Models 文档 - 全面介绍如何使用 BaseModel 创建数据验证模型，包括字段定义、数据验证、序列化、嵌套模型、错误处理和高级特性。学习 Pydantic V2 模型的最佳实践，掌握数据转换、类型注解、模型配置和验证方法，提升 Python 数据处理能力。
---

??? api "API 文档"
    [`pydantic.main.BaseModel`][pydantic.main.BaseModel]<br>

在 Pydantic 中定义模式的主要方式之一是通过模型。模型是继承自 [`BaseModel`][pydantic.main.BaseModel] 的简单类，并将字段定义为带注解的属性。

您可以将模型视为类似于 C 等语言中的结构体，或者作为 API 中单个端点的要求。

模型与 Python 的 [dataclasses][dataclasses] 有许多相似之处，但设计上存在一些微妙但重要的差异，这些差异简化了与验证、序列化和 JSON 模式生成相关的某些工作流程。
您可以在文档的 [Dataclasses](dataclasses.md) 部分找到更多关于此的讨论。

不受信任的数据可以传递给模型，在解析和验证之后，Pydantic 保证结果模型实例的字段将符合模型上定义的字段类型。

!!! note "验证 — 一个*故意*的误称"
    <h3>简要说明</h3>

    我们使用术语"验证"来指代实例化符合指定类型和约束的模型（或其他类型）的过程。Pydantic 以此闻名，在口语中这个任务最广泛地被认为是"验证"，
    尽管在其他上下文中术语"验证"可能更具限制性。

    ---

    <h3>详细说明</h3>

    围绕术语"验证"的潜在混淆源于这样一个事实：严格来说，Pydantic 的主要关注点并不完全符合"验证"的字典定义：

    > <h3>验证</h3>
    > _名词_
    > 检查或证明某物有效性或准确性的行为。

    在 Pydantic 中，术语"验证"指的是实例化符合指定类型和约束的模型（或其他类型）的过程。Pydantic 保证输出的类型和约束，而不是输入数据。
    当考虑到 Pydantic 的 `ValidationError` 在数据无法成功解析为模型实例时被引发时，这种区别变得明显。

    虽然这种区别最初可能看起来很微妙，但它具有实际意义。
    在某些情况下，"验证"超出了模型创建的范围，可能包括数据的复制和强制转换。
    这可能涉及复制传递给构造函数的参数，以便在不改变原始输入数据的情况下执行到新类型的强制转换。
    要更深入地了解对您使用的影响，请参考下面的 [数据转换](#data-conversion) 和 [属性复制](#attribute-copies) 部分。

    本质上，Pydantic 的主要目标是确保后处理（称为"验证"）的结果结构精确符合应用的类型提示。
    鉴于"验证"作为此过程的通用术语被广泛采用，我们将在文档中一致使用它。

    虽然术语"解析"和"验证"以前可以互换使用，但今后我们旨在专门使用"验证"，
    而"解析"专门保留用于与 [JSON 解析](../concepts/json.md) 相关的讨论。

## 基本模型用法

!!! note

    Pydantic 严重依赖现有的 Python 类型构造来定义模型。如果您不熟悉这些，以下资源可能会有用：

    * [类型系统指南](https://typing.readthedocs.io/en/latest/guides/index.html)
    * [mypy 文档](https://mypy.readthedocs.io/en/latest/)

```python {group="basic-model"}
from pydantic import BaseModel, ConfigDict


class User(BaseModel):
    id: int
    name: str = 'Jane Doe'

    model_config = ConfigDict(str_max_length=10)  # (1)!
```

1. Pydantic 模型支持各种 [配置值](./config.md)
   （请参阅 [此处][pydantic.ConfigDict] 了解可用的配置值）。

在这个例子中，`User` 是一个有两个字段的模型：

* `id`，是一个整数（使用 [`int`][] 类型定义）并且是必需的
* `name`，是一个字符串（使用 [`str`][] 类型定义）并且不是必需的（它有默认值）。

关于 [类型](./types.md) 的文档扩展了支持的类型。

可以使用 [`Field()`][pydantic.Field] 函数以多种方式自定义字段。
有关更多信息，请参阅 [字段文档](./fields.md)。

然后可以实例化模型：

```python {group="basic-model"}
user = User(id='123')
```

`user` 是 `User` 的一个实例。对象的初始化将执行所有解析和验证。
如果没有引发 [`ValidationError`][pydantic_core.ValidationError] 异常，
您就知道结果模型实例是有效的。

模型的字段可以作为 `user` 对象的普通属性访问：

```python {group="basic-model"}
assert user.name == 'Jane Doe'  # (1)!
assert user.id == 123  # (2)!
assert isinstance(user.id, int)
```

1. `name` 在初始化 `user` 时没有设置，所以使用了默认值。
   可以检查 [`model_fields_set`][pydantic.BaseModel.model_fields_set] 属性
   来查看在实例化期间显式设置的字段名称。
2. 注意字符串 `'123'` 被强制转换为整数，其值为 `123`。
   有关 Pydantic 强制转换逻辑的更多详细信息可以在 [数据转换](#data-conversion) 部分找到。

可以使用 [`model_dump()`][pydantic.BaseModel.model_dump] 方法序列化模型实例：

```python {group="basic-model"}
assert user.model_dump() == {'id': 123, 'name': 'Jane Doe'}
```

在实例上调用 [dict][] 也会提供一个字典，但嵌套字段不会
递归转换为字典。 [`model_dump()`][pydantic.BaseModel.model_dump] 还
提供了许多参数来自定义序列化结果。

默认情况下，模型是可变的，可以通过属性赋值更改字段值：

```python {group="basic-model"}
user.id = 321
assert user.id == 321
```

!!! warning
    在定义模型时，请注意字段名称与其类型注解之间的命名冲突。

    例如，以下内容不会按预期行为，并会产生验证错误：

    ```python {test="skip"}
    from typing import Optional

    from pydantic import BaseModel


    class Boo(BaseModel):
        int: Optional[int] = None


    m = Boo(int=123)  # 验证将失败。
    ```

    由于 Python 评估 [带注解的赋值语句][annassign] 的方式，该语句等同于 `int: None = None`，因此
    导致验证错误。

### 模型方法和属性 {#model-methods-and-properties}

上面的例子只展示了模型功能的冰山一角。
模型具有以下方法和属性：

* [`model_validate()`][pydantic.main.BaseModel.model_validate]: 根据 Pydantic 模型验证给定对象。请参阅 [验证数据](#validating-data)。
* [`model_validate_json()`][pydantic.main.BaseModel.model_validate_json]: 根据 Pydantic 模型验证给定的 JSON 数据。请参阅
    [验证数据](#validating-data)。
* [`model_construct()`][pydantic.main.BaseModel.model_construct]: 在不运行验证的情况下创建模型。请参阅
    [创建不验证的模型](#creating-models-without-validation)。
* [`model_dump()`][pydantic.main.BaseModel.model_dump]: 返回模型字段和值的字典。请参阅
    [序列化](serialization.md#python-mode)。
* [`model_dump_json()`][pydantic.main.BaseModel.model_dump_json]: 返回 [`model_dump()`][pydantic.main.BaseModel.model_dump] 的 JSON 字符串表示。请参阅 [序列化](serialization.md#json-mode)。
* [`model_copy()`][pydantic.main.BaseModel.model_copy]: 返回模型的副本（默认情况下是浅拷贝）。请参阅
    [模型复制](#model-copy)。
* [`model_json_schema()`][pydantic.main.BaseModel.model_json_schema]: 返回表示模型 JSON 模式的 JSON 可序列化字典。请参阅 [JSON 模式](json_schema.md)。
* [`model_fields`][pydantic.main.BaseModel.model_fields]: 字段名称与其定义（[`FieldInfo`][pydantic.fields.FieldInfo] 实例）之间的映射。
* [`model_computed_fields`][pydantic.main.BaseModel.model_computed_fields]: 计算字段名称与其定义（[`ComputedFieldInfo`][pydantic.fields.ComputedFieldInfo] 实例）之间的映射。
* [`model_extra`][pydantic.main.BaseModel.model_extra]: 在验证期间设置的额外字段。
* [`model_fields_set`][pydantic.main.BaseModel.model_fields_set]: 在模型初始化时显式提供的字段集合。
* [`model_parametrized_name()`][pydantic.main.BaseModel.model_parametrized_name]: 计算泛型类参数化的类名。
* [`model_post_init()`][pydantic.main.BaseModel.model_post_init]: 在模型实例化后且所有字段验证器应用后执行其他操作。
* [`model_rebuild()`][pydantic.main.BaseModel.model_rebuild]: 重建模型模式，这也支持构建递归泛型模型。
    请参阅 [重建模型模式](#rebuilding-model-schema)。

!!! note
    请参阅 [`BaseModel`][pydantic.main.BaseModel] 的 API 文档，了解包括完整方法和属性列表的类定义。

!!! tip
    请参阅 [迁移指南](../migration.md) 中的 [对 `pydantic.BaseModel` 的更改](../migration.md#changes-to-pydanticbasemodel)，
    了解 Pydantic V1 的更改详情。

## 数据转换 {#data-conversion}

Pydantic 可能会强制转换输入数据以使其符合模型字段类型，
在某些情况下这可能导致信息丢失。
例如：

```python
from pydantic import BaseModel


class Model(BaseModel):
    a: int
    b: float
    c: str


print(Model(a=3.000, b='2.72', c=b'binary data').model_dump())
#> {'a': 3, 'b': 2.72, 'c': 'binary data'}
```

这是 Pydantic 的一个有意决定，通常是最有用的方法。请参阅
[此问题](https://github.com/pydantic/pydantic/issues/578) 了解关于该主题的详细讨论。

尽管如此，Pydantic 提供了 [严格模式](strict_mode.md)，在该模式下不执行数据转换。
值必须与声明的字段类型相同。

对于集合也是如此。在大多数情况下，您不应该使用抽象容器类，
而应该使用具体类型，例如 [`list`][]：

```python
from pydantic import BaseModel


class Model(BaseModel):
    items: list[int]  # (1)!


print(Model(items=(1, 2, 3)))
#> items=[1, 2, 3]
```

1. 在这种情况下，您可能会想使用抽象的 [`Sequence`][collections.abc.Sequence] 类型
   来允许列表和元组。但 Pydantic 会负责将元组输入转换为列表，因此
   在大多数情况下这是不必要的。

此外，使用这些抽象类型还可能导致 [验证性能较差](./performance.md#sequence-vs-list-or-tuple-with-mapping-vs-dict)，通常使用具体容器类型
可以避免不必要的检查。

<!-- old anchor added for backwards compatibility -->
<!-- markdownlint-disable-next-line no-empty-links -->
[](){#extra-fields}

## 额外数据 {#extra-data}

默认情况下，Pydantic 模型**在您提供额外数据时不会报错**，这些值将被简单地忽略：

```python
from pydantic import BaseModel


class Model(BaseModel):
    x: int


m = Model(x=1, y='a')
assert m.model_dump() == {'x': 1}
```

可以使用 [`extra`][pydantic.ConfigDict.extra] 配置值来控制此行为：

```python
from pydantic import BaseModel, ConfigDict


class Model(BaseModel):
    x: int

    model_config = ConfigDict(extra='allow')


m = Model(x=1, y='a')  # (1)!
assert m.model_dump() == {'x': 1, 'y': 'a'}
assert m.__pydantic_extra__ == {'y': 'a'}
```

1. 如果 [`extra`][pydantic.ConfigDict.extra] 设置为 `'forbid'`，这将失败。

配置可以取三个值：

* `'ignore'`: 忽略提供的额外数据（默认值）。
* `'forbid'`: 不允许提供额外数据。
* `'allow'`: 允许提供额外数据并存储在 `__pydantic_extra__` 字典属性中。
  `__pydantic_extra__` 可以显式注解以提供对额外字段的验证。

验证方法（例如 [`model_validate()`][pydantic.main.BaseModel.model_validate]）有一个可选的 `extra` 参数，
该参数将覆盖该验证调用的模型的 `extra` 配置值。

有关更多详细信息，请参阅 [`extra`][pydantic.ConfigDict.extra] API 文档。

Pydantic 数据类也支持额外数据（请参阅 [数据类配置](./dataclasses.md#dataclass-config) 部分）。

## 嵌套模型 {#nested-models}

可以使用模型本身作为注解中的类型来定义更复杂的层次数据结构。

```python
from typing import Optional

from pydantic import BaseModel


class Foo(BaseModel):
    count: int
    size: Optional[float] = None


class Bar(BaseModel):
    apple: str = 'x'
    banana: str = 'y'


class Spam(BaseModel):
    foo: Foo
    bars: list[Bar]


m = Spam(foo={'count': 4}, bars=[{'apple': 'x1'}, {'apple': 'x2'}])
print(m)
"""
foo=Foo(count=4, size=None) bars=[Bar(apple='x1', banana='y'), Bar(apple='x2', banana='y')]
"""
print(m.model_dump())
"""
{
    'foo': {'count': 4, 'size': None},
    'bars': [{'apple': 'x1', 'banana': 'y'}, {'apple': 'x2', 'banana': 'y'}],
}
"""
```

支持自引用模型。有关更多详细信息，请参阅相关的
[前向注解](forward_annotations.md#self-referencing-or-recursive-models) 文档。

## 重建模型模式 {#rebuilding-model-schema}

当您在代码中定义模型类时，Pydantic 将分析类的主体以收集执行验证和序列化所需的各种信息，
这些信息收集在一个核心模式中。值得注意的是，模型类型注解会被评估以
了解每个字段的有效类型（更多信息可以在 [架构](../internals/architecture.md) 文档中找到）。
但是，注解可能引用在模型类创建时未定义的符号。
为了解决这个问题，可以使用 [`model_rebuild()`][pydantic.main.BaseModel.model_rebuild] 方法：

```python
from pydantic import BaseModel, PydanticUserError


class Foo(BaseModel):
    x: 'Bar'  # (1)!


try:
    Foo.model_json_schema()
except PydanticUserError as e:
    print(e)
    """
    `Foo` is not fully defined; you should define `Bar`, then call `Foo.model_rebuild()`.

    For further information visit https://errors.pydantic.dev/2/u/class-not-fully-defined
    """


class Bar(BaseModel):
    pass


Foo.model_rebuild()
print(Foo.model_json_schema())
"""
{
    '$defs': {'Bar': {'properties': {}, 'title': 'Bar', 'type': 'object'}},
    'properties': {'x': {'$ref': '#/$defs/Bar'}},
    'required': ['x'],
    'title': 'Foo',
    'type': 'object',
}
"""
```

1. 在创建 `Foo` 类时，`Bar` 尚未定义。因此，
    使用了 [前向注解](forward_annotations.md)。

Pydantic 会尝试自动确定何时需要这样做，如果未完成则会报错，但您可能希望在处理递归模型或泛型时
主动调用 [`model_rebuild()`][pydantic.main.BaseModel.model_rebuild]。

在 V2 中，[`model_rebuild()`][pydantic.main.BaseModel.model_rebuild] 取代了 V1 中的 `update_forward_refs()`。新行为有一些细微差异。
最大的变化是，当在最外层模型上调用 [`model_rebuild()`][pydantic.main.BaseModel.model_rebuild] 时，它会构建一个用于验证整个模型
（包括嵌套模型）的核心模式，因此在调用 [`model_rebuild()`][pydantic.main.BaseModel.model_rebuild] 之前，所有级别的所有类型都需要准备就绪。

## 任意类实例

（以前称为"ORM 模式"/`from_orm`）。

Pydantic 模型也可以通过读取与模型字段名称对应的实例属性来从任意类实例创建。
此功能的一个常见应用是与对象关系映射（ORMs）集成。

为此，将 [`from_attributes`][pydantic.config.ConfigDict.from_attributes] 配置值设置为 `True`
（有关更多详细信息，请参阅 [配置](./config.md) 文档）。

此处的示例使用 [SQLAlchemy](https://www.sqlalchemy.org/)，但相同的方法应适用于任何 ORM。

```python
from typing import Annotated

from sqlalchemy import ARRAY, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from pydantic import BaseModel, ConfigDict, StringConstraints


class Base(DeclarativeBase):
    pass


class CompanyOrm(Base):
    __tablename__ = 'companies'

    id: Mapped[int] = mapped_column(primary_key=True, nullable=False)
    public_key: Mapped[str] = mapped_column(
        String(20), index=True, nullable=False, unique=True
    )
    domains: Mapped[list[str]] = mapped_column(ARRAY(String(255)))


class CompanyModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    public_key: Annotated[str, StringConstraints(max_length=20)]
    domains: list[Annotated[str, StringConstraints(max_length=255)]]


co_orm = CompanyOrm(
    id=123,
    public_key='foobar',
    domains=['example.com', 'foobar.com'],
)
print(co_orm)
#> <__main__.CompanyOrm object at 0x0123456789ab>
co_model = CompanyModel.model_validate(co_orm)
print(co_model)
#> id=123 public_key='foobar' domains=['example.com', 'foobar.com']
```

### 嵌套属性

当使用属性解析模型时，模型实例将从顶级属性和更深层次的嵌套属性（如适用）创建。

以下是一个演示该原理的示例：

```python
from pydantic import BaseModel, ConfigDict


class PetCls:
    def __init__(self, *, name: str, species: str):
        self.name = name
        self.species = species


class PersonCls:
    def __init__(self, *, name: str, age: float = None, pets: list[PetCls]):
        self.name = name
        self.age = age
        self.pets = pets


class Pet(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    species: str


class Person(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    age: float = None
    pets: list[Pet]


bones = PetCls(name='Bones', species='dog')
orion = PetCls(name='Orion', species='cat')
anna = PersonCls(name='Anna', age=20, pets=[bones, orion])
anna_model = Person.model_validate(anna)
print(anna_model)
"""
name='Anna' age=20.0 pets=[Pet(name='Bones', species='dog'), Pet(name='Orion', species='cat')]
"""
```

## 错误处理 {#error-handling}

每当 Pydantic 在验证的数据中发现错误时，它将引发 [`ValidationError`][pydantic_core.ValidationError] 异常。

无论发现多少错误，都会引发单个异常，并且该验证错误
将包含所有错误的信息以及它们是如何发生的。

有关标准和自定义错误的详细信息，请参阅 [错误处理](../errors/errors.md)。

作为演示：

```python
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    list_of_ints: list[int]
    a_float: float


data = dict(
    list_of_ints=['1', 2, 'bad'],
    a_float='not a float',
)

try:
    Model(**data)
except ValidationError as e:
    print(e)
    """
    2 validation errors for Model
    list_of_ints.2
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='bad', input_type=str]
    a_float
      Input should be a valid number, unable to parse string as a number [type=float_parsing, input_value='not a float', input_type=str]
    """
```

## 验证数据 {#validating-data}

Pydantic 在模型类上提供了三种解析数据的方法：

* [`model_validate()`][pydantic.main.BaseModel.model_validate]: 这与模型的 `__init__` 方法非常相似，
  不同之处在于它接受字典或对象而不是关键字参数。如果传递的对象无法验证，
  或者它不是字典或相关模型的实例，将引发 [`ValidationError`][pydantic_core.ValidationError]。
* [`model_validate_json()`][pydantic.main.BaseModel.model_validate_json]: 这将提供的数据作为 JSON 字符串或 `bytes` 对象进行验证。
  如果您的传入数据是 JSON 负载，这通常被认为更快（而不是手动将数据解析为字典）。
  在文档的 [JSON](../concepts/json.md) 部分了解更多关于 JSON 解析的信息。
* [`model_validate_strings()`][pydantic.main.BaseModel.model_validate_strings]: 这接受一个具有字符串键和值的字典（可以是嵌套的），并在 JSON 模式下验证数据，以便将所述字符串强制转换为正确的类型。

```python
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ValidationError


class User(BaseModel):
    id: int
    name: str = 'John Doe'
    signup_ts: Optional[datetime] = None


m = User.model_validate({'id': 123, 'name': 'James'})
print(m)
#> id=123 name='James' signup_ts=None

try:
    User.model_validate(['not', 'a', 'dict'])
except ValidationError as e:
    print(e)
    """
    1 validation error for User
      Input should be a valid dictionary or instance of User [type=model_type, input_value=['not', 'a', 'dict'], input_type=list]
    """

m = User.model_validate_json('{"id": 123, "name": "James"}')
print(m)
#> id=123 name='James' signup_ts=None

try:
    m = User.model_validate_json('{"id": 123, "name": 123}')
except ValidationError as e:
    print(e)
    """
    1 validation error for User
    name
      Input should be a valid string [type=string_type, input_value=123, input_type=int]
    """

try:
    m = User.model_validate_json('invalid JSON')
except ValidationError as e:
    print(e)
    """
    1 validation error for User
      Invalid JSON: expected value at line 1 column 1 [type=json_invalid, input_value='invalid JSON', input_type=str]
    """

m = User.model_validate_strings({'id': '123', 'name': 'James'})
print(m)
#> id=123 name='James' signup_ts=None

m = User.model_validate_strings(
    {'id': '123', 'name': 'James', 'signup_ts': '2024-04-01T12:00:00'}
)
print(m)
#> id=123 name='James' signup_ts=datetime.datetime(2024, 4, 1, 12, 0)

try:
    m = User.model_validate_strings(
        {'id': '123', 'name': 'James', 'signup_ts': '2024-04-01'}, strict=True
    )
except ValidationError as e:
    print(e)
    """
    1 validation error for User
    signup_ts
      Input should be a valid datetime, invalid datetime separator, expected `T`, `t`, `_` or space [type=datetime_parsing, input_value='2024-04-01', input_type=str]
    """
```

如果您想要验证非 JSON 格式的序列化数据，您应该自己将数据加载到字典中，
然后将其传递给 [`model_validate`][pydantic.main.BaseModel.model_validate]。

!!! note
    根据所涉及的类型和模型配置，[`model_validate`][pydantic.main.BaseModel.model_validate]
    和 [`model_validate_json`][pydantic.main.BaseModel.model_validate_json] 可能具有不同的验证行为。
    如果您有来自非 JSON 源的数据，但想要获得与 [`model_validate_json`][pydantic.main.BaseModel.model_validate_json] 相同的验证
    行为和错误，我们目前的建议是使用 `model_validate_json(json.dumps(data))`，或者如果数据采用具有字符串键和值的（可能是嵌套的）字典形式，则使用 [`model_validate_strings`][pydantic.main.BaseModel.model_validate_strings]。

!!! note
    如果您将模型实例传递给 [`model_validate`][pydantic.main.BaseModel.model_validate]，您需要考虑在模型配置中设置
    [`revalidate_instances`][pydantic.ConfigDict.revalidate_instances]。
    如果您不设置此值，则将在模型实例上跳过验证。请参阅以下示例：

    === ":x: `revalidate_instances='never'`"
        ```python
        from pydantic import BaseModel


        class Model(BaseModel):
            a: int


        m = Model(a=0)
        # note: setting `validate_assignment` to `True` in the config can prevent this kind of misbehavior.
        m.a = 'not an int'

        # doesn't raise a validation error even though m is invalid
        m2 = Model.model_validate(m)
        ```

    === ":white_check_mark: `revalidate_instances='always'`"
        ```python
        from pydantic import BaseModel, ConfigDict, ValidationError


        class Model(BaseModel):
            a: int

            model_config = ConfigDict(revalidate_instances='always')


        m = Model(a=0)
        # note: setting `validate_assignment` to `True` in the config can prevent this kind of misbehavior.
        m.a = 'not an int'

        try:
            m2 = Model.model_validate(m)
        except ValidationError as e:
            print(e)
            """
            1 validation error for Model
            a
              Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='not an int', input_type=str]
            """
        ```

### 创建模型而不进行验证 {#creating-models-without-validation}

Pydantic 还提供了 [`model_construct()`][pydantic.main.BaseModel.model_construct] 方法，该方法允许**不进行验证**创建模型。
这在至少以下几种情况下很有用：

* 当处理已知有效的复杂数据时（出于性能原因）
* 当一个或多个验证器函数不是幂等时
* 当一个或多个验证器函数具有您不希望触发的副作用时

!!! warning
    [`model_construct()`][pydantic.main.BaseModel.model_construct] 不进行任何验证，这意味着它可以创建
    无效的模型。**您应该只对已经验证过的数据或您绝对信任的数据使用 [`model_construct()`][pydantic.main.BaseModel.model_construct]
    方法。**

!!! note
    在 Pydantic V2 中，验证（无论是直接实例化还是使用 `model_validate*` 方法）与
    [`model_construct()`][pydantic.main.BaseModel.model_construct] 之间的性能差距已经大大缩小。
    对于简单模型，使用验证甚至可能更快。如果您出于性能原因使用 [`model_construct()`][pydantic.main.BaseModel.model_construct]，
    您可能需要在假设它实际上更快之前对您的用例进行分析。

请注意，对于[根模型](#rootmodel-and-custom-root-types)，根值可以位置传递给
[`model_construct()`][pydantic.main.BaseModel.model_construct]，而不是使用关键字参数。

以下是关于 [`model_construct()`][pydantic.main.BaseModel.model_construct] 行为的一些额外说明：

* 当我们说"不执行验证"时——这包括将字典转换为模型实例。因此，如果您有一个字段
  引用模型类型，您需要自己将内部字典转换为模型。
* 如果您不为具有默认值的字段传递关键字参数，仍将使用默认值。
* 对于具有私有属性的模型，`__pydantic_private__` 字典将以与创建模型时相同的方式填充
  验证。
* 不会调用模型或其任何父类的 `__init__` 方法，即使定义了自定义 `__init__` 方法。

!!! note "关于 [`model_construct()`][pydantic.main.BaseModel.model_construct] 的[额外数据](#extra-data)行为"

    * 对于将 [`extra`][pydantic.ConfigDict.extra] 设置为 `'allow'` 的模型，不对应于字段的数据将正确存储在
    `__pydantic_extra__` 字典中并保存到模型的 `__dict__` 属性中。
    * 对于将 [`extra`][pydantic.ConfigDict.extra] 设置为 `'ignore'` 的模型，不对应于字段的数据将被忽略——也就是说，
    不会存储在实例的 `__pydantic_extra__` 或 `__dict__` 中。
    * 与通过验证实例化模型不同，当 [`extra`][pydantic.ConfigDict.extra] 设置为 `'forbid'` 时调用 [`model_construct()`][pydantic.main.BaseModel.model_construct] 不会在存在不对应于字段的数据时引发错误。相反，所述输入数据将被简单地忽略。

## 模型复制 {#model-copy}

??? api "API 文档"
    [`pydantic.main.BaseModel.model_copy`][pydantic.main.BaseModel.model_copy]<br>

[`model_copy()`][pydantic.BaseModel.model_copy] 方法允许复制模型（带有可选更新），
这在处理冻结模型时特别有用。

```python
from pydantic import BaseModel


class BarModel(BaseModel):
    whatever: int


class FooBarModel(BaseModel):
    banana: float
    foo: str
    bar: BarModel


m = FooBarModel(banana=3.14, foo='hello', bar={'whatever': 123})

print(m.model_copy(update={'banana': 0}))
#> banana=0 foo='hello' bar=BarModel(whatever=123)

# 正常复制为 bar 提供相同的对象引用：
print(id(m.bar) == id(m.model_copy().bar))
#> True
# 深度复制为 `bar` 提供新的对象引用：
print(id(m.bar) == id(m.model_copy(deep=True).bar))
#> False
```

## 泛型模型 {#generic-models}

Pydantic 支持创建泛型模型，以便更轻松地重用通用模型结构。新的
[类型参数语法][type-params]（由 Python 3.12 中的 [PEP 695](https://peps.python.org/pep-0695/) 引入）
和旧语法都受支持（有关更多详细信息，请参阅
[Python 文档](https://docs.python.org/3/library/typing.html#building-generic-types-and-type-aliases)）。

以下是一个使用泛型 Pydantic 模型创建易于重用的 HTTP 响应负载包装器的示例：

<!-- TODO: tabs should be auto-generated if using Ruff (https://github.com/pydantic/pydantic/issues/10083) -->

=== "Python 3.9 及以上版本"

    ```python {upgrade="skip"}
    from typing import Generic, TypeVar

    from pydantic import BaseModel, ValidationError

    DataT = TypeVar('DataT')  # (1)!


    class DataModel(BaseModel):
        number: int


    class Response(BaseModel, Generic[DataT]):  # (2)!
        data: DataT  # (3)!


    print(Response[int](data=1))
    #> data=1
    print(Response[str](data='value'))
    #> data='value'
    print(Response[str](data='value').model_dump())
    #> {'data': 'value'}

    data = DataModel(number=1)
    print(Response[DataModel](data=data).model_dump())
    #> {'data': {'number': 1}}
    try:
        Response[int](data='value')
    except ValidationError as e:
        print(e)
        """
        1 validation error for Response[int]
        data
          Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='value', input_type=str]
        """
    ```

    1. 声明一个或多个[类型变量][typing.TypeVar]以用于参数化您的模型。
    2. 声明一个继承自 [`BaseModel`][pydantic.BaseModel] 和 [`typing.Generic`][]
       （按此特定顺序）的 Pydantic 模型，并将您之前声明的类型变量列表作为参数添加到
       [`Generic`][typing.Generic] 父类。
    3. 在您希望用其他类型替换的地方使用类型变量作为注解。

=== "Python 3.12 及以上版本（新语法）"

    ```python {requires="3.12" upgrade="skip" lint="skip"}
    from pydantic import BaseModel, ValidationError


    class DataModel(BaseModel):
        number: int


    class Response[DataT](BaseModel):  # (1)!
        data: DataT  # (2)!


    print(Response[int](data=1))
    #> data=1
    print(Response[str](data='value'))
    #> data='value'
    print(Response[str](data='value').model_dump())
    #> {'data': 'value'}

    data = DataModel(number=1)
    print(Response[DataModel](data=data).model_dump())
    #> {'data': {'number': 1}}
    try:
        Response[int](data='value')
    except ValidationError as e:
        print(e)
        """
        1 validation error for Response[int]
        data
          Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='value', input_type=str]
        """
    ```

    1. 声明一个 Pydantic 模型并将类型变量列表添加为类型参数。
    2. 在您希望用其他类型替换的地方使用类型变量作为注解。

!!! warning
    当使用具体类型参数化模型时，如果类型变量有上界，Pydantic **不会**验证提供的类型
    是否[可分配给类型变量][spec-typevars-bound]。

    [spec-typevars-bound]: https://typing.readthedocs.io/en/latest/spec/generics.html#type-variables-with-an-upper-bound

在泛型模型上设置的任何[配置](./config.md)、[验证](./validators.md)或[序列化](./serialization.md)逻辑
也将应用于参数化类，就像从模型类继承时一样。任何自定义方法或属性也将被继承。

泛型模型还与类型检查器正确集成，因此您将获得所有类型检查
就像您为每个参数化声明一个不同的类型一样。

!!! note
    在内部，当泛型模型类被参数化时，Pydantic 在运行时创建泛型模型的子类。
    这些类被缓存，因此使用泛型模型引入的开销应该是最小的。

要从泛型模型继承并保持其泛型特性，子类还必须继承自
[`Generic`][typing.Generic]：

```python
from typing import Generic, TypeVar

from pydantic import BaseModel

TypeX = TypeVar('TypeX')


class BaseClass(BaseModel, Generic[TypeX]):
    X: TypeX


class ChildClass(BaseClass[TypeX], Generic[TypeX]):
    pass


# Parametrize `TypeX` with `int`:
print(ChildClass[int](X=1))
#> X=1
```

您还可以创建一个泛型子类，部分或完全替换超类中的类型变量：

```python
from typing import Generic, TypeVar

from pydantic import BaseModel

TypeX = TypeVar('TypeX')
TypeY = TypeVar('TypeY')
TypeZ = TypeVar('TypeZ')


class BaseClass(BaseModel, Generic[TypeX, TypeY]):
    x: TypeX
    y: TypeY


class ChildClass(BaseClass[int, TypeY], Generic[TypeY, TypeZ]):
    z: TypeZ


# Parametrize `TypeY` with `str`:
print(ChildClass[str, int](x='1', y='y', z='3'))
#> x=1 y='y' z=3
```

如果具体子类的名称很重要，您还可以通过重写[`model_parametrized_name()`][pydantic.main.BaseModel.model_parametrized_name]方法来覆盖默认的名称生成：

```python
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

DataT = TypeVar('DataT')


class Response(BaseModel, Generic[DataT]):
    data: DataT

    @classmethod
    def model_parametrized_name(cls, params: tuple[type[Any], ...]) -> str:
        return f'{params[0].__name__.title()}Response'


print(repr(Response[int](data=1)))
#> IntResponse(data=1)
print(repr(Response[str](data='a')))
#> StrResponse(data='a')
```

您可以在其他模型中使用参数化泛型模型作为类型：

```python
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar('T')


class ResponseModel(BaseModel, Generic[T]):
    content: T


class Product(BaseModel):
    name: str
    price: float


class Order(BaseModel):
    id: int
    product: ResponseModel[Product]


product = Product(name='Apple', price=0.5)
response = ResponseModel[Product](content=product)
order = Order(id=1, product=response)
print(repr(order))
"""
Order(id=1, product=ResponseModel[Product](content=Product(name='Apple', price=0.5)))
"""
```

在嵌套模型中使用相同的类型变量允许您在模型的不同点强制执行类型关系：

```python
from typing import Generic, TypeVar

from pydantic import BaseModel, ValidationError

T = TypeVar('T')


class InnerT(BaseModel, Generic[T]):
    inner: T


class OuterT(BaseModel, Generic[T]):
    outer: T
    nested: InnerT[T]


nested = InnerT[int](inner=1)
print(OuterT[int](outer=1, nested=nested))
#> outer=1 nested=InnerT[int](inner=1)
try:
    print(OuterT[int](outer='a', nested=InnerT(inner='a')))  # (1)!
except ValidationError as e:
    print(e)
    """
    2 validation errors for OuterT[int]
    outer
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='a', input_type=str]
    nested.inner
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='a', input_type=str]
    """
```

1. `OuterT` 模型使用 `int` 参数化，但在验证期间与 `T` 注解关联的数据类型为 `str`，导致验证错误。

!!! warning
    虽然可能不会引发错误，但我们强烈建议不要在 [`isinstance()`](https://docs.python.org/3/library/functions.html#isinstance) 检查中使用参数化泛型。

    例如，您不应该执行 `isinstance(my_model, MyGenericModel[int])`。但是，执行 `isinstance(my_model, MyGenericModel)` 是可以的（请注意，对于标准泛型，使用参数化泛型类进行子类检查会引发错误）。

    如果您需要对参数化泛型执行 [`isinstance()`](https://docs.python.org/3/library/functions.html#isinstance) 检查，可以通过子类化参数化泛型类来实现：

    ```python {test="skip" lint="skip"}
    class MyIntModel(MyGenericModel[int]): ...

    isinstance(my_model, MyIntModel)
    ```

??? note "实现细节"
    当使用嵌套泛型模型时，Pydantic有时会执行重新验证，以产生最直观的验证结果。
    具体来说，如果您有一个类型为 `GenericModel[SomeType]` 的字段，并且您针对此字段验证像 `GenericModel[SomeCompatibleType]` 这样的数据，
    我们将检查数据，识别输入数据是 `GenericModel` 的一种"松散"子类，并重新验证包含的 `SomeCompatibleType` 数据。

    这会增加一些验证开销，但对于如下所示的情况，它使事情更加直观。

    ```python
    from typing import Any, Generic, TypeVar

    from pydantic import BaseModel

    T = TypeVar('T')


    class GenericModel(BaseModel, Generic[T]):
        a: T


    class Model(BaseModel):
        inner: GenericModel[Any]


    print(repr(Model.model_validate(Model(inner=GenericModel[int](a=1)))))
    #> Model(inner=GenericModel[Any](a=1))
    ```

    请注意，如果您针对 `GenericModel[int]` 进行验证并传入一个 `GenericModel[str](a='not an int')` 实例，验证仍然会失败。

    还值得注意的是，这种模式也会重新触发任何自定义验证，比如额外的模型验证器等。
    验证器将在第一次传递时被调用一次，直接针对 `GenericModel[Any]` 进行验证。该验证失败，因为 `GenericModel[int]` 不是 `GenericModel[Any]` 的子类。这与上面关于在 `isinstance()` 和 `issubclass()` 检查中使用参数化泛型的复杂性的警告有关。
    然后，验证器将在第二次传递时再次被调用，在更宽松的强制重新验证阶段，这会成功。
    为了更好地理解这个后果，请参见下面：

    ```python {test="skip"}
    from typing import Any, Generic, Self, TypeVar

    from pydantic import BaseModel, model_validator

    T = TypeVar('T')


    class GenericModel(BaseModel, Generic[T]):
        a: T

        @model_validator(mode='after')
        def validate_after(self: Self) -> Self:
            print('after validator running custom validation...')
            return self


    class Model(BaseModel):
        inner: GenericModel[Any]


    m = Model.model_validate(Model(inner=GenericModel[int](a=1)))
    #> after validator running custom validation...
    #> after validator running custom validation...
    print(repr(m))
    #> Model(inner=GenericModel[Any](a=1))
    ```

### 未参数化类型变量的验证

当类型变量未被参数化时，Pydantic 处理泛型模型的方式类似于处理内置泛型类型如 [`list`][] 和 [`dict`][]：

* 如果类型变量[绑定](https://typing.readthedocs.io/en/latest/reference/generics.html#type-variables-with-upper-bounds)
  或[约束](https://typing.readthedocs.io/en/latest/reference/generics.html#type-variables-with-constraints)到特定类型，
  将使用该类型。
* 如果类型变量有默认类型（根据 [PEP 696](https://peps.python.org/pep-0696/) 指定），将使用该默认类型。
* 对于未绑定或未约束的类型变量，Pydantic 将回退到 [`Any`][typing.Any]。

```python
from typing import Generic

from typing_extensions import TypeVar

from pydantic import BaseModel, ValidationError

T = TypeVar('T')
U = TypeVar('U', bound=int)
V = TypeVar('V', default=str)


class Model(BaseModel, Generic[T, U, V]):
    t: T
    u: U
    v: V


print(Model(t='t', u=1, v='v'))
#> t='t' u=1 v='v'

try:
    Model(t='t', u='u', v=1)
except ValidationError as exc:
    print(exc)
    """
    2 validation errors for Model
    u
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='u', input_type=str]
    v
      Input should be a valid string [type=string_type, input_value=1, input_type=int]
    """
```

!!! warning

    在某些情况下，针对未参数化泛型模型的验证可能导致数据丢失。具体来说，如果使用了类型变量上界、约束或默认值的子类型，并且模型没有显式参数化，结果类型**将不是**提供的类型：

    ```python
    from typing import Generic, TypeVar

    from pydantic import BaseModel

    ItemT = TypeVar('ItemT', bound='ItemBase')


    class ItemBase(BaseModel): ...


    class IntItem(ItemBase):
        value: int


    class ItemHolder(BaseModel, Generic[ItemT]):
        item: ItemT


    loaded_data = {'item': {'value': 1}}


    print(ItemHolder(**loaded_data))  # (1)!
    #> item=ItemBase()

    print(ItemHolder[IntItem](**loaded_data))  # (2)!
    #> item=IntItem(value=1)
    ```

    1. 当泛型未被参数化时，输入数据针对 `ItemT` 上界进行验证。
       由于 `ItemBase` 没有字段，`item` 字段信息丢失。
    2. 在这种情况下，类型变量被显式参数化，因此输入数据针对 `IntItem` 类进行验证。

### 未参数化类型变量的序列化

当使用带有[上界](https://typing.readthedocs.io/en/latest/reference/generics.html#type-variables-with-upper-bounds)、[约束](https://typing.readthedocs.io/en/latest/reference/generics.html#type-variables-with-constraints)或默认值的类型变量时，序列化行为会有所不同：

如果Pydantic模型被用作类型变量的上界，并且该类型变量从未被参数化，那么Pydantic将使用上界进行验证，但在序列化方面将该值视为[`Any`][typing.Any]：

```python
from typing import Generic, TypeVar

from pydantic import BaseModel


class ErrorDetails(BaseModel):
    foo: str


ErrorDataT = TypeVar('ErrorDataT', bound=ErrorDetails)


class Error(BaseModel, Generic[ErrorDataT]):
    message: str
    details: ErrorDataT


class MyErrorDetails(ErrorDetails):
    bar: str


# serialized as Any
error = Error(
    message='We just had an error',
    details=MyErrorDetails(foo='var', bar='var2'),
)
assert error.model_dump() == {
    'message': 'We just had an error',
    'details': {
        'foo': 'var',
        'bar': 'var2',
    },
}

# serialized using the concrete parametrization
# note that `'bar': 'var2'` is missing
error = Error[ErrorDetails](
    message='We just had an error',
    details=ErrorDetails(foo='var'),
)
assert error.model_dump() == {
    'message': 'We just had an error',
    'details': {
        'foo': 'var',
    },
}
```

这是上述行为的另一个示例，枚举了关于绑定规范和泛型类型参数化的所有排列：

```python
from typing import Generic, TypeVar

from pydantic import BaseModel

TBound = TypeVar('TBound', bound=BaseModel)
TNoBound = TypeVar('TNoBound')


class IntValue(BaseModel):
    value: int


class ItemBound(BaseModel, Generic[TBound]):
    item: TBound


class ItemNoBound(BaseModel, Generic[TNoBound]):
    item: TNoBound


item_bound_inferred = ItemBound(item=IntValue(value=3))
item_bound_explicit = ItemBound[IntValue](item=IntValue(value=3))
item_no_bound_inferred = ItemNoBound(item=IntValue(value=3))
item_no_bound_explicit = ItemNoBound[IntValue](item=IntValue(value=3))

# calling `print(x.model_dump())` on any of the above instances results in the following:
#> {'item': {'value': 3}}
```

但是，如果使用了[约束](https://typing.readthedocs.io/en/latest/reference/generics.html#type-variables-with-constraints)
或默认值（根据[PEP 696](https://peps.python.org/pep-0696/)），那么如果类型变量未被参数化，将使用默认类型或约束
进行验证和序列化。您可以使用[`SerializeAsAny`](./serialization.md#serializeasany-annotation)来覆盖此行为：

```python
from typing import Generic

from typing_extensions import TypeVar

from pydantic import BaseModel, SerializeAsAny


class ErrorDetails(BaseModel):
    foo: str


ErrorDataT = TypeVar('ErrorDataT', default=ErrorDetails)


class Error(BaseModel, Generic[ErrorDataT]):
    message: str
    details: ErrorDataT


class MyErrorDetails(ErrorDetails):
    bar: str


# serialized using the default's serializer
error = Error(
    message='We just had an error',
    details=MyErrorDetails(foo='var', bar='var2'),
)
assert error.model_dump() == {
    'message': 'We just had an error',
    'details': {
        'foo': 'var',
    },
}
# If `ErrorDataT` was using an upper bound, `bar` would be present in `details`.


class SerializeAsAnyError(BaseModel, Generic[ErrorDataT]):
    message: str
    details: SerializeAsAny[ErrorDataT]


# serialized as Any
error = SerializeAsAnyError(
    message='We just had an error',
    details=MyErrorDetails(foo='var', bar='baz'),
)
assert error.model_dump() == {
    'message': 'We just had an error',
    'details': {
        'foo': 'var',
        'bar': 'baz',
    },
}
```

## 动态模型创建 {#dynamic-model-creation}

??? api "API 文档"
    [`pydantic.main.create_model`][pydantic.main.create_model]<br>

在某些情况下，需要使用运行时信息来指定字段创建模型。
Pydantic提供了[`create_model()`][pydantic.create_model]函数来允许动态创建模型：

```python
from pydantic import BaseModel, create_model

DynamicFoobarModel = create_model('DynamicFoobarModel', foo=str, bar=(int, 123))

# Equivalent to:


class StaticFoobarModel(BaseModel):
    foo: str
    bar: int = 123
```

字段定义被指定为关键字参数，应该是以下之一：

* 单个元素，表示字段的类型注解。
* 一个二元组，第一个元素是类型，第二个元素是分配的值
  （可以是默认值或[`Field()`][pydantic.Field]函数）。

这是一个更高级的示例：

```python
from typing import Annotated

from pydantic import BaseModel, Field, PrivateAttr, create_model

DynamicModel = create_model(
    'DynamicModel',
    foo=(str, Field(alias='FOO')),
    bar=Annotated[str, Field(description='Bar field')],
    _private=(int, PrivateAttr(default=1)),
)


class StaticModel(BaseModel):
    foo: str = Field(alias='FOO')
    bar: Annotated[str, Field(description='Bar field')]
    _private: int = PrivateAttr(default=1)
```

特殊的关键字参数`__config__`和`__base__`可用于自定义新模型。
这包括使用额外字段扩展基础模型。

```python
from pydantic import BaseModel, create_model


class FooModel(BaseModel):
    foo: str
    bar: int = 123


BarModel = create_model(
    'BarModel',
    apple=(str, 'russet'),
    banana=(str, 'yellow'),
    __base__=FooModel,
)
print(BarModel)
#> <class '__main__.BarModel'>
print(BarModel.model_fields.keys())
#> dict_keys(['foo', 'bar', 'apple', 'banana'])
```

您还可以通过向`__validators__`参数传递字典来添加验证器。

```python {rewrite_assert="false"}
from pydantic import ValidationError, create_model, field_validator


def alphanum(cls, v):
    assert v.isalnum(), 'must be alphanumeric'
    return v


validators = {
    'username_validator': field_validator('username')(alphanum)  # (1)!
}

UserModel = create_model(
    'UserModel', username=(str, ...), __validators__=validators
)

user = UserModel(username='scolvin')
print(user)
#> username='scolvin'

try:
    UserModel(username='scolvi%n')
except ValidationError as e:
    print(e)
    """
    1 validation error for UserModel
    username
      Assertion failed, must be alphanumeric [type=assertion_error, input_value='scolvi%n', input_type=str]
    """
```

1. 确保验证器名称不与任何字段名称冲突，因为
   在内部，Pydantic将所有成员收集到一个命名空间中，并模拟使用
   [`types`模块工具](https://docs.python.org/3/library/types.html#dynamic-type-creation)正常创建类的过程。

!!! note "注意"
    要pickle一个动态创建的模型：

    * 模型必须在全局范围内定义
    * 必须提供`__module__`参数

## `RootModel` 和自定义根类型 {#rootmodel-and-custom-root-types}

??? api "API 文档"
    [`pydantic.root_model.RootModel`][pydantic.root_model.RootModel]<br>

Pydantic模型可以通过子类化[`pydantic.RootModel`][pydantic.RootModel]来定义"自定义根类型"。

根类型可以是Pydantic支持的任何类型，并通过`RootModel`的泛型参数指定。
根值可以通过第一个也是唯一的参数传递给模型的`__init__`或[`model_validate`][pydantic.main.BaseModel.model_validate]。

以下是一个示例，说明这是如何工作的：

```python
from pydantic import RootModel

Pets = RootModel[list[str]]
PetsByName = RootModel[dict[str, str]]


print(Pets(['dog', 'cat']))
#> root=['dog', 'cat']
print(Pets(['dog', 'cat']).model_dump_json())
#> ["dog","cat"]
print(Pets.model_validate(['dog', 'cat']))
#> root=['dog', 'cat']
print(Pets.model_json_schema())
"""
{'items': {'type': 'string'}, 'title': 'RootModel[list[str]]', 'type': 'array'}
"""

print(PetsByName({'Otis': 'dog', 'Milo': 'cat'}))
#> root={'Otis': 'dog', 'Milo': 'cat'}
print(PetsByName({'Otis': 'dog', 'Milo': 'cat'}).model_dump_json())
#> {"Otis":"dog","Milo":"cat"}
print(PetsByName.model_validate({'Otis': 'dog', 'Milo': 'cat'}))
#> root={'Otis': 'dog', 'Milo': 'cat'}
```

如果您想直接访问`root`字段中的项目或迭代这些项目，您可以实现
自定义的`__iter__`和`__getitem__`函数，如下例所示。

```python
from pydantic import RootModel


class Pets(RootModel):
    root: list[str]

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]


pets = Pets.model_validate(['dog', 'cat'])
print(pets[0])
#> dog
print([pet for pet in pets])
#> ['dog', 'cat']
```

您也可以直接创建参数化根模型的子类：

```python
from pydantic import RootModel


class Pets(RootModel[list[str]]):
    def describe(self) -> str:
        return f'Pets: {", ".join(self.root)}'


my_pets = Pets.model_validate(['dog', 'cat'])

print(my_pets.describe())
#> Pets: dog, cat
```

## 伪不可变性 {#faux-immutability}

可以通过`model_config['frozen'] = True`将模型配置为不可变。设置此选项后，尝试更改
实例属性的值将引发错误。有关更多详细信息，请参阅[API参考][pydantic.config.ConfigDict.frozen]。

!!! note "注意"
    在Pydantic V1中，此行为通过配置设置`allow_mutation = False`实现。
    此配置标志在Pydantic V2中已弃用，并已被`frozen`替换。

!!! warning "警告"
    在Python中，不可变性不是强制执行的。开发人员有能力修改
    通常被认为是"不可变"的对象，如果他们选择这样做的话。

```python
from pydantic import BaseModel, ConfigDict, ValidationError


class FooBarModel(BaseModel):
    model_config = ConfigDict(frozen=True)

    a: str
    b: dict


foobar = FooBarModel(a='hello', b={'apple': 'pear'})

try:
    foobar.a = 'different'
except ValidationError as e:
    print(e)
    """
    1 validation error for FooBarModel
    a
      Instance is frozen [type=frozen_instance, input_value='different', input_type=str]
    """

print(foobar.a)
#> hello
print(foobar.b)
#> {'apple': 'pear'}
foobar.b['apple'] = 'grape'
print(foobar.b)
#> {'apple': 'grape'}
```

尝试更改`a`导致错误，`a`保持不变。然而，字典`b`是可变的，`foobar`的
不可变性不会阻止`b`被更改。

## 抽象基类

Pydantic模型可以与Python的
[抽象基类](https://docs.python.org/3/library/abc.html) (ABCs)一起使用。

```python
import abc

from pydantic import BaseModel


class FooBarModel(BaseModel, abc.ABC):
    a: str
    b: int

    @abc.abstractmethod
    def my_abstract_method(self):
        pass
```

## 字段排序 {#field-ordering}

字段顺序在以下方面影响模型：

* 字段顺序在模型的[JSON Schema](json_schema.md)中保持不变
* 字段顺序在[验证错误](#error-handling)中保持不变
* 字段顺序在[序列化数据](serialization.md#serializing-data)时保持不变

```python
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    a: int
    b: int = 2
    c: int = 1
    d: int = 0
    e: float


print(Model.model_fields.keys())
#> dict_keys(['a', 'b', 'c', 'd', 'e'])
m = Model(e=2, a=1)
print(m.model_dump())
#> {'a': 1, 'b': 2, 'c': 1, 'd': 0, 'e': 2.0}
try:
    Model(a='x', b='x', c='x', d='x', e='x')
except ValidationError as err:
    error_locations = [e['loc'] for e in err.errors()]

print(error_locations)
#> [('a',), ('b',), ('c',), ('d',), ('e',)]
```

## 自动排除的属性

### 类变量

用[`ClassVar`][typing.ClassVar]注解的属性被Pydantic正确视为类变量，并且不会
成为模型实例的字段：

```python
from typing import ClassVar

from pydantic import BaseModel


class Model(BaseModel):
    x: ClassVar[int] = 1

    y: int = 2


m = Model()
print(m)
#> y=2
print(Model.x)
#> 1
```

### 私有模型属性

??? api "API 文档"
    [`pydantic.fields.PrivateAttr`][pydantic.fields.PrivateAttr]<br>

名称带有前导下划线的属性不被Pydantic视为字段，并且不包含在
模型模式中。相反，这些属性被转换为"私有属性"，在调用
`__init__`、`model_validate`等期间不会被验证甚至设置。

以下是一个使用示例：

```python
from datetime import datetime
from random import randint
from typing import Any

from pydantic import BaseModel, PrivateAttr


class TimeAwareModel(BaseModel):
    _processed_at: datetime = PrivateAttr(default_factory=datetime.now)
    _secret_value: str

    def model_post_init(self, context: Any) -> None:
        # this could also be done with `default_factory`:
        self._secret_value = randint(1, 5)


m = TimeAwareModel()
print(m._processed_at)
#> 2032-01-02 03:04:05.000006
print(m._secret_value)
#> 3
```

私有属性名称必须以下划线开头，以防止与模型字段冲突。但是，双下划线名称
（如`__attr__`）不受支持，并且会从模型定义中完全忽略。

## 模型签名

所有Pydantic模型都将基于其字段生成签名：

```python
import inspect

from pydantic import BaseModel, Field


class FooModel(BaseModel):
    id: int
    name: str = None
    description: str = 'Foo'
    apple: int = Field(alias='pear')


print(inspect.signature(FooModel))
#> (*, id: int, name: str = None, description: str = 'Foo', pear: int) -> None
```

准确的签名对于内省目的和像`FastAPI`或`hypothesis`这样的库很有用。

生成的签名也会尊重自定义的`__init__`函数：

```python
import inspect

from pydantic import BaseModel


class MyModel(BaseModel):
    id: int
    info: str = 'Foo'

    def __init__(self, id: int = 1, *, bar: str, **data) -> None:
        """My custom init!"""
        super().__init__(id=id, bar=bar, **data)


print(inspect.signature(MyModel))
#> (id: int = 1, *, bar: str, info: str = 'Foo') -> None
```

要包含在签名中，字段的别名或名称必须是有效的Python标识符。
Pydantic在生成签名时会优先使用字段的别名而不是其名称，但如果别名
不是有效的Python标识符，则可能使用字段名称。

如果字段的别名和名称都*不是*有效的标识符（这可能是通过`create_model`的异乎寻常使用实现的），
则会添加一个`**data`参数。此外，如果`model_config['extra'] == 'allow'`，
`**data`参数将始终出现在签名中。

## 结构化模式匹配

Pydantic支持模型的结构化模式匹配，这是Python 3.10中由[PEP 636](https://peps.python.org/pep-0636/)引入的。

```python {requires="3.10" lint="skip"}
from pydantic import BaseModel


class Pet(BaseModel):
    name: str
    species: str


a = Pet(name='Bones', species='dog')

match a:
    # match `species` to 'dog', declare and initialize `dog_name`
    case Pet(species='dog', name=dog_name):
        print(f'{dog_name} is a dog')
#> Bones is a dog
    # default case
    case _:
        print('No dog matched')
```

!!! note "注意"
    match-case语句可能看起来像是创建了一个新模型，但不要被误导；
    它只是获取属性并比较它或声明和初始化它的语法糖。

## 属性复制 {#attribute-copies}

在许多情况下，传递给构造函数的参数将被复制以执行验证，并在必要时进行强制类型转换。

在这个例子中，请注意列表的ID在类构造后发生了变化，因为它在验证过程中被复制了：

```python
from pydantic import BaseModel


class C1:
    arr = []

    def __init__(self, in_arr):
        self.arr = in_arr


class C2(BaseModel):
    arr: list[int]


arr_orig = [1, 9, 10, 3]


c1 = C1(arr_orig)
c2 = C2(arr=arr_orig)
print(f'{id(c1.arr) == id(c2.arr)=}')
#> id(c1.arr) == id(c2.arr)=False
```

!!! note "注意"
    在某些情况下，Pydantic不会复制属性，例如传递模型时——我们按原样使用
    模型。您可以通过设置
    [`model_config['revalidate_instances'] = 'always'`](../api/config.md#pydantic.config.ConfigDict)来覆盖此行为。