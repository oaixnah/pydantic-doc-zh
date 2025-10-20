---
subtitle: 错误处理
description: Pydantic 错误处理文档：详细介绍 ValidationError 异常的使用方法，包括错误访问方法、ErrorDetails 属性、自定义错误消息和错误位置表示，提供完整的 Python 代码示例和错误处理最佳实践。
---

Pydantic 在验证数据时发现错误时会抛出 [`ValidationError`][pydantic_core.ValidationError]。

!!! note
    验证代码本身不应抛出 [`ValidationError`][pydantic_core.ValidationError]，
    而应抛出 [`ValueError`][] 或 [`AssertionError`][]（或其子类），这些错误将被捕获并用于填充最终的 [`ValidationError`][pydantic_core.ValidationError]。

    更多详细信息，请参阅验证器文档中的[专门章节](../concepts/validators.md#raising-validation-errors)。

该 [`ValidationError`][pydantic_core.ValidationError] 将包含所有错误的信息以及它们是如何发生的。

您可以通过以下几种方式访问这些错误：

| 方法                                                       | 描述                                                                                    |
|--------------------------------------------------------------|------------------------------------------------------------------------------------------------|
| [`errors()`][pydantic_core.ValidationError.errors]           | 返回输入数据中找到的 [`ErrorDetails`][pydantic_core.ErrorDetails] 错误列表。 |
| [`error_count()`][pydantic_core.ValidationError.error_count] | 返回错误数量。                                                                  |
| [`json()`][pydantic_core.ValidationError.json]               | 返回错误列表的 JSON 表示形式。                                              |
| `str(e)`                                                     | 返回错误的人类可读表示形式。                                         |

[`ErrorDetails`][pydantic_core.ErrorDetails] 对象是一个字典。它包含以下内容：

| 属性                                    | 描述                                                                    |
|---------------------------------------------|--------------------------------------------------------------------------------|
| [`ctx`][pydantic_core.ErrorDetails.ctx]     | 一个可选对象，包含渲染错误消息所需的值。 |
| [`input`][pydantic_core.ErrorDetails.input] | 用于验证的输入数据。                                             |
| [`loc`][pydantic_core.ErrorDetails.loc]     | 错误的位置，以列表形式表示。                                                |
| [`msg`][pydantic_core.ErrorDetails.msg]     | 错误的人类可读解释。                                     |
| [`type`][pydantic_core.ErrorDetails.type]   | 错误类型的计算机可读标识符。                              |
| [`url`][pydantic_core.ErrorDetails.url]     | 提供错误信息的文档 URL。                      |

[`loc`][pydantic_core.ErrorDetails.loc] 列表中的第一项将是发生错误的字段，如果该字段是[子模型](../concepts/models.md#nested-models)，则后续项将存在以指示错误的嵌套位置。

作为演示：

```python
from pydantic import BaseModel, Field, ValidationError, field_validator


class Location(BaseModel):
    lat: float = 0.1
    lng: float = 10.1


class Model(BaseModel):
    is_required: float
    gt_int: int = Field(gt=42)
    list_of_ints: list[int]
    a_float: float
    recursive_model: Location

    @field_validator('a_float', mode='after')
    @classmethod
    def validate_float(cls, value: float) -> float:
        if value > 2.0:
            raise ValueError('Invalid float value')
        return value


data = {
    'list_of_ints': ['1', 2, 'bad'],
    'a_float': 3.0,
    'recursive_model': {'lat': 4.2, 'lng': 'New York'},
    'gt_int': 21,
}

try:
    Model(**data)
except ValidationError as e:
    print(e)
    """
    5 validation errors for Model
    is_required
      Field required [type=missing, input_value={'list_of_ints': ['1', 2,...ew York'}, 'gt_int': 21}, input_type=dict]
    gt_int
      Input should be greater than 42 [type=greater_than, input_value=21, input_type=int]
    list_of_ints.2
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='bad', input_type=str]
    a_float
      Value error, Invalid float value [type=value_error, input_value=3.0, input_type=float]
    recursive_model.lng
      Input should be a valid number, unable to parse string as a number [type=float_parsing, input_value='New York', input_type=str]
    """

try:
    Model(**data)
except ValidationError as e:
    print(e.errors())
    """
    [
        {
            'type': 'missing',
            'loc': ('is_required',),
            'msg': 'Field required',
            'input': {
                'list_of_ints': ['1', 2, 'bad'],
                'a_float': 3.0,
                'recursive_model': {'lat': 4.2, 'lng': 'New York'},
                'gt_int': 21,
            },
            'url': 'https://errors.pydantic.dev/2/v/missing',
        },
        {
            'type': 'greater_than',
            'loc': ('gt_int',),
            'msg': 'Input should be greater than 42',
            'input': 21,
            'ctx': {'gt': 42},
            'url': 'https://errors.pydantic.dev/2/v/greater_than',
        },
        {
            'type': 'int_parsing',
            'loc': ('list_of_ints', 2),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'bad',
            'url': 'https://errors.pydantic.dev/2/v/int_parsing',
        },
        {
            'type': 'value_error',
            'loc': ('a_float',),
            'msg': 'Value error, Invalid float value',
            'input': 3.0,
            'ctx': {'error': ValueError('Invalid float value')},
            'url': 'https://errors.pydantic.dev/2/v/value_error',
        },
        {
            'type': 'float_parsing',
            'loc': ('recursive_model', 'lng'),
            'msg': 'Input should be a valid number, unable to parse string as a number',
            'input': 'New York',
            'url': 'https://errors.pydantic.dev/2/v/float_parsing',
        },
    ]
    """
```

## 错误消息

Pydantic 尝试为验证错误和使用错误提供有用的默认错误消息，可以在这里找到：

* [验证错误](validation_errors.md)：在数据验证期间发生的错误。
* [使用错误](usage_errors.md)：在使用 Pydantic 时发生的错误。

### 自定义错误消息

您可以通过创建自定义错误处理程序来自定义错误消息。

```python
from pydantic_core import ErrorDetails

from pydantic import BaseModel, HttpUrl, ValidationError

CUSTOM_MESSAGES = {
    'int_parsing': 'This is not an integer! 🤦',
    'url_scheme': 'Hey, use the right URL scheme! I wanted {expected_schemes}.',
}


def convert_errors(
    e: ValidationError, custom_messages: dict[str, str]
) -> list[ErrorDetails]:
    new_errors: list[ErrorDetails] = []
    for error in e.errors():
        custom_message = custom_messages.get(error['type'])
        if custom_message:
            ctx = error.get('ctx')
            error['msg'] = (
                custom_message.format(**ctx) if ctx else custom_message
            )
        new_errors.append(error)
    return new_errors


class Model(BaseModel):
    a: int
    b: HttpUrl


try:
    Model(a='wrong', b='ftp://example.com')
except ValidationError as e:
    errors = convert_errors(e, CUSTOM_MESSAGES)
    print(errors)
    """
    [
        {
            'type': 'int_parsing',
            'loc': ('a',),
            'msg': 'This is not an integer! 🤦',
            'input': 'wrong',
            'url': 'https://errors.pydantic.dev/2/v/int_parsing',
        },
        {
            'type': 'url_scheme',
            'loc': ('b',),
            'msg': "Hey, use the right URL scheme! I wanted 'http' or 'https'.",
            'input': 'ftp://example.com',
            'ctx': {'expected_schemes': "'http' or 'https'"},
            'url': 'https://errors.pydantic.dev/2/v/url_scheme',
        },
    ]
    """
```

一个常见的用例是翻译错误消息。例如，在上面的示例中，我们可以通过将 `CUSTOM_MESSAGES` 字典替换为翻译字典来翻译错误消息。

另一个例子是自定义错误 `'loc'` 值的表示方式。

```python
from typing import Any, Union

from pydantic import BaseModel, ValidationError


def loc_to_dot_sep(loc: tuple[Union[str, int], ...]) -> str:
    path = ''
    for i, x in enumerate(loc):
        if isinstance(x, str):
            if i > 0:
                path += '.'
            path += x
        elif isinstance(x, int):
            path += f'[{x}]'
        else:
            raise TypeError('Unexpected type')
    return path


def convert_errors(e: ValidationError) -> list[dict[str, Any]]:
    new_errors: list[dict[str, Any]] = e.errors()
    for error in new_errors:
        error['loc'] = loc_to_dot_sep(error['loc'])
    return new_errors


class TestNestedModel(BaseModel):
    key: str
    value: str


class TestModel(BaseModel):
    items: list[TestNestedModel]


data = {'items': [{'key': 'foo', 'value': 'bar'}, {'key': 'baz'}]}

try:
    TestModel.model_validate(data)
except ValidationError as e:
    print(e.errors())  # (1)!
    """
    [
        {
            'type': 'missing',
            'loc': ('items', 1, 'value'),
            'msg': 'Field required',
            'input': {'key': 'baz'},
            'url': 'https://errors.pydantic.dev/2/v/missing',
        }
    ]
    """
    pretty_errors = convert_errors(e)
    print(pretty_errors)  # (2)!
    """
    [
        {
            'type': 'missing',
            'loc': 'items[1].value',
            'msg': 'Field required',
            'input': {'key': 'baz'},
            'url': 'https://errors.pydantic.dev/2/v/missing',
        }
    ]
    """
```

1. 默认情况下，`e.errors()` 会产生一个错误列表，其中 `loc` 值采用元组形式。
2. 使用我们自定义的 `loc_to_dot_sep` 函数，我们修改了 `loc` 的表示形式。