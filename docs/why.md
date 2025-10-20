---
subtitle: 为什么使用 Pydantic
---

# 为什么使用 Pydantic Validation？

如今，Pydantic 每月被下载<span id="download-count">许多</span>次，并被世界上一些最大和最知名的组织使用。

很难确切知道为什么自六年前诞生以来，有这么多人采用了 Pydantic，但这里有一些猜测。

## 类型提示驱动的模式验证 {#type-hints}

Pydantic 验证的模式通常由 Python [类型提示](https://docs.python.org/3/glossary.html#term-type-hint)定义。

类型提示非常适合这个用途，因为如果你正在编写现代 Python，你已经知道如何使用它们。
使用类型提示也意味着 Pydantic 与静态类型工具（如 [mypy](https://www.mypy-lang.org/) 和 [Pyright](https://github.com/microsoft/pyright/)）
以及 IDE（如 [PyCharm](https://www.jetbrains.com/pycharm/) 和 [VSCode](https://code.visualstudio.com/)）集成良好。

???+ example "示例 - 仅使用类型提示"
    ```python
    from typing import Annotated, Literal

    from annotated_types import Gt

    from pydantic import BaseModel


    class Fruit(BaseModel):
        name: str  # (1)!
        color: Literal['red', 'green']  # (2)!
        weight: Annotated[float, Gt(0)]  # (3)!
        bazam: dict[str, list[tuple[int, bool, float]]]  # (4)!


    print(
        Fruit(
            name='Apple',
            color='red',
            weight=4.2,
            bazam={'foobar': [(1, True, 0.1)]},
        )
    )
    #> name='Apple' color='red' weight=4.2 bazam={'foobar': [(1, True, 0.1)]}
    ```

    1. `name` 字段简单地用 `str` 注解 &mdash; 允许任何字符串。
    2. [`Literal`][typing.Literal] 类型用于强制 `color` 为 `'red'` 或 `'green'`。
    3. 即使我们想要应用 Python 类型未封装的约束，我们也可以使用 [`Annotated`][typing.Annotated]
       和 [`annotated-types`](https://github.com/annotated-types/annotated-types) 来强制执行约束，同时保持类型支持。
    4. 我并不是声称 "bazam" 真的是水果的属性，而是为了展示任意复杂的类型可以轻松验证。

!!! tip "了解更多"
    参见[支持类型的文档](concepts/types.md)。

## 性能 {#performance}

Pydantic 的核心验证逻辑在一个单独的包 ([`pydantic-core`](https://github.com/pydantic/pydantic-core)) 中实现，
其中大多数类型的验证是用 Rust 实现的。

因此，Pydantic 是 Python 中最快的数据验证库之一。

??? example "性能示例 - Pydantic vs. 专用代码"
    一般来说，专用代码应该比通用验证器快得多，但在这个例子中，
    当解析 JSON 和验证 URL 时，Pydantic 比专用代码快 >300%。

    ```python {title="性能示例" test="skip"}
    import json
    import timeit
    from urllib.parse import urlparse

    import requests

    from pydantic import HttpUrl, TypeAdapter

    reps = 7
    number = 100
    r = requests.get('https://api.github.com/emojis')
    r.raise_for_status()
    emojis_json = r.content


    def emojis_pure_python(raw_data):
        data = json.loads(raw_data)
        output = {}
        for key, value in data.items():
            assert isinstance(key, str)
            url = urlparse(value)
            assert url.scheme in ('https', 'http')
            output[key] = url


    emojis_pure_python_times = timeit.repeat(
        'emojis_pure_python(emojis_json)',
        globals={
            'emojis_pure_python': emojis_pure_python,
            'emojis_json': emojis_json,
        },
        repeat=reps,
        number=number,
    )
    print(f'pure python: {min(emojis_pure_python_times) / number * 1000:0.2f}ms')
    #> pure python: 5.32ms

    type_adapter = TypeAdapter(dict[str, HttpUrl])
    emojis_pydantic_times = timeit.repeat(
        'type_adapter.validate_json(emojis_json)',
        globals={
            'type_adapter': type_adapter,
            'HttpUrl': HttpUrl,
            'emojis_json': emojis_json,
        },
        repeat=reps,
        number=number,
    )
    print(f'pydantic: {min(emojis_pydantic_times) / number * 1000:0.2f}ms')
    #> pydantic: 1.54ms

    print(
        f'Pydantic {min(emojis_pure_python_times) / min(emojis_pydantic_times):0.2f}x faster'
    )
    #> Pydantic 3.45x faster
    ```

与其他用编译语言编写的性能中心库不同，Pydantic 还通过[函数式验证器](#customisation)提供了出色的验证定制支持。

!!! tip "了解更多"
    Samuel Colvin 在 [PyCon 2023 的演讲](https://youtu.be/pWZw7hYoRVU) 解释了 [`pydantic-core`](https://github.com/pydantic/pydantic-core)
    的工作原理以及它如何与 Pydantic 集成。

## 序列化

Pydantic 提供了三种序列化模型的方式：

1. 转换为由关联的 Python 对象组成的 Python `dict`。
2. 转换为仅由 "jsonable" 类型组成的 Python `dict`。
3. 转换为 JSON 字符串。

在所有三种模式中，输出可以通过排除特定字段、排除未设置字段、排除默认值和排除 `None` 值来自定义。

??? example "示例 - 三种序列化方式"

    ```python
    from datetime import datetime

    from pydantic import BaseModel


    class Meeting(BaseModel):
        when: datetime
        where: bytes
        why: str = 'No idea'


    m = Meeting(when='2020-01-01T12:00', where='home')
    print(m.model_dump(exclude_unset=True))
    #> {'when': datetime.datetime(2020, 1, 1, 12, 0), 'where': b'home'}
    print(m.model_dump(exclude={'where'}, mode='json'))
    #> {'when': '2020-01-01T12:00:00', 'why': 'No idea'}
    print(m.model_dump_json(exclude_defaults=True))
    #> {"when":"2020-01-01T12:00:00","where":"home"}
    ```

!!! tip "了解更多"
    参见[序列化文档](concepts/serialization.md)。

## JSON Schema

可以为任何 Pydantic 模式生成 [JSON Schema](https://json-schema.org/) &mdash; 允许自文档化 API 并与支持 JSON Schema 格式的各种工具集成。

??? example "示例 - JSON Schema"

    ```python
    from datetime import datetime

    from pydantic import BaseModel


    class Address(BaseModel):
        street: str
        city: str
        zipcode: str


    class Meeting(BaseModel):
        when: datetime
        where: Address
        why: str = 'No idea'


    print(Meeting.model_json_schema())
    """
    {
        '$defs': {
            'Address': {
                'properties': {
                    'street': {'title': 'Street', 'type': 'string'},
                    'city': {'title': 'City', 'type': 'string'},
                    'zipcode': {'title': 'Zipcode', 'type': 'string'},
                },
                'required': ['street', 'city', 'zipcode'],
                'title': 'Address',
                'type': 'object',
            }
        },
        'properties': {
            'when': {'format': 'date-time', 'title': 'When', 'type': 'string'},
            'where': {'$ref': '#/$defs/Address'},
            'why': {'default': 'No idea', 'title': 'Why', 'type': 'string'},
        },
        'required': ['when', 'where'],
        'title': 'Meeting',
        'type': 'object',
    }
    """
    ```

Pydantic 符合最新版本的 JSON Schema 规范
([2020-12](https://json-schema.org/draft/2020-12/release-notes.html))，该规范
与 [OpenAPI 3.1](https://spec.openapis.org/oas/v3.1.0.html) 兼容。

!!! tip "了解更多"
    参见 [JSON Schema 文档](concepts/json_schema.md)。

## 严格模式和数据强制转换 {#strict-lax}

默认情况下，Pydantic 对常见的不正确类型是宽容的，并将数据强制转换为正确的类型 &mdash;
例如，传递给 `int` 字段的数字字符串将被解析为 `int`。

Pydantic 也有[严格模式](concepts/strict_mode.md)，在这种模式下，类型不会被强制转换，除非输入数据完全匹配预期的模式，否则会引发验证错误。

但在验证 JSON 数据时，严格模式会相当无用，因为 JSON 没有匹配许多常见 Python 类型的类型，
如 [`datetime`][datetime.datetime]、[`UUID`][uuid.UUID] 或 [`bytes`][]。

为了解决这个问题，Pydantic 可以一步解析和验证 JSON。这允许合理的数据转换
（例如，在将字符串解析为 [`datetime`][datetime.datetime] 对象时）。由于 JSON 解析是
用 Rust 实现的，它也非常高效。

??? example "示例 - 真正有用的严格模式"

    ```python
    from datetime import datetime

    from pydantic import BaseModel, ValidationError


    class Meeting(BaseModel):
        when: datetime
        where: bytes


    m = Meeting.model_validate({'when': '2020-01-01T12:00', 'where': 'home'})
    print(m)
    #> when=datetime.datetime(2020, 1, 1, 12, 0) where=b'home'
    try:
        m = Meeting.model_validate(
            {'when': '2020-01-01T12:00', 'where': 'home'}, strict=True
        )
    except ValidationError as e:
        print(e)
        """
        2 validation errors for Meeting
        when
          Input should be a valid datetime [type=datetime_type, input_value='2020-01-01T12:00', input_type=str]
        where
          Input should be a valid bytes [type=bytes_type, input_value='home', input_type=str]
        """

    m_json = Meeting.model_validate_json(
        '{"when": "2020-01-01T12:00", "where": "home"}'
    )
    print(m_json)
    #> when=datetime.datetime(2020, 1, 1, 12, 0) where=b'home'
    ```

!!! tip "了解更多"
    参见[严格模式文档](concepts/strict_mode.md)。

## Dataclasses、TypedDicts 等 {#dataclasses-typeddict-more}

Pydantic 提供了四种创建模式和执行验证和序列化的方式：

1. [`BaseModel`](concepts/models.md) &mdash; Pydantic 自己的超类，通过实例方法提供许多常用实用程序。
2. [Pydantic dataclasses](concepts/dataclasses.md) &mdash; 标准数据类的包装器，执行额外的验证。
3. [`TypeAdapter`][pydantic.type_adapter.TypeAdapter] &mdash; 一种通用的方式来适配任何类型以进行验证和序列化。
   这允许验证像 [`TypedDict`](api/standard_library_types.md#typeddict) 和 [`NamedTuple`](api/standard_library_types.md#named-tuples)
   这样的类型，以及简单类型（如 [`int`][] 或 [`timedelta`][datetime.timedelta]）&mdash; [所有支持的类型](concepts/types.md)
   都可以与 [`TypeAdapter`][pydantic.type_adapter.TypeAdapter] 一起使用。
4. [`validate_call`](concepts/validation_decorator.md) &mdash; 在调用函数时执行验证的装饰器。

??? example "示例 - 基于 [`TypedDict`][typing.TypedDict] 的模式"

    ```python
    from datetime import datetime

    from typing_extensions import NotRequired, TypedDict

    from pydantic import TypeAdapter


    class Meeting(TypedDict):
        when: datetime
        where: bytes
        why: NotRequired[str]


    meeting_adapter = TypeAdapter(Meeting)
    m = meeting_adapter.validate_python(  # (1)!
        {'when': '2020-01-01T12:00', 'where': 'home'}
    )
    print(m)
    #> {'when': datetime.datetime(2020, 1, 1, 12, 0), 'where': b'home'}
    meeting_adapter.dump_python(m, exclude={'where'})  # (2)!

    print(meeting_adapter.json_schema())  # (3)!
    """
    {
        'properties': {
            'when': {'format': 'date-time', 'title': 'When', 'type': 'string'},
            'where': {'format': 'binary', 'title': 'Where', 'type': 'string'},
            'why': {'title': 'Why', 'type': 'string'},
        },
        'required': ['when', 'where'],
        'title': 'Meeting',
        'type': 'object',
    }
    """
    ```

    1. [`TypeAdapter`][pydantic.type_adapter.TypeAdapter] 用于执行验证的 [`TypedDict`][typing.TypedDict]，
       它也可以直接使用 [`validate_json`][pydantic.type_adapter.TypeAdapter.validate_json] 验证 JSON 数据。
    2. [`dump_python`][pydantic.type_adapter.TypeAdapter.dump_python] 将 [`TypedDict`][typing.TypedDict]
       序列化为 python 对象，它也可以使用 [`dump_json`][pydantic.type_adapter.TypeAdapter.dump_json] 序列化为 JSON。
    3. [`TypeAdapter`][pydantic.type_adapter.TypeAdapter] 也可以生成 JSON Schema。

## 自定义 {#customisation}

函数式验证器和序列化器，以及自定义类型的强大协议，意味着 Pydantic 的操作方式可以在每个字段或每个类型的基础上进行定制。

??? example "自定义示例 - 包装验证器"
    "包装验证器" 是 Pydantic V2 中的新功能，是自定义验证的最强大方式之一。

    ```python
    from datetime import datetime, timezone
    from typing import Any

    from pydantic_core.core_schema import ValidatorFunctionWrapHandler

    from pydantic import BaseModel, field_validator


    class Meeting(BaseModel):
        when: datetime

        @field_validator('when', mode='wrap')
        def when_now(
            cls, input_value: Any, handler: ValidatorFunctionWrapHandler
        ) -> datetime:
            if input_value == 'now':
                return datetime.now()
            when = handler(input_value)
            # 在这个特定的应用程序中，我们知道无时区信息的日期时间是在 UTC 中
            if when.tzinfo is None:
                when = when.replace(tzinfo=timezone.utc)
            return when


    print(Meeting(when='2020-01-01T12:00+01:00'))
    #> when=datetime.datetime(2020, 1, 1, 12, 0, tzinfo=TzInfo(3600))
    print(Meeting(when='now'))
    #> when=datetime.datetime(2032, 1, 2, 3, 4, 5, 6)
    print(Meeting(when='2020-01-01T12:00'))
    #> when=datetime.datetime(2020, 1, 1, 12, 0, tzinfo=datetime.timezone.utc)
    ```

!!! tip "了解更多"
    参见[验证器](concepts/validators.md)、[自定义序列化器](concepts/serialization.md#serializers)
    和[自定义类型](concepts/types.md#custom-types)的文档。

## 生态系统 {#ecosystem}

在撰写本文时，GitHub 上有 466,400 个仓库，PyPI 上有 8,119 个包依赖 Pydantic。

一些依赖 Pydantic 的著名库：

{{ libraries }}

更多使用 Pydantic 的库可以在 [`Kludex/awesome-pydantic`](https://github.com/Kludex/awesome-pydantic) 找到。

## 使用 Pydantic 的组织 {#using-pydantic}

一些使用 Pydantic 的著名公司和组织，以及关于我们如何知道他们使用 Pydantic 的评论。

下面的组织被包括在内，是因为它们符合以下一个或多个标准：

* 在公共仓库中使用 Pydantic 作为依赖项。
* 从组织内部域引用 Pydantic 文档站点的流量 &mdash; 具体的引用者不包括在内，因为它们通常不在公共领域。
* Pydantic 团队与受雇于该组织的工程师之间关于在该组织内使用 Pydantic 的直接沟通。

我们在适当且已在公共领域的情况下包含了一些额外细节。

{{ organisations }}