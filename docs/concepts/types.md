---
description: Pydantic 类型系统详解：学习如何在 Pydantic 中使用内置类型、标准库类型和自定义类型进行数据验证和序列化。涵盖注解模式、类型别名、泛型类、自定义验证器和序列化器等高级技术，帮助您构建强大的数据验证模型。
---

Pydantic 使用类型来定义验证和序列化应该如何执行。
[内置和标准库类型](../api/standard_library_types.md)（例如 [`int`][]、
[`str`][]、[`date`][datetime.date]）可以直接使用。[严格模式](./strict_mode.md)
可以控制，并且可以在它们上应用约束。

除此之外，Pydantic 还提供了额外的类型，要么[直接在库中](../api/types.md)
（例如 [`SecretStr`][pydantic.types.SecretStr]），要么在 [`pydantic-extra-types`](https://github.com/pydantic/pydantic-extra-types)
外部库中。这些类型使用[自定义类型](#custom-types)部分描述的模式实现。
严格模式和约束*不能*应用于它们。

[内置和标准库类型](../api/standard_library_types.md)文档详细介绍了
支持的类型：允许的值、可能的验证约束以及是否可以配置[严格模式](./strict_mode.md)。

另请参阅[转换表](../concepts/conversion_table.md)以获取每个类型允许值的摘要。

本页将介绍如何定义您自己的自定义类型。

## 自定义类型 {#custom-types}

有几种方法可以定义您的自定义类型。

### 使用注解模式 {#using-the-annotated-pattern}

[注解模式](./fields.md#the-annotated-pattern)可用于使类型在代码库中可重用。
例如，创建一个表示正整数的类型：

```python
from typing import Annotated

from pydantic import Field, TypeAdapter, ValidationError

PositiveInt = Annotated[int, Field(gt=0)]  # (1)!

ta = TypeAdapter(PositiveInt)

print(ta.validate_python(1))
#> 1

try:
    ta.validate_python(-1)
except ValidationError as exc:
    print(exc)
    """
    1 validation error for constrained-int
      Input should be greater than 0 [type=greater_than, input_value=-1, input_type=int]
    """
```

1. 请注意，您也可以使用 [annotated-types](https://github.com/annotated-types/annotated-types)
   库中的约束来使其与 Pydantic 无关：

    ```python {test="skip" lint="skip"}
    from annotated_types import Gt

    PositiveInt = Annotated[int, Gt(0)]
    ```

#### 添加验证和序列化 {#adding-validation-and-serialization}

您可以使用 Pydantic 导出的标记为任意类型添加或覆盖验证、序列化和 JSON 模式：

```python
from typing import Annotated

from pydantic import (
    AfterValidator,
    PlainSerializer,
    TypeAdapter,
    WithJsonSchema,
)

TruncatedFloat = Annotated[
    float,
    AfterValidator(lambda x: round(x, 1)),
    PlainSerializer(lambda x: f'{x:.1e}', return_type=str),
    WithJsonSchema({'type': 'string'}, mode='serialization'),
]


ta = TypeAdapter(TruncatedFloat)

input = 1.02345
assert input != 1.0

assert ta.validate_python(input) == 1.0

assert ta.dump_json(input) == b'"1.0e+00"'

assert ta.json_schema(mode='validation') == {'type': 'number'}
assert ta.json_schema(mode='serialization') == {'type': 'string'}
```

#### 泛型

[类型变量][typing.TypeVar] 可以在 [`Annotated`][typing.Annotated] 类型中使用：

```python
from typing import Annotated, TypeVar

from annotated_types import Gt, Len

from pydantic import TypeAdapter, ValidationError

T = TypeVar('T')


ShortList = Annotated[list[T], Len(max_length=4)]


ta = TypeAdapter(ShortList[int])

v = ta.validate_python([1, 2, 3, 4])
assert v == [1, 2, 3, 4]

try:
    ta.validate_python([1, 2, 3, 4, 5])
except ValidationError as exc:
    print(exc)
    """
    1 validation error for list[int]
      List should have at most 4 items after validation, not 5 [type=too_long, input_value=[1, 2, 3, 4, 5], input_type=list]
    """


PositiveList = list[Annotated[T, Gt(0)]]

ta = TypeAdapter(PositiveList[float])

v = ta.validate_python([1.0])
assert type(v[0]) is float


try:
    ta.validate_python([-1.0])
except ValidationError as exc:
    print(exc)
    """
    1 validation error for list[constrained-float]
    0
      Input should be greater than 0 [type=greater_than, input_value=-1.0, input_type=float]
    """
```

### 命名类型别名

上述示例使用了*隐式*类型别名，分配给变量。在运行时，Pydantic
无法知道它被分配给哪个变量名，这可能会带来两个问题：

* 别名的 [JSON Schema](./json_schema.md) 不会转换为
  [定义](https://json-schema.org/understanding-json-schema/structuring#defs)。
  这在您在模型定义中多次使用别名时特别有用。
* 在大多数情况下，[递归类型别名](#named-recursive-types) 将无法工作。

通过利用新的 [`type` 语句](https://typing.readthedocs.io/en/latest/spec/aliases.html#type-statement)
（在 [PEP 695](https://peps.python.org/pep-0695/) 中引入），您可以按如下方式定义别名：

=== "Python 3.9 及以上"

    ```python
    from typing import Annotated

    from annotated_types import Gt
    from typing_extensions import TypeAliasType

    from pydantic import BaseModel

    PositiveIntList = TypeAliasType('PositiveIntList', list[Annotated[int, Gt(0)]])


    class Model(BaseModel):
        x: PositiveIntList
        y: PositiveIntList


    print(Model.model_json_schema())  # (1)!
    """
    {
        '$defs': {
            'PositiveIntList': {
                'items': {'exclusiveMinimum': 0, 'type': 'integer'},
                'type': 'array',
            }
        },
        'properties': {
            'x': {'$ref': '#/$defs/PositiveIntList'},
            'y': {'$ref': '#/$defs/PositiveIntList'},
        },
        'required': ['x', 'y'],
        'title': 'Model',
        'type': 'object',
    }
    """
    ```

    1. 如果 `PositiveIntList` 被定义为隐式类型别名，其定义
       将在 `'x'` 和 `'y'` 中重复。

=== "Python 3.12 及以上（新语法）"

    ```python {requires="3.12" upgrade="skip" lint="skip"}
    from typing import Annotated

    from annotated_types import Gt

    from pydantic import BaseModel

    type PositiveIntList = list[Annotated[int, Gt(0)]]


    class Model(BaseModel):
        x: PositiveIntList
        y: PositiveIntList


    print(Model.model_json_schema())  # (1)!
    """
    {
        '$defs': {
            'PositiveIntList': {
                'items': {'exclusiveMinimum': 0, 'type': 'integer'},
                'type': 'array',
            }
        },
        'properties': {
            'x': {'$ref': '#/$defs/PositiveIntList'},
            'y': {'$ref': '#/$defs/PositiveIntList'},
        },
        'required': ['x', 'y'],
        'title': 'Model',
        'type': 'object',
    }
    """
    ```

    1. 如果 `PositiveIntList` 被定义为隐式类型别名，其定义
       将在 `'x'` 和 `'y'` 中重复。

<!-- markdownlint-disable-next-line no-empty-links -->
[](){#metadata-type-alias-warning}

!!! warning "何时使用命名类型别名"

    虽然（命名的）PEP 695 和隐式类型别名对于静态类型检查器应该是等价的，
    但 Pydantic *不会*理解命名别名中的字段特定元数据。也就是说，诸如
    `alias`、`default`、`deprecated` 之类的元数据*不能*使用：

    === "Python 3.9 及以上"

        ```python {test="skip"}
        from typing import Annotated

        from typing_extensions import TypeAliasType

        from pydantic import BaseModel, Field

        MyAlias = TypeAliasType('MyAlias', Annotated[int, Field(default=1)])


        class Model(BaseModel):
            x: MyAlias  # 这是不允许的
        ```

    === "Python 3.12 及以上（新语法）"

        ```python {requires="3.12" upgrade="skip" lint="skip" test="skip"}
        from typing import Annotated

        from pydantic import BaseModel, Field

        type MyAlias = Annotated[int, Field(default=1)]


        class Model(BaseModel):
            x: MyAlias  # 这是不允许的
        ```

    只允许应用于注解类型本身的元数据
    （例如[验证约束](./fields.md#field-constraints)和 JSON 元数据）。
    尝试支持字段特定元数据需要急切地检查
    类型别名的 [`__value__`][typing.TypeAliasType.__value__]，因此 Pydantic
    将无法将别名存储为 JSON Schema 定义。

!!! note
    与隐式类型别名一样，[类型变量][typing.TypeVar] 也可以在泛型别名中使用：

    === "Python 3.9 及以上"

        ```python
        from typing import Annotated, TypeVar

        from annotated_types import Len
        from typing_extensions import TypeAliasType

        T = TypeVar('T')

        ShortList = TypeAliasType(
            'ShortList', Annotated[list[T], Len(max_length=4)], type_params=(T,)
        )
        ```

    === "Python 3.12 及以上（新语法）"

        ```python {requires="3.12" upgrade="skip" lint="skip"}
        from typing import Annotated, TypeVar

        from annotated_types import Len

        type ShortList[T] = Annotated[list[T], Len(max_length=4)]
        ```

#### 命名递归类型 {#named-recursive-types}

每当您需要定义递归类型别名时，应使用命名类型别名 (1)。
{ .annotate }

1. 由于多种原因，Pydantic 无法支持隐式递归别名。例如，
   它将无法解析跨模块的[前向注解](./forward_annotations.md)。

例如，这里是一个 JSON 类型的示例定义：

=== "Python 3.9 及以上"

    ```python
    from typing import Union

    from typing_extensions import TypeAliasType

    from pydantic import TypeAdapter

    Json = TypeAliasType(
        'Json',
        'Union[dict[str, Json], list[Json], str, int, float, bool, None]',  # (1)!
    )

    ta = TypeAdapter(Json)
    print(ta.json_schema())
    """
    {
        '$defs': {
            'Json': {
                'anyOf': [
                    {
                        'additionalProperties': {'$ref': '#/$defs/Json'},
                        'type': 'object',
                    },
                    {'items': {'$ref': '#/$defs/Json'}, 'type': 'array'},
                    {'type': 'string'},
                    {'type': 'integer'},
                    {'type': 'number'},
                    {'type': 'boolean'},
                    {'type': 'null'},
                ]
            }
        },
        '$ref': '#/$defs/Json',
    }
    """
    ```

    1. 将注解用引号括起来是必要的，因为它会被急切求值
       （并且 `Json` 尚未定义）。

=== "Python 3.12 及以上（新语法）"

    ```python {requires="3.12" upgrade="skip" lint="skip"}
    from pydantic import TypeAdapter

    type Json = dict[str, Json] | list[Json] | str | int | float | bool | None  # (1)!

    ta = TypeAdapter(Json)
    print(ta.json_schema())
    """
    {
        '$defs': {
            'Json': {
                'anyOf': [
                    {
                        'additionalProperties': {'$ref': '#/$defs/Json'},
                        'type': 'object',
                    },
                    {'items': {'$ref': '#/$defs/Json'}, 'type': 'array'},
                    {'type': 'string'},
                    {'type': 'integer'},
                    {'type': 'number'},
                    {'type': 'boolean'},
                    {'type': 'null'},
                ]
            }
        },
        '$ref': '#/$defs/Json',
    }
    """
    ```

    1. 命名类型别名的值是惰性求值的，因此不需要使用前向注解。

!!! tip
    Pydantic 定义了一个 [`JsonValue`][pydantic.types.JsonValue] 类型作为便利工具。

### 使用 `__get_pydantic_core_schema__` 自定义验证 <a name="customizing_validation_with_get_pydantic_core_schema"></a>

要对 Pydantic 处理自定义类的方式进行更广泛的定制，特别是当您可以访问类或可以对其进行子类化时，
您可以实现一个特殊的 `__get_pydantic_core_schema__` 来告诉 Pydantic 如何生成
`pydantic-core` 模式。

虽然 `pydantic` 在内部使用 `pydantic-core` 来处理验证和序列化，但这是 Pydantic V2 的一个新 API，
因此这是未来最有可能进行调整的领域之一，您应该尽量坚持使用内置的
构造，例如 `annotated-types`、`pydantic.Field` 或 `BeforeValidator` 等提供的构造。

您可以在自定义类型上以及打算放入 `Annotated` 的元数据上实现 `__get_pydantic_core_schema__`。
在这两种情况下，API 都是中间件式的，类似于"包装"验证器：您会得到一个 `source_type`（它不一定
与类相同，特别是对于泛型）和一个 `handler`，您可以使用类型调用它来
调用 `Annotated` 中的下一个元数据或调用 Pydantic 的内部模式生成。

最简单的无操作实现是使用给定的类型调用处理程序，然后将其作为结果返回。您也可以
选择在调用处理程序之前修改类型，修改处理程序返回的核心模式，或者根本不调用
处理程序。

#### 作为自定义类型的方法 {#as-a-method-on-a-custom-type}

以下是一个使用 `__get_pydantic_core_schema__` 来自定义其验证方式的类型示例。
这相当于在 Pydantic V1 中实现 `__get_validators__`。

```python
from typing import Any

from pydantic_core import CoreSchema, core_schema

from pydantic import GetCoreSchemaHandler, TypeAdapter


class Username(str):
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        return core_schema.no_info_after_validator_function(cls, handler(str))


ta = TypeAdapter(Username)
res = ta.validate_python('abc')
assert isinstance(res, Username)
assert res == 'abc'
```

有关如何为自定义类型自定义 JSON 模式的更多详细信息，请参阅 [JSON Schema](../concepts/json_schema.md)。

#### 作为注解

通常，您会希望通过不仅仅是泛型类型参数来参数化您的自定义类型（您可以通过类型系统来实现，稍后将讨论）。或者您可能实际上并不关心（或想要）创建子类的实例；您实际上想要原始类型，只是进行一些额外的验证。

例如，如果您要自己实现 `pydantic.AfterValidator`（请参阅[添加验证和序列化](#adding-validation-and-serialization)），您会执行类似以下的操作：

```python
from dataclasses import dataclass
from typing import Annotated, Any, Callable

from pydantic_core import CoreSchema, core_schema

from pydantic import BaseModel, GetCoreSchemaHandler


@dataclass(frozen=True)  # (1)!
class MyAfterValidator:
    func: Callable[[Any], Any]

    def __get_pydantic_core_schema__(
        self, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        return core_schema.no_info_after_validator_function(
            self.func, handler(source_type)
        )


Username = Annotated[str, MyAfterValidator(str.lower)]


class Model(BaseModel):
    name: Username


assert Model(name='ABC').name == 'abc'  # (2)!
```

1. `frozen=True` 规范使 `MyAfterValidator` 可哈希。没有这个，像 `Username | None` 这样的联合类型会引发错误。
2. 请注意，类型检查器不会像上一个示例中那样抱怨将 `'ABC'` 赋值给 `Username`，因为它们不认为 `Username` 是与 `str` 不同的类型。

#### 处理第三方类型

上一节中模式的另一个用例是处理第三方类型。

```python
from typing import Annotated, Any

from pydantic_core import core_schema

from pydantic import (
    BaseModel,
    GetCoreSchemaHandler,
    GetJsonSchemaHandler,
    ValidationError,
)
from pydantic.json_schema import JsonSchemaValue


class ThirdPartyType:
    """
    这旨在表示来自第三方库的类型，该库在设计时没有考虑 Pydantic
    集成，因此没有 `pydantic_core.CoreSchema` 或任何相关内容。
    """

    x: int

    def __init__(self):
        self.x = 0


class _ThirdPartyTypePydanticAnnotation:
    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        """
        我们返回一个 `pydantic_core.CoreSchema`，其行为方式如下：

        * int 将被解析为 `ThirdPartyType` 实例，其中 int 作为 x 属性
        * `ThirdPartyType` 实例将被解析为 `ThirdPartyType` 实例，不做任何更改
        * 其他任何内容都无法通过验证
        * 序列化将始终只返回一个 int
        """

        def validate_from_int(value: int) -> ThirdPartyType:
            result = ThirdPartyType()
            result.x = value
            return result

        from_int_schema = core_schema.chain_schema(
            [
                core_schema.int_schema(),
                core_schema.no_info_plain_validator_function(validate_from_int),
            ]
        )

        return core_schema.json_or_python_schema(
            json_schema=from_int_schema,
            python_schema=core_schema.union_schema(
                [
                    # 首先检查它是否是一个实例，然后再进行进一步的工作
                    core_schema.is_instance_schema(ThirdPartyType),
                    from_int_schema,
                ]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda instance: instance.x
            ),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        # 使用与 `int` 相同的模式
        return handler(core_schema.int_schema())


# 我们现在创建一个 `Annotated` 包装器，我们将用它作为 `BaseModel` 等字段的注解
PydanticThirdPartyType = Annotated[
    ThirdPartyType, _ThirdPartyTypePydanticAnnotation
]


# 创建一个使用此注解作为字段的模型类
class Model(BaseModel):
    third_party_type: PydanticThirdPartyType


# 演示此字段被正确处理，int 被解析为 `ThirdPartyType`，并且
# 这些实例也按预期直接"转储"为 int
m_int = Model(third_party_type=1)
assert isinstance(m_int.third_party_type, ThirdPartyType)
assert m_int.third_party_type.x == 1
assert m_int.model_dump() == {'third_party_type': 1}

# 传入 ThirdPartyType 实例时执行相同的操作
instance = ThirdPartyType()
assert instance.x == 0
instance.x = 10

m_instance = Model(third_party_type=instance)
assert isinstance(m_instance.third_party_type, ThirdPartyType)
assert m_instance.third_party_type.x == 10
assert m_instance.model_dump() == {'third_party_type': 10}

# 演示对于无效输入会按预期引发验证错误
try:
    Model(third_party_type='a')
except ValidationError as e:
    print(e)
    """
    2 validation errors for Model
    third_party_type.is-instance[ThirdPartyType]
      Input should be an instance of ThirdPartyType [type=is_instance_of, input_value='a', input_type=str]
    third_party_type.chain[int,function-plain[validate_from_int()]]
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='a', input_type=str]
    """


assert Model.model_json_schema() == {
    'properties': {
        'third_party_type': {'title': 'Third Party Type', 'type': 'integer'}
    },
    'required': ['third_party_type'],
    'title': 'Model',
    'type': 'object',
}
```

您可以使用这种方法来定义 Pandas 或 Numpy 类型的行为。

#### 使用 `GetPydanticSchema` 减少样板代码

??? api "API 文档"
    [`pydantic.types.GetPydanticSchema`][pydantic.types.GetPydanticSchema]<br>

您可能会注意到，上面我们创建标记类的示例需要大量的样板代码。
对于许多简单的情况，您可以通过使用 `pydantic.GetPydanticSchema` 来大大减少这些代码：

```python
from typing import Annotated

from pydantic_core import core_schema

from pydantic import BaseModel, GetPydanticSchema


class Model(BaseModel):
    y: Annotated[
        str,
        GetPydanticSchema(
            lambda tp, handler: core_schema.no_info_after_validator_function(
                lambda x: x * 2, handler(tp)
            )
        ),
    ]


assert Model(y='ab').y == 'abab'
```

#### 总结

让我们回顾一下：

1. Pydantic 提供了通过 `Annotated` 自定义类型的高级钩子，如 `AfterValidator` 和 `Field`。尽可能使用这些。
2. 在底层，这些使用 `pydantic-core` 来自定义验证，您可以直接使用 `GetPydanticSchema` 或带有 `__get_pydantic_core_schema__` 的标记类来挂钩。
3. 如果您真的想要一个自定义类型，您可以在类型本身上实现 `__get_pydantic_core_schema__`。

### 处理自定义泛型类

!!! warning
    这是一种高级技术，您可能一开始不需要。在大多数情况下，
    您可能使用标准的 Pydantic 模型就足够了。

您可以使用
[泛型类](https://docs.python.org/3/library/typing.html#typing.Generic)作为
字段类型，并使用 `__get_pydantic_core_schema__` 基于"类型参数"（或子类型）
执行自定义验证。

如果您用作子类型的泛型类具有类方法
`__get_pydantic_core_schema__`，您不需要使用
[`arbitrary_types_allowed`][pydantic.config.ConfigDict.arbitrary_types_allowed] 来使其工作。

因为 `source_type` 参数与 `cls` 参数不同，您可以使用 `typing.get_args`（或 `typing_extensions.get_args`）来提取泛型参数。
然后您可以通过调用 `handler.generate_schema` 来为它们生成模式。
请注意，我们不执行类似 `handler(get_args(source_type)[0])` 的操作，因为我们想要为那个泛型参数生成一个不相关的
模式，而不是受当前 `Annotated` 元数据等上下文影响的模式。
这对于自定义类型不太重要，但对于修改模式构建的注解元数据至关重要。

```python
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from pydantic_core import CoreSchema, core_schema
from typing_extensions import get_args, get_origin

from pydantic import (
    BaseModel,
    GetCoreSchemaHandler,
    ValidationError,
    ValidatorFunctionWrapHandler,
)

ItemType = TypeVar('ItemType')


# This is not a pydantic model, it's an arbitrary generic class
@dataclass
class Owner(Generic[ItemType]):
    name: str
    item: ItemType

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        origin = get_origin(source_type)
        if origin is None:  # used as `x: Owner` without params
            origin = source_type
            item_tp = Any
        else:
            item_tp = get_args(source_type)[0]
        # both calling handler(...) and handler.generate_schema(...)
        # would work, but prefer the latter for conceptual and consistency reasons
        item_schema = handler.generate_schema(item_tp)

        def val_item(
            v: Owner[Any], handler: ValidatorFunctionWrapHandler
        ) -> Owner[Any]:
            v.item = handler(v.item)
            return v

        python_schema = core_schema.chain_schema(
            # `chain_schema` means do the following steps in order:
            [
                # Ensure the value is an instance of Owner
                core_schema.is_instance_schema(cls),
                # Use the item_schema to validate `items`
                core_schema.no_info_wrap_validator_function(
                    val_item, item_schema
                ),
            ]
        )

        return core_schema.json_or_python_schema(
            # for JSON accept an object with name and item keys
            json_schema=core_schema.chain_schema(
                [
                    core_schema.typed_dict_schema(
                        {
                            'name': core_schema.typed_dict_field(
                                core_schema.str_schema()
                            ),
                            'item': core_schema.typed_dict_field(item_schema),
                        }
                    ),
                    # after validating the json data convert it to python
                    core_schema.no_info_before_validator_function(
                        lambda data: Owner(
                            name=data['name'], item=data['item']
                        ),
                        # note that we reuse the same schema here as below
                        python_schema,
                    ),
                ]
            ),
            python_schema=python_schema,
        )


class Car(BaseModel):
    color: str


class House(BaseModel):
    rooms: int


class Model(BaseModel):
    car_owner: Owner[Car]
    home_owner: Owner[House]


model = Model(
    car_owner=Owner(name='John', item=Car(color='black')),
    home_owner=Owner(name='James', item=House(rooms=3)),
)
print(model)
"""
car_owner=Owner(name='John', item=Car(color='black')) home_owner=Owner(name='James', item=House(rooms=3))
"""

try:
    # If the values of the sub-types are invalid, we get an error
    Model(
        car_owner=Owner(name='John', item=House(rooms=3)),
        home_owner=Owner(name='James', item=Car(color='black')),
    )
except ValidationError as e:
    print(e)
    """
    2 validation errors for Model
    wine
      Input should be a valid number, unable to parse string as a number [type=float_parsing, input_value='Kinda good', input_type=str]
    cheese
      Input should be a valid boolean, unable to interpret input [type=bool_parsing, input_value='yeah', input_type=str]
    """

# Similarly with JSON
model = Model.model_validate_json(
    '{"car_owner":{"name":"John","item":{"color":"black"}},"home_owner":{"name":"James","item":{"rooms":3}}}'
)
print(model)
"""
car_owner=Owner(name='John', item=Car(color='black')) home_owner=Owner(name='James', item=House(rooms=3))
"""

try:
    Model.model_validate_json(
        '{"car_owner":{"name":"John","item":{"rooms":3}},"home_owner":{"name":"James","item":{"color":"black"}}}'
    )
except ValidationError as e:
    print(e)
    """
    2 validation errors for Model
    car_owner.item.color
      Field required [type=missing, input_value={'rooms': 3}, input_type=dict]
    home_owner.item.rooms
      Field required [type=missing, input_value={'color': 'black'}, input_type=dict]
    """
```

#### 泛型容器

同样的想法可以应用于创建泛型容器类型，比如自定义的 `Sequence` 类型：

```python
from collections.abc import Sequence
from typing import Any, TypeVar

from pydantic_core import ValidationError, core_schema
from typing_extensions import get_args

from pydantic import BaseModel, GetCoreSchemaHandler

T = TypeVar('T')


class MySequence(Sequence[T]):
    def __init__(self, v: Sequence[T]):
        self.v = v

    def __getitem__(self, i):
        return self.v[i]

    def __len__(self):
        return len(self.v)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        instance_schema = core_schema.is_instance_schema(cls)

        args = get_args(source)
        if args:
            # replace the type and rely on Pydantic to generate the right schema
            # for `Sequence`
            sequence_t_schema = handler.generate_schema(Sequence[args[0]])
        else:
            sequence_t_schema = handler.generate_schema(Sequence)

        non_instance_schema = core_schema.no_info_after_validator_function(
            MySequence, sequence_t_schema
        )
        return core_schema.union_schema([instance_schema, non_instance_schema])


class M(BaseModel):
    model_config = dict(validate_default=True)

    s1: MySequence = [3]


m = M()
print(m)
#> s1=<__main__.MySequence object at 0x0123456789ab>
print(m.s1.v)
#> [3]


class M(BaseModel):
    s1: MySequence[int]


M(s1=[1])
try:
    M(s1=['a'])
except ValidationError as exc:
    print(exc)
    """
    2 validation errors for M
    s1.is-instance[MySequence]
      Input should be an instance of MySequence [type=is_instance_of, input_value=['a'], input_type=list]
    s1.function-after[MySequence(), json-or-python[json=list[int],python=chain[is-instance[Sequence],function-wrap[sequence_validator()]]]].0
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='a', input_type=str]
    """
```

### 访问字段名称

!!! note
    这在 Pydantic V2 到 V2.3 中是不可能的，它在 Pydantic V2.4 中[重新添加](https://github.com/pydantic/pydantic/pull/7542)。

从 Pydantic V2.4 开始，您可以通过 `__get_pydantic_core_schema__` 中的 `handler.field_name` 访问字段名称，
从而设置可以从 `info.field_name` 获取的字段名称。

```python
from typing import Any

from pydantic_core import core_schema

from pydantic import BaseModel, GetCoreSchemaHandler, ValidationInfo


class CustomType:
    """Custom type that stores the field it was used in."""

    def __init__(self, value: int, field_name: str):
        self.value = value
        self.field_name = field_name

    def __repr__(self):
        return f'CustomType<{self.value} {self.field_name!r}>'

    @classmethod
    def validate(cls, value: int, info: ValidationInfo):
        return cls(value, info.field_name)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.with_info_after_validator_function(
            cls.validate, handler(int)
        )


class MyModel(BaseModel):
    my_field: CustomType


m = MyModel(my_field=1)
print(m.my_field)
#> CustomType<1 'my_field'>
```

您也可以从与 `Annotated` 一起使用的标记中访问 `field_name`，例如 [`AfterValidator`][pydantic.functional_validators.AfterValidator]。

```python
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ValidationInfo


def my_validators(value: int, info: ValidationInfo):
    return f'<{value} {info.field_name!r}>'


class MyModel(BaseModel):
    my_field: Annotated[int, AfterValidator(my_validators)]


m = MyModel(my_field=1)
print(m.my_field)
#> <1 'my_field'>
```