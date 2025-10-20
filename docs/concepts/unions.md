---
description: Pydantic 联合类型验证指南：详解三种验证模式（从左到右、智能模式和区分联合类型），包括使用 str 区分器和可调用 Discriminator 的高级技巧，以及如何处理嵌套区分联合类型和验证错误。掌握 Union 类型验证的最佳实践，提升数据验证效率和准确性。
---

联合类型（Unions）与Pydantic验证的所有其他类型有着根本性的不同 - 不是要求所有字段/项/值都有效，联合类型只需要其中一个成员有效即可。

这导致在如何验证联合类型方面存在一些细微差别：

* 应该针对联合类型的哪个成员（或多个成员）验证数据，以及按什么顺序？
* 验证失败时应引发哪些错误？

验证联合类型感觉像是为验证过程添加了另一个正交维度。

为了解决这些问题，Pydantic支持三种基本的联合类型验证方法：

1. [从左到右模式](#left-to-right-mode) - 最简单的方法，按顺序尝试联合类型的每个成员，返回第一个匹配项
2. [智能模式](#smart-mode) - 类似于"从左到右模式"，按顺序尝试成员；但是，验证会继续寻找更好的匹配项，这是大多数联合类型验证的默认模式
3. [区分联合类型](#discriminated-unions) - 基于区分器，只尝试联合类型的一个成员

!!! tip

    一般来说，我们推荐使用[区分联合类型](#discriminated-unions)。它们比未标记的联合类型既更高效又更可预测，因为它们允许您控制要验证联合类型的哪个成员。

    对于复杂情况，如果您使用未标记的联合类型，建议使用 `union_mode='left_to_right'`，如果您需要对联合类型成员的验证尝试顺序有保证。

    如果您需要极其专业化的行为，可以使用[自定义验证器](../concepts/validators.md#field-validators)。

## 联合类型模式 {#union-modes}

### 从左到右模式 {#left-to-right-mode}

!!! note
    由于此模式经常导致意外的验证结果，它不是Pydantic >=2中的默认模式，而是 `union_mode='smart'` 是默认模式。

使用这种方法，验证会按照联合类型成员定义的顺序依次尝试每个成员，第一个成功的验证被接受为输入。

如果所有成员的验证都失败，验证错误将包含联合类型所有成员的错误。

`union_mode='left_to_right'` 必须作为 [`Field`](../concepts/fields.md) 参数设置在您想要使用它的联合类型字段上。

```python {title="Union with left to right mode"}
from typing import Union

from pydantic import BaseModel, Field, ValidationError


class User(BaseModel):
    id: Union[str, int] = Field(union_mode='left_to_right')


print(User(id=123))
#> id=123
print(User(id='hello'))
#> id='hello'

try:
    User(id=[])
except ValidationError as e:
    print(e)
    """
    2 validation errors for User
    id.str
      Input should be a valid string [type=string_type, input_value=[], input_type=list]
    id.int
      Input should be a valid integer [type=int_type, input_value=[], input_type=list]
    """
```

在这种情况下，成员的顺序非常重要，正如通过调整上述示例所展示的：

```python {title="Union with left to right - unexpected results"}
from typing import Union

from pydantic import BaseModel, Field


class User(BaseModel):
    id: Union[int, str] = Field(union_mode='left_to_right')


print(User(id=123))  # (1)
#> id=123
print(User(id='456'))  # (2)
#> id=456
```

1. 正如预期的那样，输入针对 `int` 成员进行验证，结果符合预期。
2. 我们处于宽松模式，数字字符串 `'123'` 作为联合类型第一个成员 `int` 的输入是有效的。
   由于它首先被尝试，我们得到了令人惊讶的结果：`id` 是 `int` 而不是 `str`。

### 智能模式 {#smart-mode}

由于 `union_mode='left_to_right'` 可能产生令人惊讶的结果，在Pydantic >=2中，`Union` 验证的默认模式是 `union_mode='smart'`。

在这种模式下，pydantic尝试从联合类型成员中选择与输入最匹配的项。确切的算法可能会在Pydantic次要版本之间更改，以允许在性能和准确性方面进行改进。

!!! note

    我们保留在未来版本的Pydantic中调整内部 `smart` 匹配算法的权利。如果您依赖非常特定的匹配行为，建议使用 `union_mode='left_to_right'` 或[区分联合类型](#discriminated-unions)。

??? info "智能模式算法"

    智能模式算法使用两个指标来确定与输入的最佳匹配：

    1. 有效字段设置的数量（与模型、数据类和类型化字典相关）
    2. 匹配的精确度（与所有类型相关）

    #### 有效字段设置的数量

    !!! note
        此指标在Pydantic v2.8.0中引入。在此版本之前，仅使用精确度来确定最佳匹配。

    此指标目前仅与模型、数据类和类型化字典相关。

    有效字段设置的数量越多，匹配越好。嵌套模型上设置的字段数量也会被考虑在内。
    这些计数会冒泡到顶级联合类型，其中具有最高计数的联合类型成员被认为是最佳匹配。

    对于此指标相关的数据类型，我们优先考虑此计数而不是精确度。对于所有其他类型，我们仅使用精确度。

    #### 精确度

    对于 `exactness`，Pydantic将联合类型成员的匹配评分到以下三个组之一（从最高分到最低分）：

    * 精确类型匹配，例如 `int` 输入到 `float | int` 联合类型验证是 `int` 成员的精确类型匹配
    * 验证将在[`strict`模式](../concepts/strict_mode.md)中成功
    * 验证将在宽松模式中成功

    产生最高精确度得分的联合类型匹配将被认为是最佳匹配。

    在智能模式下，采取以下步骤来尝试选择与输入的最佳匹配：

    === "`BaseModel`, `dataclass`, and `TypedDict`"

        1. 从左到右尝试联合类型成员，任何成功的匹配都会根据上述三个精确度类别进行评分，同时统计有效字段设置的数量。
        2. 评估所有成员后，返回具有最高"有效字段设置"计数的成员。
        3. 如果最高"有效字段设置"计数出现平局，则使用精确度得分作为决胜局，返回具有最高精确度得分的成员。
        4. 如果所有成员的验证都失败，则返回所有错误。

    === "所有其他数据类型"

        1. 从左到右尝试联合类型成员，任何成功的匹配都会根据上述三个精确度类别进行评分。
            * 如果验证以精确类型匹配成功，则立即返回该成员，并且不会尝试后续成员。
        2. 如果至少有一个成员作为"strict"匹配成功，则返回最左边的"strict"匹配。
        3. 如果至少有一个成员在"lax"模式下成功，则返回最左边的匹配。
        4. 所有成员的验证都失败，返回所有错误。

```python
from typing import Union
from uuid import UUID

from pydantic import BaseModel


class User(BaseModel):
    id: Union[int, str, UUID]
    name: str


user_01 = User(id=123, name='John Doe')
print(user_01)
#> id=123 name='John Doe'
print(user_01.id)
#> 123
user_02 = User(id='1234', name='John Doe')
print(user_02)
#> id='1234' name='John Doe'
print(user_02.id)
#> 1234
user_03_uuid = UUID('cf57432e-809e-4353-adbd-9d5c0d733868')
user_03 = User(id=user_03_uuid, name='John Doe')
print(user_03)
#> id=UUID('cf57432e-809e-4353-adbd-9d5c0d733868') name='John Doe'
print(user_03.id)
#> cf57432e-809e-4353-adbd-9d5c0d733868
print(user_03_uuid.int)
#> 275603287559914445491632874575877060712
```

## 区分联合类型

**区分联合类型有时被称为"标记联合类型"。**

我们可以使用区分联合类型来更有效地验证 `Union` 类型，通过选择要验证的联合类型成员。

这使得验证更加高效，并且在验证失败时避免了错误扩散。

向联合类型添加区分器还意味着生成的JSON模式实现了[相关的OpenAPI规范](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.0.md#discriminator-object)。

### 使用 `str` 区分器的区分联合类型

通常，在具有多个模型的 `Union` 情况下，
联合类型的所有成员都有一个共同的字段，可以用来区分
数据应该针对哪个联合类型情况进行验证；这在
[OpenAPI](https://swagger.io/docs/specification/data-models/inheritance-and-polymorphism/)中被称为"区分器"。

要基于该信息验证模型，您可以在每个模型中设置相同的字段 - 我们称之为 `my_discriminator` -
并为其设置一个区分值，该值是一个（或多个）`Literal` 值。
对于您的 `Union`，您可以在其值中设置区分器：`Field(discriminator='my_discriminator')`。

```python
from typing import Literal, Union

from pydantic import BaseModel, Field, ValidationError


class Cat(BaseModel):
    pet_type: Literal['cat']
    meows: int


class Dog(BaseModel):
    pet_type: Literal['dog']
    barks: float


class Lizard(BaseModel):
    pet_type: Literal['reptile', 'lizard']
    scales: bool


class Model(BaseModel):
    pet: Union[Cat, Dog, Lizard] = Field(discriminator='pet_type')
    n: int


print(Model(pet={'pet_type': 'dog', 'barks': 3.14}, n=1))
#> pet=Dog(pet_type='dog', barks=3.14) n=1
try:
    Model(pet={'pet_type': 'dog'}, n=1)
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    pet.dog.barks
      Field required [type=missing, input_value={'pet_type': 'dog'}, input_type=dict]
    """
```

### 使用可调用 `Discriminator` 的区分联合类型 {#discriminated-unions}

??? api "API 文档"
    [`pydantic.types.Discriminator`][pydantic.types.Discriminator]<br>

在具有多个模型的 `Union` 情况下，有时在所有模型中没有统一的字段
可以作为区分器使用。
这是可调用 `Discriminator` 的完美用例。

!!! tip
    当您设计可调用区分器时，请记住您可能需要同时考虑
    `dict` 和模型类型的输入。这种模式类似于 `mode='before'` 验证器，
    您需要预测各种形式的输入。

    但是等等！您可能会问，我只期望传入 `dict` 类型，为什么需要考虑模型？
    Pydantic也使用可调用区分器进行序列化，此时您的可调用函数的输入
    很可能是模型实例。

    在以下示例中，您将看到可调用区分器被设计为处理 `dict` 和模型输入。
    如果您不遵循这种做法，很可能在最好的情况下会在序列化期间收到警告，
    而在最坏的情况下会在验证期间出现运行时错误。

```python
from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, Discriminator, Tag


class Pie(BaseModel):
    time_to_cook: int
    num_ingredients: int


class ApplePie(Pie):
    fruit: Literal['apple'] = 'apple'


class PumpkinPie(Pie):
    filling: Literal['pumpkin'] = 'pumpkin'


def get_discriminator_value(v: Any) -> str:
    if isinstance(v, dict):
        return v.get('fruit', v.get('filling'))
    return getattr(v, 'fruit', getattr(v, 'filling', None))


class ThanksgivingDinner(BaseModel):
    dessert: Annotated[
        Union[
            Annotated[ApplePie, Tag('apple')],
            Annotated[PumpkinPie, Tag('pumpkin')],
        ],
        Discriminator(get_discriminator_value),
    ]


apple_variation = ThanksgivingDinner.model_validate(
    {'dessert': {'fruit': 'apple', 'time_to_cook': 60, 'num_ingredients': 8}}
)
print(repr(apple_variation))
"""
ThanksgivingDinner(dessert=ApplePie(time_to_cook=60, num_ingredients=8, fruit='apple'))
"""

pumpkin_variation = ThanksgivingDinner.model_validate(
    {
        'dessert': {
            'filling': 'pumpkin',
            'time_to_cook': 40,
            'num_ingredients': 6,
        }
    }
)
print(repr(pumpkin_variation))
"""
ThanksgivingDinner(dessert=PumpkinPie(time_to_cook=40, num_ingredients=6, filling='pumpkin'))
"""
```

`Discriminator` 也可以用于验证包含模型和基本类型组合的 `Union` 类型。

例如：

```python
from typing import Annotated, Any, Union

from pydantic import BaseModel, Discriminator, Tag, ValidationError


def model_x_discriminator(v: Any) -> str:
    if isinstance(v, int):
        return 'int'
    if isinstance(v, (dict, BaseModel)):
        return 'model'
    else:
        # return None if the discriminator value isn't found
        return None


class SpecialValue(BaseModel):
    value: int


class DiscriminatedModel(BaseModel):
    value: Annotated[
        Union[
            Annotated[int, Tag('int')],
            Annotated['SpecialValue', Tag('model')],
        ],
        Discriminator(model_x_discriminator),
    ]


model_data = {'value': {'value': 1}}
m = DiscriminatedModel.model_validate(model_data)
print(m)
#> value=SpecialValue(value=1)

int_data = {'value': 123}
m = DiscriminatedModel.model_validate(int_data)
print(m)
#> value=123

try:
    DiscriminatedModel.model_validate({'value': 'not an int or a model'})
except ValidationError as e:
    print(e)  # (1)!
    """
    1 validation error for DiscriminatedModel
    value
      Unable to extract tag using discriminator model_x_discriminator() [type=union_tag_not_found, input_value='not an int or a model', input_type=str]
    """
```

1. 请注意，如果未找到区分器值，可调用区分器函数返回 `None`。
   当返回 `None` 时，会引发此 `union_tag_not_found` 错误。

!!! note
    使用[注解模式](./fields.md#the-annotated-pattern)可以方便地重新组织
    `Union` 和 `discriminator` 信息。有关更多详细信息，请参阅下一个示例。

    有几种方法可以为字段设置区分器，语法略有不同。

    对于 `str` 区分器：

    ```python {lint="skip" test="skip"}
    some_field: Union[...] = Field(discriminator='my_discriminator')
    some_field: Annotated[Union[...], Field(discriminator='my_discriminator')]
    ```

    对于可调用 `Discriminator`：

    ```python {lint="skip" test="skip"}
    some_field: Union[...] = Field(discriminator=Discriminator(...))
    some_field: Annotated[Union[...], Discriminator(...)]
    some_field: Annotated[Union[...], Field(discriminator=Discriminator(...))]
    ```

!!! warning
    区分联合类型不能仅与单个变体一起使用，例如 `Union[Cat]`。

    Python在解释时将 `Union[T]` 更改为 `T`，因此 `pydantic` 不可能
    区分 `Union[T]` 的字段与 `T` 的字段。

### 嵌套区分联合类型

一个字段只能设置一个区分器，但有时您想要组合多个区分器。
您可以通过创建嵌套的 `Annotated` 类型来实现，例如：

```python
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field, ValidationError


class BlackCat(BaseModel):
    pet_type: Literal['cat']
    color: Literal['black']
    black_name: str


class WhiteCat(BaseModel):
    pet_type: Literal['cat']
    color: Literal['white']
    white_name: str


Cat = Annotated[Union[BlackCat, WhiteCat], Field(discriminator='color')]


class Dog(BaseModel):
    pet_type: Literal['dog']
    name: str


Pet = Annotated[Union[Cat, Dog], Field(discriminator='pet_type')]


class Model(BaseModel):
    pet: Pet
    n: int


m = Model(pet={'pet_type': 'cat', 'color': 'black', 'black_name': 'felix'}, n=1)
print(m)
#> pet=BlackCat(pet_type='cat', color='black', black_name='felix') n=1
try:
    Model(pet={'pet_type': 'cat', 'color': 'red'}, n='1')
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    pet.cat
      Input tag 'red' found using 'color' does not match any of the expected tags: 'black', 'white' [type=union_tag_invalid, input_value={'pet_type': 'cat', 'color': 'red'}, input_type=dict]
    """
try:
    Model(pet={'pet_type': 'cat', 'color': 'black'}, n='1')
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    pet.cat.black.black_name
      Field required [type=missing, input_value={'pet_type': 'cat', 'color': 'black'}, input_type=dict]
    """
```

!!! tip
    如果您想针对联合类型验证数据，并且仅针对联合类型，您可以使用pydantic的[`TypeAdapter`](../concepts/type_adapter.md)构造，而不是继承标准的 `BaseModel`。

    在前一个示例的上下文中，我们有：

    ```python {lint="skip" test="skip"}
    type_adapter = TypeAdapter(Pet)

    pet = type_adapter.validate_python(
        {'pet_type': 'cat', 'color': 'black', 'black_name': 'felix'}
    )
    print(repr(pet))
    #> BlackCat(pet_type='cat', color='black', black_name='felix')
    ```

## 联合类型验证错误

当 `Union` 验证失败时，错误消息可能非常冗长，因为它们会为
联合类型中的每种情况产生验证错误。
在处理递归模型时尤其明显，其中错误原因可能在每个递归级别生成。
区分联合类型在这种情况下有助于简化错误消息，因为验证错误仅针对
具有匹配区分器值的情况产生。

您还可以通过将这些规范作为参数传递给 `Discriminator` 构造函数来自定义
`Discriminator` 的错误类型、消息和上下文，如下例所示。

```python
from typing import Annotated, Union

from pydantic import BaseModel, Discriminator, Tag, ValidationError


# Errors are quite verbose with a normal Union:
class Model(BaseModel):
    x: Union[str, 'Model']


try:
    Model.model_validate({'x': {'x': {'x': 1}}})
except ValidationError as e:
    print(e)
    """
    4 validation errors for Model
    x.str
      Input should be a valid string [type=string_type, input_value={'x': {'x': 1}}, input_type=dict]
    x.Model.x.str
      Input should be a valid string [type=string_type, input_value={'x': 1}, input_type=dict]
    x.Model.x.Model.x.str
      Input should be a valid string [type=string_type, input_value=1, input_type=int]
    x.Model.x.Model.x.Model
      Input should be a valid dictionary or instance of Model [type=model_type, input_value=1, input_type=int]
    """

try:
    Model.model_validate({'x': {'x': {'x': {}}}})
except ValidationError as e:
    print(e)
    """
    4 validation errors for Model
    x.str
      Input should be a valid string [type=string_type, input_value={'x': {'x': {}}}, input_type=dict]
    x.Model.x.str
      Input should be a valid string [type=string_type, input_value={'x': {}}, input_type=dict]
    x.Model.x.Model.x.str
      Input should be a valid string [type=string_type, input_value={}, input_type=dict]
    x.Model.x.Model.x.Model.x
      Field required [type=missing, input_value={}, input_type=dict]
    """


# Errors are much simpler with a discriminated union:
def model_x_discriminator(v):
    if isinstance(v, str):
        return 'str'
    if isinstance(v, (dict, BaseModel)):
        return 'model'


class DiscriminatedModel(BaseModel):
    x: Annotated[
        Union[
            Annotated[str, Tag('str')],
            Annotated['DiscriminatedModel', Tag('model')],
        ],
        Discriminator(
            model_x_discriminator,
            custom_error_type='invalid_union_member',  # (1)!
            custom_error_message='Invalid union member',  # (2)!
            custom_error_context={'discriminator': 'str_or_model'},  # (3)!
        ),
    ]


try:
    DiscriminatedModel.model_validate({'x': {'x': {'x': 1}}})
except ValidationError as e:
    print(e)
    """
    1 validation error for DiscriminatedModel
    x.model.x.model.x
      Invalid union member [type=invalid_union_member, input_value=1, input_type=int]
    """

try:
    DiscriminatedModel.model_validate({'x': {'x': {'x': {}}}})
except ValidationError as e:
    print(e)
    """
    1 validation error for DiscriminatedModel
    x.model.x.model.x.model.x
      Field required [type=missing, input_value={}, input_type=dict]
    """

# The data is still handled properly when valid:
data = {'x': {'x': {'x': 'a'}}}
m = DiscriminatedModel.model_validate(data)
print(m.model_dump())
#> {'x': {'x': {'x': 'a'}}}
```

1. `custom_error_type` 是验证失败时引发的 `ValidationError` 的 `type` 属性。
2. `custom_error_message` 是验证失败时引发的 `ValidationError` 的 `msg` 属性。
3. `custom_error_context` 是验证失败时引发的 `ValidationError` 的 `ctx` 属性。

您还可以通过使用 [`Tag`][pydantic.types.Tag] 标记每种情况来简化错误消息。
当您有像此示例中的复杂类型时，这尤其有用：

```python
from typing import Annotated, Union

from pydantic import AfterValidator, Tag, TypeAdapter, ValidationError

DoubledList = Annotated[list[int], AfterValidator(lambda x: x * 2)]
StringsMap = dict[str, str]


# 如果不为每个联合类型情况使用 `Tag`，错误信息看起来就不那么美观
adapter = TypeAdapter(Union[DoubledList, StringsMap])

try:
    adapter.validate_python(['a'])
except ValidationError as exc_info:
    print(exc_info)
    """
    2 validation errors for union[function-after[<lambda>(), list[int]],dict[str,str]]
    function-after[<lambda>(), list[int]].0
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='a', input_type=str]
    dict[str,str]
      Input should be a valid dictionary [type=dict_type, input_value=['a'], input_type=list]
    """

tag_adapter = TypeAdapter(
    Union[
        Annotated[DoubledList, Tag('DoubledList')],
        Annotated[StringsMap, Tag('StringsMap')],
    ]
)

try:
    tag_adapter.validate_python(['a'])
except ValidationError as exc_info:
    print(exc_info)
    """
    2 validation errors for union[DoubledList,StringsMap]
    DoubledList.0
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='a', input_type=str]
    StringsMap
      Input should be a valid dictionary [type=dict_type, input_value=['a'], input_type=list]
    """
```