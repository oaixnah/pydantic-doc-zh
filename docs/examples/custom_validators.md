---
subtitle: 自定义验证器
description: Pydantic 自定义验证器示例文档，展示如何创建复杂的自定义验证逻辑。包括通过 Annotated 元数据的 datetime 验证器，实现时区约束和 UTC 偏移验证，以及验证嵌套模型字段的两种方法。这些示例展示了 Pydantic 验证系统的灵活性和强大功能，帮助开发者实现高级数据验证需求。
---

本页面提供了创建更复杂的自定义验证器的示例代码片段。
这些示例大多改编自 Pydantic 的问题和讨论，旨在展示 Pydantic 验证系统的灵活性和强大功能。

## 通过 [`Annotated`][typing.Annotated] 元数据的自定义 `datetime` 验证器

在这个示例中，我们将构建一个自定义验证器，附加到 [`Annotated`][typing.Annotated] 类型上，
确保 [`datetime`][datetime.datetime] 对象符合给定的时区约束。

自定义验证器支持字符串形式的时区规范，如果 [`datetime`][datetime.datetime] 对象没有正确的时区，将引发错误。

我们在验证器中使用 `__get_pydantic_core_schema__` 来自定义注解类型的模式（在本例中为 [`datetime`][datetime.datetime]），这允许我们添加自定义验证逻辑。值得注意的是，我们使用 `wrap` 验证器函数，以便我们可以在默认的 `pydantic` 对 [`datetime`][datetime.datetime] 的验证前后执行操作。

```python
import datetime as dt
from dataclasses import dataclass
from pprint import pprint
from typing import Annotated, Any, Callable, Optional

import pytz
from pydantic_core import CoreSchema, core_schema

from pydantic import (
    GetCoreSchemaHandler,
    PydanticUserError,
    TypeAdapter,
    ValidationError,
)


@dataclass(frozen=True)
class MyDatetimeValidator:
    tz_constraint: Optional[str] = None

    def tz_constraint_validator(
        self,
        value: dt.datetime,
        handler: Callable,  # (1)!
    ):
        """验证 tz_constraint 和 tz_info。"""
        # 处理朴素日期时间
        if self.tz_constraint is None:
            assert (
                value.tzinfo is None
            ), 'tz_constraint 为 None，但提供的值有时区信息。'
            return handler(value)

        # 验证 tz_constraint 和有时区信息的 tzinfo
        if self.tz_constraint not in pytz.all_timezones:
            raise PydanticUserError(
                f'无效的 tz_constraint: {self.tz_constraint}',
                code='unevaluable-type-annotation',
            )
        result = handler(value)  # (2)!
        assert self.tz_constraint == str(
            result.tzinfo
        ), f'无效的 tzinfo: {str(result.tzinfo)}, 期望: {self.tz_constraint}'

        return result

    def __get_pydantic_core_schema__(
        self,
        source_type: Any,
        handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        return core_schema.no_info_wrap_validator_function(
            self.tz_constraint_validator,
            handler(source_type),
        )


LA = 'America/Los_Angeles'
ta = TypeAdapter(Annotated[dt.datetime, MyDatetimeValidator(LA)])
print(
    ta.validate_python(dt.datetime(2023, 1, 1, 0, 0, tzinfo=pytz.timezone(LA)))
)
#> 2023-01-01 00:00:00-07:53

LONDON = 'Europe/London'
try:
    ta.validate_python(
        dt.datetime(2023, 1, 1, 0, 0, tzinfo=pytz.timezone(LONDON))
    )
except ValidationError as ve:
    pprint(ve.errors(), width=100)
    """
    [{'ctx': {'error': AssertionError('Invalid tzinfo: Europe/London, expected: America/Los_Angeles')},
    'input': datetime.datetime(2023, 1, 1, 0, 0, tzinfo=<DstTzInfo 'Europe/London' LMT-1 day, 23:59:00 STD>),
    'loc': (),
    'msg': 'Assertion failed, Invalid tzinfo: Europe/London, expected: America/Los_Angeles',
    'type': 'assertion_error',
    'url': 'https://errors.pydantic.dev/2.8/v/assertion_error'}]
    """
```

1. `handler` 函数是我们用来使用标准 `pydantic` 验证来验证输入的函数
2. 在这个包装验证器中，我们调用 `handler` 函数来使用标准 `pydantic` 验证来验证输入

我们也可以用类似的方式强制执行UTC偏移约束。假设我们有一个 `lower_bound` 和一个 `upper_bound`，我们可以创建一个自定义验证器来确保我们的 `datetime` 的UTC偏移在我们定义的边界内（包含边界）：

```python
import datetime as dt
from dataclasses import dataclass
from pprint import pprint
from typing import Annotated, Any, Callable

import pytz
from pydantic_core import CoreSchema, core_schema

from pydantic import GetCoreSchemaHandler, TypeAdapter, ValidationError


@dataclass(frozen=True)
class MyDatetimeValidator:
    lower_bound: int
    upper_bound: int

    def validate_tz_bounds(self, value: dt.datetime, handler: Callable):
        """验证和测试边界"""
        assert value.utcoffset() is not None, 'UTC偏移必须存在'
        assert self.lower_bound <= self.upper_bound, '无效的边界'

        result = handler(value)

        hours_offset = value.utcoffset().total_seconds() / 3600
        assert (
            self.lower_bound <= hours_offset <= self.upper_bound
        ), '值超出边界'

        return result

    def __get_pydantic_core_schema__(
        self,
        source_type: Any,
        handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        return core_schema.no_info_wrap_validator_function(
            self.validate_tz_bounds,
            handler(source_type),
        )


LA = 'America/Los_Angeles'  # UTC-7 or UTC-8
ta = TypeAdapter(Annotated[dt.datetime, MyDatetimeValidator(-10, -5)])
print(
    ta.validate_python(dt.datetime(2023, 1, 1, 0, 0, tzinfo=pytz.timezone(LA)))
)
#> 2023-01-01 00:00:00-07:53

LONDON = 'Europe/London'
try:
    print(
        ta.validate_python(
            dt.datetime(2023, 1, 1, 0, 0, tzinfo=pytz.timezone(LONDON))
        )
    )
except ValidationError as e:
    pprint(e.errors(), width=100)
    """
    [{'ctx': {'error': AssertionError('Value out of bounds')},
    'input': datetime.datetime(2023, 1, 1, 0, 0, tzinfo=<DstTzInfo 'Europe/London' LMT-1 day, 23:59:00 STD>),
    'loc': (),
    'msg': 'Assertion failed, Value out of bounds',
    'type': 'assertion_error',
    'url': 'https://errors.pydantic.dev/2.8/v/assertion_error'}]
    """
```

## 验证嵌套模型字段

在这里，我们演示了两种验证嵌套模型字段的方法，其中验证器利用来自父模型的数据。

在这个示例中，我们构建一个验证器，检查每个用户的密码是否不在父模型指定的禁止密码列表中。

一种方法是在外部模型上放置自定义验证器：

```python
from typing_extensions import Self

from pydantic import BaseModel, ValidationError, model_validator


class User(BaseModel):
    username: str
    password: str


class Organization(BaseModel):
    forbidden_passwords: list[str]
    users: list[User]

    @model_validator(mode='after')
    def validate_user_passwords(self) -> Self:
        """检查用户密码是否不在禁止列表中。如果遇到禁止密码，则引发验证错误。"""
        for user in self.users:
            current_pw = user.password
            if current_pw in self.forbidden_passwords:
                raise ValueError(
                    f'Password {current_pw} is forbidden. Please choose another password for user {user.username}.'
                )
        return self


data = {
    'forbidden_passwords': ['123'],
    'users': [
        {'username': 'Spartacat', 'password': '123'},
        {'username': 'Iceburgh', 'password': '87'},
    ],
}
try:
    org = Organization(**data)
except ValidationError as e:
    print(e)
    """
    1 validation error for Organization
      Value error, Password 123 is forbidden. Please choose another password for user Spartacat. [type=value_error, input_value={'forbidden_passwords': [...gh', 'password': '87'}]}, input_type=dict]
    """
```

或者，可以在嵌套模型类（`User`）中使用自定义验证器，通过验证上下文传递来自父模型的禁止密码数据。

!!! warning
    在验证器内修改上下文的能力为嵌套验证增加了很大的灵活性，但也可能导致代码难以理解或调试。请自行承担使用此方法的风险！

```python
from pydantic import BaseModel, ValidationError, ValidationInfo, field_validator


class User(BaseModel):
    username: str
    password: str

    @field_validator('password', mode='after')
    @classmethod
    def validate_user_passwords(
        cls, password: str, info: ValidationInfo
    ) -> str:
        """检查用户密码是否不在禁止列表中。"""
        forbidden_passwords = (
            info.context.get('forbidden_passwords', []) if info.context else []
        )
        if password in forbidden_passwords:
            raise ValueError(f'Password {password} is forbidden.')
        return password


class Organization(BaseModel):
    forbidden_passwords: list[str]
    users: list[User]

    @field_validator('forbidden_passwords', mode='after')
    @classmethod
    def add_context(cls, v: list[str], info: ValidationInfo) -> list[str]:
        if info.context is not None:
            info.context.update({'forbidden_passwords': v})
        return v


data = {
    'forbidden_passwords': ['123'],
    'users': [
        {'username': 'Spartacat', 'password': '123'},
        {'username': 'Iceburgh', 'password': '87'},
    ],
}

try:
    org = Organization.model_validate(data, context={})
except ValidationError as e:
    print(e)
    """
    1 validation error for Organization
    users.0.password
      Value error, Password 123 is forbidden. [type=value_error, input_value='123', input_type=str]
    """
```

请注意，如果在 `model_validate` 中未包含 context 属性，则 `info.context` 将为 `None`，并且在上面的实现中，禁止密码列表将不会被添加到上下文中。因此，`validate_user_passwords` 将不会执行所需的密码验证。

有关验证上下文的更多详细信息，请参阅[验证器文档](../concepts/validators.md#validation-context)。