---
description: Pydantic 实验特性文档 - 介绍 Pipeline API、部分验证、可调用参数验证和 MISSING 标记等前沿功能，这些实验性 API 提供更类型安全的数据验证方式，支持不完整 JSON 解析和高级参数验证，为 Python 数据验证提供创新解决方案。
---

# 实验特性

在本节中，您将找到 Pydantic 中新的实验特性的文档。这些特性可能会发生变化或被移除，在将它们作为 Pydantic 的永久部分之前，我们正在寻求反馈和建议。

有关实验特性的更多信息，请参阅我们的[版本策略](../version-policy.md#experimental-features)。

## 反馈 {#feedback}

我们欢迎对实验特性的反馈！请在 [Pydantic GitHub 仓库](https://github.com/pydantic/pydantic/issues/new/choose) 上创建一个 issue 来分享您的想法、请求或建议。

我们也鼓励您阅读现有的反馈并在现有 issue 中添加您的想法。

## Pipeline API

Pydantic v2.8.0 引入了一个实验性的 "pipeline" API，允许以比现有 API 更类型安全的方式组合解析（验证）、约束和转换。此 API 可能会发生变化或被移除，在将其作为 Pydantic 的永久部分之前，我们正在寻求反馈和建议。

??? api "API 文档"
    [`pydantic.experimental.pipeline`][pydantic.experimental.pipeline]<br>

通常，pipeline API 用于定义在验证期间应用于传入数据的一系列步骤。Pipeline API 被设计为比现有的 Pydantic API 更类型安全和可组合。

管道中的每个步骤可以是：

* 验证步骤：对提供的类型运行 pydantic 验证
* 转换步骤：修改数据
* 约束步骤：根据条件检查数据
* 断言步骤：根据条件检查数据，如果返回 `False` 则引发错误

<!-- TODO: 在实验阶段巩固 API 后添加更多文档 -->

请注意，以下示例试图以复杂性为代价做到详尽：如果您发现自己在类型注解中编写这么多转换，您可能需要考虑使用 `UserIn` 和 `UserOut` 模型（如下例所示）或类似的模式，通过惯用的普通 Python 代码进行转换。
这些 API 适用于代码节省显著且增加的复杂性相对较小的情况。

```python
from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel
from pydantic.experimental.pipeline import validate_as


class User(BaseModel):
    name: Annotated[str, validate_as(str).str_lower()]  # (1)!
    age: Annotated[int, validate_as(int).gt(0)]  # (2)!
    username: Annotated[str, validate_as(str).str_pattern(r'[a-z]+')]  # (3)!
    password: Annotated[
        str,
        validate_as(str)
        .transform(str.lower)
        .predicate(lambda x: x != 'password'),  # (4)!
    ]
    favorite_number: Annotated[  # (5)!
        int,
        (validate_as(int) | validate_as(str).str_strip().validate_as(int)).gt(
            0
        ),
    ]
    friends: Annotated[list[User], validate_as(...).len(0, 100)]  # (6)!
    bio: Annotated[
        datetime,
        validate_as(int)
        .transform(lambda x: x / 1_000_000)
        .validate_as(...),  # (8)!
    ]
```

1. 将字符串转换为小写。
2. 约束整数大于零。
3. 约束字符串匹配正则表达式模式。
4. 您也可以使用较低级别的转换、约束和断言方法。
5. 使用 `|` 或 `&` 运算符组合步骤（类似于逻辑 OR 或 AND）。
6. 使用 `Ellipsis`、`...` 作为第一个位置参数调用 `validate_as(...)` 意味着 `validate_as(<字段类型>)`。使用 `validate_as(Any)` 接受任何类型。
7. 您可以在其他步骤之前或之后调用 `validate_as()` 来进行预处理或后处理。

### 从 `BeforeValidator`、`AfterValidator` 和 `WrapValidator` 映射

`validate_as` 方法是定义 `BeforeValidator`、`AfterValidator` 和 `WrapValidator` 的更类型安全的方式：

```python
from typing import Annotated

from pydantic.experimental.pipeline import transform, validate_as

# BeforeValidator
Annotated[int, validate_as(str).str_strip().validate_as(...)]  # (1)!
# AfterValidator
Annotated[int, transform(lambda x: x * 2)]  # (2)!
# WrapValidator
Annotated[
    int,
    validate_as(str)
    .str_strip()
    .validate_as(...)
    .transform(lambda x: x * 2),  # (3)!
]
```

1. 在将字符串解析为整数之前去除空格。
2. 在解析整数后将其乘以 2。
3. 去除字符串的空格，将其验证为整数，然后乘以 2。

### 替代模式

根据场景有许多替代模式可以使用。
作为一个例子，考虑上面提到的 `UserIn` 和 `UserOut` 模式：

```python
from __future__ import annotations

from pydantic import BaseModel


class UserIn(BaseModel):
    favorite_number: int | str


class UserOut(BaseModel):
    favorite_number: int


def my_api(user: UserIn) -> UserOut:
    favorite_number = user.favorite_number
    if isinstance(favorite_number, str):
        favorite_number = int(user.favorite_number.strip())

    return UserOut(favorite_number=favorite_number)


assert my_api(UserIn(favorite_number=' 1 ')).favorite_number == 1
```

这个示例使用普通的惯用 Python 代码，可能比上面的示例更容易理解、类型检查等。
您选择的方法应该真正取决于您的用例。
您需要比较冗长性、性能、向用户返回有意义的错误的难易程度等，以选择正确的模式。
请注意不要仅仅因为可以使用就滥用像 pipeline API 这样的高级模式。

## 部分验证

Pydantic v2.10.0 引入了对"部分验证"的实验性支持。

这允许您验证不完整的 JSON 字符串，或表示不完整输入数据的 Python 对象。

部分验证在处理 LLM 的输出时特别有用，模型会流式传输结构化响应，您可能希望在仍在接收数据时开始验证流（例如，向用户显示部分数据）。

!!! warning
    部分验证是一个实验性特性，可能会在未来的 Pydantic 版本中发生变化。当前的实现应被视为概念验证，并且有一些[限制](#limitations-of-partial-validation)。

部分验证可以在使用 `TypeAdapter` 的三种验证方法时启用：[`TypeAdapter.validate_json()`][pydantic.TypeAdapter.validate_json]、[`TypeAdapter.validate_python()`][pydantic.TypeAdapter.validate_python] 和 [`TypeAdapter.validate_strings()`][pydantic.TypeAdapter.validate_strings]。这允许您解析和验证不完整的 JSON，还可以验证通过解析任何格式的不完整数据创建的 Python 对象。

可以向这些方法传递 `experimental_allow_partial` 标志来启用部分验证。
它可以采用以下值（默认为 `False`）：

* `False` 或 `'off'` - 禁用部分验证
* `True` 或 `'on'` - 启用部分验证，但不支持尾随字符串
* `'trailing-strings'` - 启用部分验证并支持尾随字符串

!!! info "`'trailing-strings'` 模式"
    `'trailing-strings'` 模式允许将部分 JSON 末尾的不完整尾随字符串包含在输出中。
    例如，如果您针对以下模型进行验证：

    ```python
    from typing import TypedDict


    class Model(TypedDict):
        a: str
        b: str
    ```

    那么以下 JSON 输入将被视为有效，尽管末尾有不完整的字符串：

    ```json
    '{"a": "hello", "b": "wor'
    ```

    并将验证为：

    ```python {test="skip" lint="skip"}
    {'a': 'hello', 'b': 'wor'}
    ```

`experiment_allow_partial` 实际应用示例：

```python
from typing import Annotated

from annotated_types import MinLen
from typing_extensions import NotRequired, TypedDict

from pydantic import TypeAdapter


class Foobar(TypedDict):  # (1)!
    a: int
    b: NotRequired[float]
    c: NotRequired[Annotated[str, MinLen(5)]]


ta = TypeAdapter(list[Foobar])

v = ta.validate_json('[{"a": 1, "b"', experimental_allow_partial=True)  # (2)!
print(v)
#> [{'a': 1}]

v = ta.validate_json(
    '[{"a": 1, "b": 1.0, "c": "abcd', experimental_allow_partial=True  # (3)!
)
print(v)
#> [{'a': 1, 'b': 1.0}]

v = ta.validate_json(
    '[{"b": 1.0, "c": "abcde"', experimental_allow_partial=True  # (4)!
)
print(v)
#> []

v = ta.validate_json(
    '[{"a": 1, "b": 1.0, "c": "abcde"},{"a": ', experimental_allow_partial=True
)
print(v)
#> [{'a': 1, 'b': 1.0, 'c': 'abcde'}]

v = ta.validate_python([{'a': 1}], experimental_allow_partial=True)  # (5)!
print(v)
#> [{'a': 1}]

v = ta.validate_python(
    [{'a': 1, 'b': 1.0, 'c': 'abcd'}], experimental_allow_partial=True  # (6)!
)
print(v)
#> [{'a': 1, 'b': 1.0}]

v = ta.validate_json(
    '[{"a": 1, "b": 1.0, "c": "abcdefg',
    experimental_allow_partial='trailing-strings',  # (7)!
)
print(v)
#> [{'a': 1, 'b': 1.0, 'c': 'abcdefg'}]
```

1. TypedDict `Foobar` 有三个字段，但只有 `a` 是必需的，这意味着即使 `b` 和 `c` 字段缺失，也可以创建 `Foobar` 的有效实例。
2. 解析 JSON，输入在字符串被截断之前是有效的 JSON。
3. 在这种情况下，输入的截断意味着 `c` 的值（`abcd`）作为 `c` 字段的输入无效，因此被省略。
4. `a` 字段是必需的，因此列表中唯一项的验证失败并被丢弃。
5. 部分验证也适用于 Python 对象，它应该具有与 JSON 相同的语义，当然您不能拥有真正"不完整"的 Python 对象。
6. 与上面相同，但使用 Python 对象，`c` 被丢弃，因为它不是必需的且验证失败。
7. `trailing-strings` 模式允许将部分 JSON 末尾的不完整字符串包含在输出中，在这种情况下，输入在字符串被截断之前是有效的 JSON，因此最后一个字符串被包含。

### 部分验证的工作原理

部分验证遵循 Pydantic 的禅意——它不保证输入数据可能是什么，但确实保证返回您所需类型的有效实例，或者引发验证错误。

为此，`experimental_allow_partial` 标志启用了两种行为：

#### 1. 部分 JSON 解析

Pydantic 使用的 [jiter](https://github.com/pydantic/jiter) JSON 解析器已经支持解析部分 JSON，
`experimental_allow_partial` 只是通过 `allow_partial` 参数传递给 jiter。

!!! note
    如果您只想要支持部分 JSON 的纯 JSON 解析，可以直接使用 [`jiter`](https://pypi.org/project/jiter/) Python 库，或者在调用 [`pydantic_core.from_json`][pydantic_core.from_json] 时传递 `allow_partial` 参数。

#### 2. 忽略输入最后一个元素中的错误 {#2-ignore-errors-in-last}

只能访问部分输入数据意味着错误通常会在输入数据的最后一个元素中发生。

例如：

* 如果字符串有约束 `MinLen(5)`，当您只看到部分输入时，验证可能会失败，因为部分字符串缺失（例如 `{"name": "Sam` 而不是 `{"name": "Samuel"}`）
* 如果 `int` 字段有约束 `Ge(10)`，当您只看到部分输入时，验证可能会失败，因为数字太小（例如 `1` 而不是 `10`）
* 如果 `TypedDict` 字段有 3 个必需字段，但部分输入只有两个字段，验证将失败，因为缺少某些字段
* 等等——还有更多类似的情况

关键是如果您只看到某些有效输入数据的一部分，验证错误通常会在序列的最后一个元素或映射的最后一个值中发生。

为了避免这些错误破坏部分验证，Pydantic 将忽略输入数据最后一个元素中的所有错误。

```python {title="Errors in last element ignored"}
from typing import Annotated

from annotated_types import MinLen

from pydantic import BaseModel, TypeAdapter


class MyModel(BaseModel):
    a: int
    b: Annotated[str, MinLen(5)]


ta = TypeAdapter(list[MyModel])
v = ta.validate_json(
    '[{"a": 1, "b": "12345"}, {"a": 1,',
    experimental_allow_partial=True,
)
print(v)
#> [MyModel(a=1, b='12345')]
```

### 部分验证的限制 {#limitations-of-partial-validation}

#### 仅限 TypeAdapter

您只能将 `experiment_allow_partial` 传递给 [`TypeAdapter`][pydantic.TypeAdapter] 方法，尚不支持通过其他 Pydantic 入口点（如 [`BaseModel`][pydantic.BaseModel]）使用。

#### 支持的类型

目前只有一部分集合验证器知道如何处理部分验证：

* `list`
* `set`
* `frozenset`
* `dict`（如 `dict[X, Y]`）
* `TypedDict` — 只有非必需字段可能缺失，例如通过 [`NotRequired`][typing.NotRequired] 或 [`total=False`][typing.TypedDict.__total__]）

虽然您可以在验证包含其他集合验证器的类型时使用 `experimental_allow_partial`，但这些类型将被"全有或全无"地验证，部分验证将无法在更嵌套的类型上工作。

例如，在[上面](#2-ignore-errors-in-last)的示例中，部分验证有效，尽管列表中的第二项被完全丢弃，因为 `BaseModel` 尚不支持部分验证。

但部分验证在以下示例中根本不起作用，因为 `BaseModel` 不支持部分验证，因此它不会将 `allow_partial` 指令转发给 `b` 中的列表验证器：

```python
from typing import Annotated

from annotated_types import MinLen

from pydantic import BaseModel, TypeAdapter, ValidationError


class MyModel(BaseModel):
    a: int = 1
    b: list[Annotated[str, MinLen(5)]] = []  # (1)!


ta = TypeAdapter(MyModel)
try:
    v = ta.validate_json(
        '{"a": 1, "b": ["12345", "12', experimental_allow_partial=True
    )
except ValidationError as e:
    print(e)
    """
    1 validation error for MyModel
    b.1
      String should have at least 5 characters [type=string_too_short, input_value='12', input_type=str]
    """
```

1. `b` 的列表验证器没有从模型验证器接收到 `allow_partial` 指令，因此它不知道忽略输入最后一个元素中的错误。

#### 一些无效但完整的 JSON 将被接受

[jiter](https://github.com/pydantic/jiter)（Pydantic 使用的 JSON 解析器）的工作方式意味着目前无法区分像 `{"a": 1, "b": "12"}` 这样的完整 JSON 和像 `{"a": 1, "b": "12` 这样的不完整 JSON。

这意味着在使用 `experimental_allow_partial` 时，一些无效的 JSON 将被 Pydantic 接受，例如：

```python
from typing import Annotated

from annotated_types import MinLen
from typing_extensions import TypedDict

from pydantic import TypeAdapter


class Foobar(TypedDict, total=False):
    a: int
    b: Annotated[str, MinLen(5)]


ta = TypeAdapter(Foobar)

v = ta.validate_json(
    '{"a": 1, "b": "12', experimental_allow_partial=True  # (1)!
)
print(v)
#> {'a': 1}

v = ta.validate_json(
    '{"a": 1, "b": "12"}', experimental_allow_partial=True  # (2)!
)
print(v)
#> {'a': 1}
```

1. 这将按预期通过验证，尽管最后一个字段将因验证失败而被省略。
2. 这也将通过验证，因为传递给 pydantic-core 的 JSON 数据的二进制表示与前面的情况无法区分。

#### 输入最后一个字段中的任何错误都将被忽略

如[上面](#2-ignore-errors-in-last)所述，截断输入可能导致许多错误。Pydantic 不是尝试专门忽略可能由截断引起的错误，而是在部分验证模式下忽略输入最后一个元素中的所有错误。

这意味着如果错误在输入的最后一个字段中，明显无效的数据将通过验证：

```python
from typing import Annotated

from annotated_types import Ge

from pydantic import TypeAdapter

ta = TypeAdapter(list[Annotated[int, Ge(10)]])
v = ta.validate_python([20, 30, 4], experimental_allow_partial=True)  # (1)!
print(v)
#> [20, 30]

ta = TypeAdapter(list[int])

v = ta.validate_python([1, 2, 'wrong'], experimental_allow_partial=True)  # (2)!
print(v)
#> [1, 2]
```

1. 正如您所期望的，这将通过验证，因为 Pydantic 正确地忽略了（截断的）最后一项中的错误。
2. 这也将通过验证，因为最后一项中的错误被忽略了。

## 可调用参数的验证

Pydantic 提供了 [`@validate_call`][pydantic.validate_call] 装饰器来对可调用对象的参数（以及返回类型）进行验证。然而，它只允许通过实际调用装饰后的可调用对象来提供参数。在某些情况下，您可能只想*验证*参数，例如从其他数据源（如 JSON 数据）加载时。

因此，实验性的 [`generate_arguments_schema()`][pydantic.experimental.arguments_schema.generate_arguments_schema]
函数可用于构建核心模式，稍后可以与 [`SchemaValidator`][pydantic_core.SchemaValidator] 一起使用。

```python
from pydantic_core import SchemaValidator

from pydantic.experimental.arguments_schema import generate_arguments_schema


def func(p: bool, *args: str, **kwargs: int) -> None: ...


arguments_schema = generate_arguments_schema(func=func)

val = SchemaValidator(arguments_schema, config={'coerce_numbers_to_str': True})

args, kwargs = val.validate_json(
    '{"p": true, "args": ["arg1", 1], "kwargs": {"extra": 1}}'
)
print(args, kwargs)  # (1)!
#> (True, 'arg1', '1') {'extra': 1}
```

1. 如果您想要将验证后的参数作为字典，可以使用 [`Signature.bind()`][inspect.Signature.bind]
   方法：

     ```python {test="skip" lint="skip"}
     from inspect import signature

     signature(func).bind(*args, **kwargs).arguments
     #> {'p': True, 'args': ('arg1', '1'), 'kwargs': {'extra': 1}}
     ```

!!! note
    与 [`@validate_call`][pydantic.validate_call] 不同，此核心模式只会验证提供的参数；
    底层可调用对象将*不会*被调用。

此外，您可以通过提供回调来忽略特定参数，该回调会为每个参数调用：

```python
from typing import Any

from pydantic_core import SchemaValidator

from pydantic.experimental.arguments_schema import generate_arguments_schema


def func(p: bool, *args: str, **kwargs: int) -> None: ...


def skip_first_parameter(index: int, name: str, annotation: Any) -> Any:
    if index == 0:
        return 'skip'


arguments_schema = generate_arguments_schema(
    func=func,
    parameters_callback=skip_first_parameter,
)

val = SchemaValidator(arguments_schema)

args, kwargs = val.validate_json('{"args": ["arg1"], "kwargs": {"extra": 1}}')
print(args, kwargs)
#> ('arg1',) {'extra': 1}
```

## `MISSING` 标记 {#missing-sentinel}

`MISSING` 标记是一个单例，表示在验证期间未提供字段值。

此单例可用作默认值，作为 `None` 的替代方案，当它具有明确含义时。在序列化期间，任何值为 `MISSING` 的字段都将从输出中排除。

```python
from typing import Union

from pydantic import BaseModel
from pydantic.experimental.missing_sentinel import MISSING


class Configuration(BaseModel):
    timeout: Union[int, None, MISSING] = MISSING


# 配置默认值，存储在其他地方：
defaults = {'timeout': 200}

conf = Configuration()

# `timeout` 从序列化输出中排除：
conf.model_dump()
# {}

# `MISSING` 值不会出现在 JSON Schema 中：
Configuration.model_json_schema()['properties']['timeout']
#> {'anyOf': [{'type': 'integer'}, {'type': 'null'}], 'title': 'Timeout'}}


# 可以使用 `is` 来区分标记和其他值：
timeout = conf.timeout if conf.timeout is not MISSING else defaults['timeout']
```

此功能被标记为实验性，因为它依赖于草案 [PEP 661](https://peps.python.org/pep-0661/)，该草案在标准库中引入了标记。

因此，目前存在以下限制：

* 标记的静态类型检查仅支持 Pyright [1.1.402](https://github.com/microsoft/pyright/releases/tag/1.1.402) 或更高版本，并且应启用 `enableExperimentalFeatures` 类型评估设置。
* 不支持包含 `MISSING` 作为值的模型的序列化。