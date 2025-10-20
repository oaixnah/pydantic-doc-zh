---
description: Pydantic 性能优化指南：提升数据验证效率的最佳实践，包括使用 model_validate_json() 替代两步验证、TypeAdapter 单例模式、精确类型选择、标记联合、TypedDict 替代嵌套模型等技巧，帮助开发者优化 Pydantic 应用性能。
---

# 性能提示

在大多数情况下，Pydantic 不会成为你的性能瓶颈，只有在确定有必要时才遵循这些建议。

## 一般情况下，使用 `model_validate_json()` 而不是 `model_validate(json.loads(...))`

在 `model_validate(json.loads(...))` 中，JSON 首先在 Python 中被解析，然后转换为字典，最后在内部进行验证。
另一方面，`model_validate_json()` 已经在内部执行了验证。

有少数情况下 `model_validate(json.loads(...))` 可能更快。具体来说，当在模型上使用 `'before'` 或 `'wrap'` 验证器时，
两步验证方法可能更快。你可以在[这个讨论](https://github.com/pydantic/pydantic/discussions/6388#discussioncomment-8193105)中了解更多关于这些特殊情况的信息。

目前 `pydantic-core` 正在进行许多性能改进，请参阅
[这个讨论](https://github.com/pydantic/pydantic/discussions/6388#discussioncomment-8194048)。
一旦这些更改合并，我们应该达到 `model_validate_json()` 总是比 `model_validate(json.loads(...))` 更快的程度。

## `TypeAdapter` 只实例化一次

这里的想法是避免不必要地多次构造验证器和序列化器。每次实例化 `TypeAdapter` 时，
它都会构造一个新的验证器和序列化器。如果你在函数中使用 `TypeAdapter`，它会在每次
函数调用时被实例化。相反，应该只实例化一次，然后重复使用它。

=== ":x: 错误做法"

    ```python {lint="skip"}
    from pydantic import TypeAdapter


    def my_func():
        adapter = TypeAdapter(list[int])
        # 使用 adapter 做一些事情
    ```

=== ":white_check_mark: 正确做法"

    ```python {lint="skip"}
    from pydantic import TypeAdapter

    adapter = TypeAdapter(list[int])

    def my_func():
        ...
        # 使用 adapter 做一些事情
    ```

## `Sequence` vs `list` 或 `tuple` 以及 `Mapping` vs `dict` {#sequence-vs-list-or-tuple-with-mapping-vs-dict}

当使用 `Sequence` 时，Pydantic 会调用 `isinstance(value, Sequence)` 来检查该值是否是一个序列。
此外，Pydantic 会尝试针对不同类型的序列进行验证，比如 `list` 和 `tuple`。
如果你知道该值是 `list` 或 `tuple`，请使用 `list` 或 `tuple` 而不是 `Sequence`。

同样的规则适用于 `Mapping` 和 `dict`。
如果你知道该值是 `dict`，请使用 `dict` 而不是 `Mapping`。

## 不需要验证时不要验证，使用 `Any` 保持值不变

如果你不需要验证某个值，请使用 `Any` 来保持该值不变。

```python
from typing import Any

from pydantic import BaseModel


class Model(BaseModel):
    a: Any


model = Model(a=1)
```

## 避免通过基本类型的子类添加额外信息

=== "不要这样做"

    ```python
    class CompletedStr(str):
        def __init__(self, s: str):
            self.s = s
            self.done = False
    ```

=== "应该这样做"

    ```python
    from pydantic import BaseModel


    class CompletedModel(BaseModel):
        s: str
        done: bool = False
    ```

## 使用标记联合（tagged union），而不是普通联合

标记联合（或称为可区分联合）是一种带有指示其类型的字段的联合类型。

```python {test="skip"}
from typing import Any, Literal

from pydantic import BaseModel, Field


class DivModel(BaseModel):
    el_type: Literal['div'] = 'div'
    class_name: str | None = None
    children: list[Any] | None = None


class SpanModel(BaseModel):
    el_type: Literal['span'] = 'span'
    class_name: str | None = None
    contents: str | None = None


class ButtonModel(BaseModel):
    el_type: Literal['button'] = 'button'
    class_name: str | None = None
    contents: str | None = None


class InputModel(BaseModel):
    el_type: Literal['input'] = 'input'
    class_name: str | None = None
    value: str | None = None


class Html(BaseModel):
    contents: DivModel | SpanModel | ButtonModel | InputModel = Field(
        discriminator='el_type'
    )
```

有关更多详细信息，请参阅[可区分联合]。

## 使用 `TypedDict` 而不是嵌套模型

不要使用嵌套模型，而是使用 `TypedDict` 来定义数据的结构。

??? info "性能比较"
    通过简单的基准测试，`TypedDict` 比嵌套模型快约 2.5 倍：

    ```python {test="skip"}
    from timeit import timeit

    from typing_extensions import TypedDict

    from pydantic import BaseModel, TypeAdapter


    class A(TypedDict):
        a: str
        b: int


    class TypedModel(TypedDict):
        a: A


    class B(BaseModel):
        a: str
        b: int


    class Model(BaseModel):
        b: B


    ta = TypeAdapter(TypedModel)
    result1 = timeit(
        lambda: ta.validate_python({'a': {'a': 'a', 'b': 2}}), number=10000
    )
    result2 = timeit(
        lambda: Model.model_validate({'b': {'a': 'a', 'b': 2}}), number=10000
    )
    print(result2 / result1)
    ```

## 如果真正关心性能，请避免使用包装验证器

包装验证器通常比其他验证器慢。这是因为它们在验证过程中需要将数据具体化到 Python 中。
包装验证器对于复杂的验证逻辑非常有用，但如果你追求最佳性能，应该避免使用它们。

## 使用 `FailFast` 提前失败

从 v2.8+ 开始，你可以将 `FailFast` 注解应用于序列类型，以便在序列中的任何项验证失败时提前失败。
如果你使用此注解，当序列中的一个项失败时，你将不会获得序列中其余项的验证错误，因此你实际上是在用可见性换取性能。

```python
from typing import Annotated

from pydantic import FailFast, TypeAdapter, ValidationError

ta = TypeAdapter(Annotated[list[bool], FailFast()])
try:
    ta.validate_python([True, 'invalid', False, 'also invalid'])
except ValidationError as exc:
    print(exc)
    """
    1 validation error for list[bool]
    1
      Input should be a valid boolean, unable to interpret input [type=bool_parsing, input_value='invalid', input_type=str]
    """
```

有关 `FailFast` 的更多信息，请参阅[此处][pydantic.types.FailFast]。

[可区分联合]: ../concepts/unions.md#discriminated-unions