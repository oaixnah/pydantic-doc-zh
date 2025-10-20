---
description: Pydantic JSON 处理指南：学习如何使用 Pydantic 进行高效的 JSON 解析和序列化。了解内置 JSON 解析器、部分 JSON 解析功能、字符串缓存优化以及严格模式验证，提升数据验证性能和灵活性。
---

# JSON

## JSON 解析

??? api "API 文档"
    [`pydantic.main.BaseModel.model_validate_json`][pydantic.main.BaseModel.model_validate_json]
    [`pydantic.type_adapter.TypeAdapter.validate_json`][pydantic.type_adapter.TypeAdapter.validate_json]
    [`pydantic_core.from_json`][pydantic_core.from_json]

Pydantic 提供了内置的 JSON 解析功能，这有助于实现：

* 显著的性能改进，无需使用第三方库的成本
* 支持自定义错误
* 支持 `strict` 规范

以下是 Pydantic 内置 JSON 解析的示例，通过 [`model_validate_json`][pydantic.main.BaseModel.model_validate_json] 方法展示了对 `strict` 规范的支持，同时解析与模型类型注解不匹配的 JSON 数据：

```python
from datetime import date

from pydantic import BaseModel, ConfigDict, ValidationError


class Event(BaseModel):
    model_config = ConfigDict(strict=True)

    when: date
    where: tuple[int, int]


json_data = '{"when": "1987-01-28", "where": [51, -1]}'
print(Event.model_validate_json(json_data))  # (1)!
#> when=datetime.date(1987, 1, 28) where=(51, -1)

try:
    Event.model_validate({'when': '1987-01-28', 'where': [51, -1]})  # (2)!
except ValidationError as e:
    print(e)
    """
    2 validation errors for Event
    when
      Input should be a valid date [type=date_type, input_value='1987-01-28', input_type=str]
    where
      Input should be a valid tuple [type=tuple_type, input_value=[51, -1], input_type=list]
    """
```

1. JSON 没有 `date` 或 tuple 类型，但 Pydantic 知道这一点，因此在直接解析 JSON 时允许分别使用字符串和数组作为输入。
2. 如果将相同的值传递给 [`model_validate`][pydantic.main.BaseModel.model_validate] 方法，Pydantic 将引发验证错误，因为启用了 `strict` 配置。

在 v2.5.0 及更高版本中，Pydantic 使用 [`jiter`](https://docs.rs/jiter/latest/jiter/)（一个快速且可迭代的 JSON 解析器）来解析 JSON 数据。
与 `serde` 相比，使用 `jiter` 带来了适度的性能改进，并且未来会变得更好。

`jiter` JSON 解析器几乎完全兼容 `serde` JSON 解析器，
其中一个显著的增强是 `jiter` 支持反序列化 `inf` 和 `NaN` 值。
在未来，`jiter` 旨在支持验证错误包含原始 JSON 输入中包含无效值的位置。

### 部分 JSON 解析

**从 v2.7.0 开始**，Pydantic 的 [JSON 解析器](https://docs.rs/jiter/latest/jiter/) 提供了对部分 JSON 解析的支持，这通过 [`pydantic_core.from_json`][pydantic_core.from_json] 暴露。以下是此功能的实际示例：

```python
from pydantic_core import from_json

partial_json_data = '["aa", "bb", "c'  # (1)!

try:
    result = from_json(partial_json_data, allow_partial=False)
except ValueError as e:
    print(e)  # (2)!
    #> EOF while parsing a string at line 1 column 15

result = from_json(partial_json_data, allow_partial=True)
print(result)  # (3)!
#> ['aa', 'bb']
```

1. JSON 列表不完整 - 缺少一个闭合的 `"]`
2. 当 `allow_partial` 设置为 `False`（默认值）时，会发生解析错误。
3. 当 `allow_partial` 设置为 `True` 时，部分输入被成功反序列化。

这也适用于反序列化部分字典。例如：

```python
from pydantic_core import from_json

partial_dog_json = '{"breed": "lab", "name": "fluffy", "friends": ["buddy", "spot", "rufus"], "age'
dog_dict = from_json(partial_dog_json, allow_partial=True)
print(dog_dict)
#> {'breed': 'lab', 'name': 'fluffy', 'friends': ['buddy', 'spot', 'rufus']}
```

!!! tip "验证 LLM 输出"
    此功能对于验证 LLM 输出特别有益。
    我们撰写了一些关于此主题的博客文章，您可以在[我们的网站](https://pydantic.dev/articles)上找到。

在未来的 Pydantic 版本中，我们期望通过 Pydantic 的其他 JSON 验证功能
([`pydantic.main.BaseModel.model_validate_json`][pydantic.main.BaseModel.model_validate_json] 和
[`pydantic.type_adapter.TypeAdapter.validate_json`][pydantic.type_adapter.TypeAdapter.validate_json]) 或模型配置来扩展对此功能的支持。敬请期待 🚀！

目前，您可以将 [`pydantic_core.from_json`][pydantic_core.from_json] 与 [`pydantic.main.BaseModel.model_validate`][pydantic.main.BaseModel.model_validate] 结合使用以达到相同的结果。以下是一个示例：

```python
from pydantic_core import from_json

from pydantic import BaseModel


class Dog(BaseModel):
    breed: str
    name: str
    friends: list


partial_dog_json = '{"breed": "lab", "name": "fluffy", "friends": ["buddy", "spot", "rufus"], "age'
dog = Dog.model_validate(from_json(partial_dog_json, allow_partial=True))
print(repr(dog))
#> Dog(breed='lab', name='fluffy', friends=['buddy', 'spot', 'rufus'])
```

!!! tip
    为了使部分 JSON 解析可靠工作，模型上的所有字段都应具有默认值。

查看以下示例，深入了解如何在部分 JSON 解析中使用默认值：

!!! example "在部分 JSON 解析中使用默认值"

    ```python
    from typing import Annotated, Any, Optional

    import pydantic_core

    from pydantic import BaseModel, ValidationError, WrapValidator


    def default_on_error(v, handler) -> Any:
        """
        如果值缺失，则引发 PydanticUseDefault 异常。

        这对于避免因部分 JSON 阻止成功验证而导致的错误非常有用。
        """
        try:
            return handler(v)
        except ValidationError as exc:
            # 可能存在其他类型的错误，这些错误是由于部分 JSON 解析导致的
            # 您可以在这里允许这些错误，根据需要自由定制
            if all(e['type'] == 'missing' for e in exc.errors()):
                raise pydantic_core.PydanticUseDefault()
            else:
                raise


    class NestedModel(BaseModel):
        x: int
        y: str


    class MyModel(BaseModel):
        foo: Optional[str] = None
        bar: Annotated[
            Optional[tuple[str, int]], WrapValidator(default_on_error)
        ] = None
        nested: Annotated[
            Optional[NestedModel], WrapValidator(default_on_error)
        ] = None


    m = MyModel.model_validate(
        pydantic_core.from_json('{"foo": "x", "bar": ["world",', allow_partial=True)
    )
    print(repr(m))
    #> MyModel(foo='x', bar=None, nested=None)


    m = MyModel.model_validate(
        pydantic_core.from_json(
            '{"foo": "x", "bar": ["world", 1], "nested": {"x":', allow_partial=True
        )
    )
    print(repr(m))
    #> MyModel(foo='x', bar=('world', 1), nested=None)
    ```

### 字符串缓存

**从 v2.7.0 开始**，Pydantic 的 [JSON 解析器](https://docs.rs/jiter/latest/jiter/) 提供了配置在 JSON 解析和验证期间如何缓存 Python 字符串的支持（当在 Python 验证期间从 Rust 字符串构造 Python 字符串时，例如在 `strip_whitespace=True` 之后）。
`cache_strings` 设置通过 [模型配置][pydantic.config.ConfigDict] 和 [`pydantic_core.from_json`][pydantic_core.from_json] 暴露。

`cache_strings` 设置可以接受以下任何值：

* `True` 或 `'all'`（默认值）：缓存所有字符串
* `'keys'`：仅缓存字典键，这**仅**适用于与 [`pydantic_core.from_json`][pydantic_core.from_json] 一起使用或使用 [`Json`][pydantic.types.Json] 解析 JSON 时
* `False` 或 `'none'`：不缓存

使用字符串缓存功能可以提高性能，但会稍微增加内存使用量。

!!! note "字符串缓存详情"

    1. 字符串使用大小为 [16,384](https://github.com/pydantic/jiter/blob/5bbdcfd22882b7b286416b22f74abd549c7b2fd7/src/py_string_cache.rs#L113) 的全相联缓存进行缓存。
    2. 仅缓存 `len(string) < 64` 的字符串。
    3. 查找缓存会有一些开销，这通常值得避免构造字符串。
    但是，如果您知道数据中重复字符串很少，通过禁用此设置 `cache_strings=False` 可能会获得性能提升。

## JSON 序列化

??? api "API 文档"
    [`pydantic.main.BaseModel.model_dump_json`][pydantic.main.BaseModel.model_dump_json]<br>
    [`pydantic.type_adapter.TypeAdapter.dump_json`][pydantic.type_adapter.TypeAdapter.dump_json]<br>
    [`pydantic_core.to_json`][pydantic_core.to_json]<br>

有关 JSON 序列化的更多信息，请参阅[序列化概念](./serialization.md)页面。