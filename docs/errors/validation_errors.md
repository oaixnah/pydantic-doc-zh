---
subtitle: 验证错误
description: Pydantic 验证错误文档详细介绍了在使用 Pydantic 数据验证库时可能遇到的各种验证错误类型，包括参数类型错误、断言错误、布尔值解析错误、字节类型错误、日期时间验证错误、数字约束错误、URL验证错误等。每个错误类型都提供了详细的解释、示例代码和修复建议，帮助开发者快速识别和解决数据验证问题，提高 Python 应用程序的健壮性和可靠性。
---

Pydantic 尝试提供有用的验证错误。以下是用户在使用 pydantic 时可能遇到的常见验证错误的详细信息，以及一些修复建议。

## `arguments_type`

当在验证期间传递给函数作为参数的对象不是 `tuple`、`list` 或 `dict` 时，会引发此错误。因为 `NamedTuple` 在其实现中使用了函数调用，这是产生此错误的一种方式：

```python
from typing import NamedTuple

from pydantic import BaseModel, ValidationError


class MyNamedTuple(NamedTuple):
    x: int


class MyModel(BaseModel):
    field: MyNamedTuple


try:
    MyModel.model_validate({'field': 'invalid'})
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'arguments_type'
```

## `assertion_error`

当在验证期间遇到失败的 `assert` 语句时，会引发此错误：

```python
from pydantic import BaseModel, ValidationError, field_validator


class Model(BaseModel):
    x: int

    @field_validator('x')
    @classmethod
    def force_x_positive(cls, v):
        assert v > 0
        return v


try:
    Model(x=-1)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'assertion_error'
```

## `bool_parsing`

当输入值是一个无法强制转换为布尔值的字符串时，会引发此错误：

```python
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: bool


Model(x='true')  # 正常

try:
    Model(x='test')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'bool_parsing'
```

## `bool_type`

当输入值的类型对于 `bool` 字段无效时，会引发此错误：

```python
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: bool


try:
    Model(x=None)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'bool_type'
```

对于严格字段，当输入值不是 `bool` 的实例时，也会引发此错误。

## `bytes_invalid_encoding`

当 `bytes` 值在配置的编码下无效时，会引发此错误。
在以下示例中，`b'a'` 是无效的十六进制（奇数位数）。

```python
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: bytes
    model_config = {'val_json_bytes': 'hex'}


try:
    Model(x=b'a')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'bytes_invalid_encoding'
```

## `bytes_too_long`

当 `bytes` 值的长度大于字段的 `max_length` 约束时，会引发此错误：

```python
from pydantic import BaseModel, Field, ValidationError


class Model(BaseModel):
    x: bytes = Field(max_length=3)


try:
    Model(x=b'test')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'bytes_too_long'
```

## `bytes_too_short`

当 `bytes` 值的长度小于字段的 `min_length` 约束时，会引发此错误：

```python
from pydantic import BaseModel, Field, ValidationError


class Model(BaseModel):
    x: bytes = Field(min_length=3)


try:
    Model(x=b't')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'bytes_too_short'
```

## `bytes_type`

当输入值的类型对于 `bytes` 字段无效时，会引发此错误：

```python
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: bytes


try:
    Model(x=123)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'bytes_type'
```

对于严格字段，当输入值不是 `bytes` 的实例时，也会引发此错误。

## `callable_type`

当输入值作为 `Callable` 无效时，会引发此错误：

```python
from typing import Any, Callable

from pydantic import BaseModel, ImportString, ValidationError


class Model(BaseModel):
    x: ImportString[Callable[[Any], Any]]


Model(x='math:cos')  # 正常

try:
    Model(x='os.path')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'callable_type'
```

## `complex_str_parsing`

当输入值是一个字符串但无法解析为复数时，会引发此错误，因为它不遵循 Python 中的[规则](https://docs.python.org/3/library/functions.html#complex)：

```python
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    num: complex


try:
    # JSON 中的复数应为有效的复数字符串。
    # 值 `abc` 不是有效的复数字符串。
    Model.model_validate_json('{"num": "abc"}')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'complex_str_parsing'
```

## `complex_type`

当输入值无法解释为复数时，会引发此错误：

```python
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    num: complex


try:
    Model(num=False)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'complex_type'
```

## `dataclass_exact_type`

当使用 `strict=True` 验证数据类且输入不是该数据类的实例时，会引发此错误：

```python
import pydantic.dataclasses
from pydantic import TypeAdapter, ValidationError


@pydantic.dataclasses.dataclass
class MyDataclass:
    x: str


adapter = TypeAdapter(MyDataclass)

print(adapter.validate_python(MyDataclass(x='test'), strict=True))
#> MyDataclass(x='test')
print(adapter.validate_python({'x': 'test'}))
#> MyDataclass(x='test')

try:
    adapter.validate_python({'x': 'test'}, strict=True)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'dataclass_exact_type'
```

## `dataclass_type`

当输入值对于 `dataclass` 字段无效时，会引发此错误：

```python
from pydantic import ValidationError, dataclasses


@dataclasses.dataclass
class Inner:
    x: int


@dataclasses.dataclass
class Outer:
    y: Inner


Outer(y=Inner(x=1))  # 正常

try:
    Outer(y=1)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'dataclass_type'
```

## `date_from_datetime_inexact`

当为 `date` 字段提供的输入 `datetime` 值具有非零时间分量时，会引发此错误。
对于要解析为 `date` 类型字段的时间戳，时间分量必须全部为零：

```python
from datetime import date, datetime

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: date


Model(x='2023-01-01')  # 正常
Model(x=datetime(2023, 1, 1))  # 正常

try:
    Model(x=datetime(2023, 1, 1, 12))
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'date_from_datetime_inexact'
```

## `date_from_datetime_parsing`

当输入值是一个无法为 `date` 字段解析的字符串时，会引发此错误：

```python
from datetime import date

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: date


try:
    Model(x='XX1494012000')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'date_from_datetime_parsing'
```

## `date_future`

当为 `FutureDate` 字段提供的输入值不在未来时，会引发此错误：

```python
from datetime import date

from pydantic import BaseModel, FutureDate, ValidationError


class Model(BaseModel):
    x: FutureDate


try:
    Model(x=date(2000, 1, 1))
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'date_future'
```

## `date_parsing`

当验证 JSON 时，输入值是无法为 `date` 字段解析的字符串时，会引发此错误：

```python
import json
from datetime import date

from pydantic import BaseModel, Field, ValidationError


class Model(BaseModel):
    x: date = Field(strict=True)


try:
    Model.model_validate_json(json.dumps({'x': '1'}))
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'date_parsing'
```

## `date_past`

当为 `PastDate` 字段提供的值不在过去时，会引发此错误：

```python
from datetime import date, timedelta

from pydantic import BaseModel, PastDate, ValidationError


class Model(BaseModel):
    x: PastDate


try:
    Model(x=date.today() + timedelta(1))
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'date_past'
```

## `date_type`

当输入值的类型对于 `date` 字段无效时，会引发此错误：

```python
from datetime import date

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: date


try:
    Model(x=None)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'date_type'
```

对于严格字段，当输入值不是 `date` 的实例时，也会引发此错误。

## `datetime_from_date_parsing`

当输入值是一个无法为 `datetime` 字段解析的字符串时，会引发此错误：

```python
from datetime import datetime

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: datetime


try:
    # 没有第13个月
    Model(x='2023-13-01')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'datetime_from_date_parsing'
```

## `datetime_future`

当为 `FutureDatetime` 字段提供的值不在未来时，会引发此错误：

```python
from datetime import datetime

from pydantic import BaseModel, FutureDatetime, ValidationError


class Model(BaseModel):
    x: FutureDatetime


try:
    Model(x=datetime(2000, 1, 1))
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'datetime_future'
```

## `datetime_object_invalid`

当 `datetime` 对象的某些方面无效时，会引发此错误：

```python
from datetime import datetime, tzinfo

from pydantic import AwareDatetime, BaseModel, ValidationError


class CustomTz(tzinfo):
    # utcoffset 未实现！

    def tzname(self, _dt):
        return 'CustomTZ'


class Model(BaseModel):
    x: AwareDatetime


try:
    Model(x=datetime(2023, 1, 1, tzinfo=CustomTz()))
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'datetime_object_invalid'
```

## `datetime_parsing`

当值是一个无法为 `datetime` 字段解析的字符串时，会引发此错误：

```python
import json
from datetime import datetime

from pydantic import BaseModel, Field, ValidationError


class Model(BaseModel):
    x: datetime = Field(strict=True)


try:
    Model.model_validate_json(json.dumps({'x': 'not a datetime'}))
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'datetime_parsing'
```

## `datetime_past`

当为 `PastDatetime` 字段提供的值不在过去时，会引发此错误：

```python
from datetime import datetime, timedelta

from pydantic import BaseModel, PastDatetime, ValidationError


class Model(BaseModel):
    x: PastDatetime


try:
    Model(x=datetime.now() + timedelta(100))
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'datetime_past'
```

## `datetime_type`

当输入值的类型对于 `datetime` 字段无效时，会引发此错误：

```python
from datetime import datetime

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: datetime


try:
    Model(x=None)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'datetime_type'
```

对于严格字段，当输入值不是 `datetime` 的实例时，也会引发此错误。

## `decimal_max_digits`

当为 `Decimal` 提供的值有太多位数时，会引发此错误：

```python
from decimal import Decimal

from pydantic import BaseModel, Field, ValidationError


class Model(BaseModel):
    x: Decimal = Field(max_digits=3)


try:
    Model(x='42.1234')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'decimal_max_digits'
```

## `decimal_max_places`

当为 `Decimal` 提供的值在小数点后有太多位数时，会引发此错误：

```python
from decimal import Decimal

from pydantic import BaseModel, Field, ValidationError


class Model(BaseModel):
    x: Decimal = Field(decimal_places=3)


try:
    Model(x='42.1234')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'decimal_max_places'
```

## `decimal_parsing`

当为 `Decimal` 提供的值无法解析为十进制数字时，会引发此错误：

```python
from decimal import Decimal

from pydantic import BaseModel, Field, ValidationError


class Model(BaseModel):
    x: Decimal = Field(decimal_places=3)


try:
    Model(x='test')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'decimal_parsing'
```

## `decimal_type`

当为 `Decimal` 提供的值类型错误时，会引发此错误：

```python
from decimal import Decimal

from pydantic import BaseModel, Field, ValidationError


class Model(BaseModel):
    x: Decimal = Field(decimal_places=3)


try:
    Model(x=[1, 2, 3])
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'decimal_type'
```

对于严格字段，当输入值不是 `Decimal` 的实例时，也会引发此错误。

## `decimal_whole_digits`

当为 `Decimal` 提供的值在小数点前的位数超过 `max_digits` - `decimal_places` 时（只要两者都指定），会引发此错误：

```python
from decimal import Decimal

from pydantic import BaseModel, Field, ValidationError


class Model(BaseModel):
    x: Decimal = Field(max_digits=6, decimal_places=3)


try:
    Model(x='12345.6')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'decimal_whole_digits'
```

## `default_factory_not_called`

当[使用已验证数据的默认工厂](../concepts/fields.md#default-factory-validated-data)
无法被调用时，会引发此错误，因为先前字段的验证失败：

```python
from pydantic import BaseModel, Field, ValidationError


class Model(BaseModel):
    a: int = Field(gt=10)
    b: int = Field(default_factory=lambda data: data['a'])


try:
    Model(a=1)
except ValidationError as exc:
    print(exc)
    """
    2 validation errors for Model
    a
      Input should be greater than 10 [type=greater_than, input_value=1, input_type=int]
    b
      The default factory uses validated data, but at least one validation error occurred [type=default_factory_not_called]
    """
    print(repr(exc.errors()[1]['type']))
    #> 'default_factory_not_called'
```

## `dict_type`

当输入值的类型对于 `dict` 字段不是 `dict` 时，会引发此错误：

```python
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: dict


try:
    Model(x=['1', '2'])
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'dict_type'
```

## `enum`

当输入值不存在于 `enum` 字段的成员中时，会引发此错误：

```python
from enum import Enum

from pydantic import BaseModel, ValidationError


class MyEnum(str, Enum):
    option = 'option'


class Model(BaseModel):
    x: MyEnum


try:
    Model(x='other_option')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'enum'
```

## `extra_forbidden`

当输入值包含额外字段，但 `model_config['extra'] == 'forbid'` 时，会引发此错误：

```python
from pydantic import BaseModel, ConfigDict, ValidationError


class Model(BaseModel):
    x: str

    model_config = ConfigDict(extra='forbid')


try:
    Model(x='test', y='test')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'extra_forbidden'
```

您可以在[额外属性][pydantic.config.ConfigDict.extra]部分阅读更多关于 `extra` 配置的信息。

## `finite_number`

当值无限大，或者在验证期间太大而无法表示为64位浮点数时，会引发此错误：

```python
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: int


try:
    Model(x=2.2250738585072011e308)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'finite_number'
```

## `float_parsing`

当值是一个无法解析为 `float` 的字符串时，会引发此错误：

```python
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: float


try:
    Model(x='test')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'float_parsing'
```

## `float_type`

当输入值的类型对于 `float` 字段无效时，会引发此错误：

```python
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: float


try:
    Model(x=None)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'float_type'
```

## `frozen_field`

当您尝试为具有 `frozen=True` 的字段赋值或删除此类字段时，会引发此错误：

```python
from pydantic import BaseModel, Field, ValidationError


class Model(BaseModel):
    x: str = Field('test', frozen=True)


model = Model()

try:
    model.x = 'test1'
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'frozen_field'

try:
    del model.x
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'frozen_field'
```

## `frozen_instance`

当在[配置](../concepts/config.md)中设置了 `frozen` 并且您尝试删除或为任何字段分配新值时，会引发此错误：

```python
from pydantic import BaseModel, ConfigDict, ValidationError


class Model(BaseModel):
    x: int

    model_config = ConfigDict(frozen=True)


m = Model(x=1)

try:
    m.x = 2
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'frozen_instance'

try:
    del m.x
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'frozen_instance'
```

## `frozen_set_type`

当输入值的类型对于 `frozenset` 字段无效时，会引发此错误：

```python
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: frozenset


try:
    model = Model(x='test')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'frozen_set_type'
```

## `get_attribute_error`

当 `model_config['from_attributes'] == True` 并且在读取属性时引发错误时，会引发此错误：

```python
from pydantic import BaseModel, ConfigDict, ValidationError


class Foobar:
    def __init__(self):
        self.x = 1

    @property
    def y(self):
        raise RuntimeError('intentional error')


class Model(BaseModel):
    x: int
    y: str

    model_config = ConfigDict(from_attributes=True)


try:
    Model.model_validate(Foobar())
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'get_attribute_error'
```

## `greater_than`

当值不大于字段的 `gt` 约束时，会引发此错误：

```python
from pydantic import BaseModel, Field, ValidationError


class Model(BaseModel):
    x: int = Field(gt=10)


try:
    Model(x=10)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'greater_than'
```

## `greater_than_equal`

当值不大于或等于字段的 `ge` 约束时，会引发此错误：

```python
from pydantic import BaseModel, Field, ValidationError


class Model(BaseModel):
    x: int = Field(ge=10)


try:
    Model(x=9)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'greater_than_equal'
```

## `int_from_float`

当您为 `int` 字段提供 `float` 值时，会引发此错误：

```python
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: int


try:
    Model(x=0.5)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'int_from_float'
```

## `int_parsing`

当值无法解析为 `int` 时，会引发此错误：

```python
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: int


try:
    Model(x='test')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'int_parsing'
```

## `int_parsing_size`

当尝试从超出 Python `str` 到 `int` 解析允许的最大范围的字符串解析 Python 或 JSON 值时，会引发此错误：

```python
import json

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: int


# 从 Python
assert Model(x='1' * 4_300).x == int('1' * 4_300)  # 正常

too_long = '1' * 4_301
try:
    Model(x=too_long)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'int_parsing_size'

# 从 JSON
try:
    Model.model_validate_json(json.dumps({'x': too_long}))
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'int_parsing_size'
```

## `int_type`

当输入值的类型对于 `int` 字段无效时，会引发此错误：

```python
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: int


try:
    Model(x=None)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'int_type'
```

## `invalid_key`

当尝试验证具有非 `str` 实例键的 `dict` 时，会引发此错误：

```python
from pydantic import BaseModel, ConfigDict, ValidationError


class Model(BaseModel):
    x: int

    model_config = ConfigDict(extra='allow')


try:
    Model.model_validate({'x': 1, b'y': 2})
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'invalid_key'
```

## `is_instance_of`

当输入值不是预期类型的实例时，会引发此错误：

```python
from pydantic import BaseModel, ConfigDict, ValidationError


class Nested:
    x: str


class Model(BaseModel):
    y: Nested

    model_config = ConfigDict(arbitrary_types_allowed=True)


try:
    Model(y='test')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'is_instance_of'
```

## `is_subclass_of`

当输入值不是预期类型的子类时，会引发此错误：

```python
from pydantic import BaseModel, ValidationError


class Nested:
    x: str


class Model(BaseModel):
    y: type[Nested]


try:
    Model(y='test')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'is_subclass_of'
```

## `iterable_type`

当输入值作为 `Iterable` 无效时，会引发此错误：

```python
from collections.abc import Iterable

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    y: Iterable[str]


try:
    Model(y=123)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'iterable_type'
```

## `iteration_error`

当在迭代期间发生错误时，会引发此错误：

```python
from pydantic import BaseModel, ValidationError


def gen():
    yield 1
    raise RuntimeError('error')


class Model(BaseModel):
    x: list[int]


try:
    Model(x=gen())
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'iteration_error'
```

## `json_invalid`

当输入值不是有效的 JSON 时，会引发此错误：

```python
from pydantic import BaseModel, Json, ValidationError


class Model(BaseModel):
    x: Json


try:
    Model(x='test')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'json_invalid'
```

## `json_type`

当输入值的类型无法解析为 JSON 时，会引发此错误：

```python
from pydantic import BaseModel, Json, ValidationError


class Model(BaseModel):
    x: Json


try:
    Model(x=None)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'json_type'
```

## `less_than`

当输入值不小于字段的 `lt` 约束时，会引发此错误：

```python
from pydantic import BaseModel, Field, ValidationError


class Model(BaseModel):
    x: int = Field(lt=10)


try:
    Model(x=10)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'less_than'
```

## `less_than_equal`

当输入值不大于或等于字段的 `le` 约束时，会引发此错误：

```python
from pydantic import BaseModel, Field, ValidationError


class Model(BaseModel):
    x: int = Field(le=10)


try:
    Model(x=11)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'less_than_equal'
```

## `list_type`

当输入值的类型对于 `list` 字段无效时，会引发此错误：

```python
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: list[int]


try:
    Model(x=1)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'list_type'
```

## `literal_error`

当输入值不是预期的字面值之一时，会引发此错误：

```python
from typing import Literal

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: Literal['a', 'b']


Model(x='a')  # 正常

try:
    Model(x='c')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'literal_error'
```

## `mapping_type`

当由于调用 `Mapping` 协议的方法（例如 `.items()`）失败而在验证期间发生问题时，会引发此错误：

```python
from collections.abc import Mapping

from pydantic import BaseModel, ValidationError


class BadMapping(Mapping):
    def items(self):
        raise ValueError()

    def __iter__(self):
        raise ValueError()

    def __getitem__(self, key):
        raise ValueError()

    def __len__(self):
        return 1


class Model(BaseModel):
    x: dict[str, str]


try:
    Model(x=BadMapping())
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'mapping_type'
```

## `missing`

当输入值中缺少必需字段时，会引发此错误：

```python
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: str


try:
    Model()
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'missing'
```

## `missing_argument`

当未将必需的位置或关键字参数传递给使用 `validate_call` 装饰的函数时，会引发此错误：

```python
from pydantic import ValidationError, validate_call


@validate_call
def foo(a: int):
    return a


try:
    foo()
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'missing_argument'
```

## `missing_keyword_only_argument`

当未将必需的仅关键字参数传递给使用 `validate_call` 装饰的函数时，会引发此错误：

```python
from pydantic import ValidationError, validate_call


@validate_call
def foo(*, a: int):
    return a


try:
    foo()
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'missing_keyword_only_argument'
```

## `missing_positional_only_argument`

当未将必需的仅位置参数传递给使用 `validate_call` 装饰的函数时，会引发此错误：

```python
from pydantic import ValidationError, validate_call


@validate_call
def foo(a: int, /):
    return a


try:
    foo()
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'missing_positional_only_argument'
```

## `missing_sentinel_error`

当实验性的 `MISSING` 标记是唯一允许的值，并且在验证期间未提供时，会引发此错误：

```python
from pydantic import BaseModel, ValidationError
from pydantic.experimental.missing_sentinel import MISSING


class Model(BaseModel):
    f: MISSING


try:
    Model(f=1)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'missing_sentinel_error'
```

## `model_attributes_type`

当输入值不是有效的字典、模型实例或可以从中提取字段的实例时，会引发此错误：

```python
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    a: int
    b: int


# 简单地验证字典
print(Model.model_validate({'a': 1, 'b': 2}))
#> a=1 b=2


class CustomObj:
    def __init__(self, a, b):
        self.a = a
        self.b = b


# 使用 from_attributes 从对象中提取字段
print(Model.model_validate(CustomObj(3, 4), from_attributes=True))
#> a=3 b=4

try:
    Model.model_validate('not an object', from_attributes=True)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'model_attributes_type'
```

## `model_type`

当模型的输入不是模型实例或字典时，会引发此错误：

```python
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    a: int
    b: int


# 简单地验证字典
m = Model.model_validate({'a': 1, 'b': 2})
print(m)
#> a=1 b=2

# 验证现有的模型实例
print(Model.model_validate(m))
#> a=1 b=2

try:
    Model.model_validate('not an object')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'model_type'
```

## `multiple_argument_values`

当在调用使用 `validate_call` 装饰的函数时为单个参数提供多个值时，会引发此错误：

```python
from pydantic import ValidationError, validate_call


@validate_call
def foo(a: int):
    return a


try:
    foo(1, a=2)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'multiple_argument_values'
```

## `multiple_of`

当输入不是字段的 `multiple_of` 约束的倍数时，会引发此错误：

```python
from pydantic import BaseModel, Field, ValidationError


class Model(BaseModel):
    x: int = Field(multiple_of=5)


try:
    Model(x=1)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'multiple_of'
```

## `needs_python_object`

当尝试验证无法转换为 Python 对象的格式时，会引发此类错误。
例如，我们无法从 JSON 检查 `isinstance` 或 `issubclass`：

```python
import json

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    bm: type[BaseModel]


try:
    Model.model_validate_json(json.dumps({'bm': 'not a basemodel class'}))
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'needs_python_object'
```

## `no_such_attribute`

当配置中设置了 `validate_assignment=True`，并且您尝试为不是现有字段的属性赋值时，会引发此错误：

```python
from pydantic import ConfigDict, ValidationError, dataclasses


@dataclasses.dataclass(config=ConfigDict(validate_assignment=True))
class MyDataclass:
    x: int


m = MyDataclass(x=1)
try:
    m.y = 10
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'no_such_attribute'
```

## `none_required`

当输入值对于需要 `None` 的字段不是 `None` 时，会引发此错误：

```python
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: None


try:
    Model(x=1)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'none_required'
```

!!! note
    当您的模型中字段名称与其类型之间存在命名冲突时，您可能会遇到此错误。更具体地说，当该字段的默认值为 `None` 时，很可能会抛出此错误。

    例如，以下代码会产生 `none_required` 验证错误，因为字段 `int` 设置为默认值 `None`，并且与其类型名称完全相同，这会导致验证问题。

    ```python {test="skip"}
    from typing import Optional

    from pydantic import BaseModel


    class M1(BaseModel):
        int: Optional[int] = None


    m = M1(int=123)  # 错误
    ```

## `recursion_loop`

当检测到循环引用时，会引发此错误：

```python
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: list['Model']


d = {'x': []}
d['x'].append(d)
try:
    Model(**d)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'recursion_loop'
```

## `set_item_not_hashable`

当不可哈希的值针对 [`set`][] 或 [`frozenset`][] 进行验证时，会引发此错误：

```python
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: set[object]


class Unhashable:
    __hash__ = None


try:
    Model(x=[{'a': 'b'}, Unhashable()])
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'set_item_not_hashable'
    print(repr(exc.errors()[1]['type']))
    #> 'set_item_not_hashable'
```

## `set_type`

当值类型对于 `set` 字段无效时，会引发此错误：

```python
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: set[int]


try:
    Model(x='test')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'set_type'
```

## `string_pattern_mismatch`

当输入值与字段的 `pattern` 约束不匹配时，会引发此错误：

```python
from pydantic import BaseModel, Field, ValidationError


class Model(BaseModel):
    x: str = Field(pattern='test')


try:
    Model(x='1')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'string_pattern_mismatch'
```

## `string_sub_type`

当字段是严格的且值是 `str` 的严格子类型的实例时，会引发此错误：

```python
from enum import Enum

from pydantic import BaseModel, Field, ValidationError


class MyEnum(str, Enum):
    foo = 'foo'


class Model(BaseModel):
    x: str = Field(strict=True)


try:
    Model(x=MyEnum.foo)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'string_sub_type'
```

## `string_too_long`

当输入值是一个长度大于字段的 `max_length` 约束的字符串时，会引发此错误：

```python
from pydantic import BaseModel, Field, ValidationError


class Model(BaseModel):
    x: str = Field(max_length=3)


try:
    Model(x='test')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'string_too_long'
```

## `string_too_short`

当输入值是一个长度小于字段的 `min_length` 约束的字符串时，会引发此错误：

```python
from pydantic import BaseModel, Field, ValidationError


class Model(BaseModel):
    x: str = Field(min_length=3)


try:
    Model(x='t')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'string_too_short'
```

## `string_type`

当输入值的类型对于 `str` 字段无效时，会引发此错误：

```python
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: str


try:
    Model(x=1)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'string_type'
```

对于严格字段，当输入值不是 `str` 的实例时，也会引发此错误。

## `string_unicode`

当值无法解析为 Unicode 字符串时，会引发此错误：

```python
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: str


try:
    Model(x=b'\x81')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'string_unicode'
```

## `time_delta_parsing`

当输入值是无法为 `timedelta` 字段解析的字符串时，会引发此错误：

```python
from datetime import timedelta

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: timedelta


try:
    Model(x='t')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'time_delta_parsing'
```

## `time_delta_type`

当输入值的类型对于 `timedelta` 字段无效时，会引发此错误：

```python
from datetime import timedelta

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: timedelta


try:
    Model(x=None)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'time_delta_type'
```

对于严格字段，当输入值不是 `timedelta` 的实例时，也会引发此错误。

## `time_parsing`

当输入值是无法为 `time` 字段解析的字符串时，会引发此错误：

```python
from datetime import time

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: time


try:
    Model(x='25:20:30.400')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'time_parsing'
```

## `time_type`

当值类型对于 `time` 字段无效时，会引发此错误：

```python
from datetime import time

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: time


try:
    Model(x=None)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'time_type'
```

对于严格字段，当输入值不是 `time` 的实例时，也会引发此错误。

## `timezone_aware`

当为时区感知的 `datetime` 字段提供的 `datetime` 值没有时区信息时，会引发此错误：

```python
from datetime import datetime

from pydantic import AwareDatetime, BaseModel, ValidationError


class Model(BaseModel):
    x: AwareDatetime


try:
    Model(x=datetime.now())
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'timezone_aware'
```

## `timezone_naive`

当为时区无关的 `datetime` 字段提供的 `datetime` 值有时区信息时，会引发此错误：

```python
from datetime import datetime, timezone

from pydantic import BaseModel, NaiveDatetime, ValidationError


class Model(BaseModel):
    x: NaiveDatetime


try:
    Model(x=datetime.now(tz=timezone.utc))
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'timezone_naive'
```

## `too_long`

当输入值的长度大于字段的 `max_length` 约束时，会引发此错误：

```python
from pydantic import BaseModel, Field, ValidationError


class Model(BaseModel):
    x: list[int] = Field(max_length=3)


try:
    Model(x=[1, 2, 3, 4])
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'too_long'
```

## `too_short`

当值长度小于字段的 `min_length` 约束时，会引发此错误：

```python
from pydantic import BaseModel, Field, ValidationError


class Model(BaseModel):
    x: list[int] = Field(min_length=3)


try:
    Model(x=[1, 2])
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'too_short'
```

## `tuple_type`

当输入值的类型对于 `tuple` 字段无效时，会引发此错误：

```python
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: tuple[int]


try:
    Model(x=None)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'tuple_type'
```

对于严格字段，当输入值不是 `tuple` 的实例时，也会引发此错误。

## `unexpected_keyword_argument`

当您在调用使用 `validate_call` 装饰的函数时，为仅限位置的参数提供关键字值时，会引发此错误：

```python
from pydantic import ValidationError, validate_call


@validate_call
def foo(a: int, /):
    return a


try:
    foo(a=2)
except ValidationError as exc:
    print(repr(exc.errors()[1]['type']))
    #> 'unexpected_keyword_argument'
```

在使用 pydantic.dataclasses 和 `extra=forbid` 时也会引发此错误：

```python
from pydantic import TypeAdapter, ValidationError
from pydantic.dataclasses import dataclass


@dataclass(config={'extra': 'forbid'})
class Foo:
    bar: int


try:
    TypeAdapter(Foo).validate_python({'bar': 1, 'foobar': 2})
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'unexpected_keyword_argument'
```

## `unexpected_positional_argument`

当您在调用使用 `validate_call` 装饰的函数时，为仅限关键字的参数提供位置值时，会引发此错误：

```python
from pydantic import ValidationError, validate_call


@validate_call
def foo(*, a: int):
    return a


try:
    foo(2)
except ValidationError as exc:
    print(repr(exc.errors()[1]['type']))
    #> 'unexpected_positional_argument'
```

## `union_tag_invalid`

当输入的鉴别器不是预期值之一时，会引发此错误：

```python
from typing import Literal, Union

from pydantic import BaseModel, Field, ValidationError


class BlackCat(BaseModel):
    pet_type: Literal['blackcat']


class WhiteCat(BaseModel):
    pet_type: Literal['whitecat']


class Model(BaseModel):
    cat: Union[BlackCat, WhiteCat] = Field(discriminator='pet_type')


try:
    Model(cat={'pet_type': 'dog'})
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'union_tag_invalid'
```

## `union_tag_not_found`

当无法从输入中提取鉴别器值时，会引发此错误：

```python
from typing import Literal, Union

from pydantic import BaseModel, Field, ValidationError


class BlackCat(BaseModel):
    pet_type: Literal['blackcat']


class WhiteCat(BaseModel):
    pet_type: Literal['whitecat']


class Model(BaseModel):
    cat: Union[BlackCat, WhiteCat] = Field(discriminator='pet_type')


try:
    Model(cat={'name': 'blackcat'})
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'union_tag_not_found'
```

## `url_parsing`

当输入值无法解析为 URL 时，会引发此错误：

```python
from pydantic import AnyUrl, BaseModel, ValidationError


class Model(BaseModel):
    x: AnyUrl


try:
    Model(x='test')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'url_parsing'
```

## `url_scheme`

当 URL 方案对于字段的 URL 类型无效时，会引发此错误：

```python
from pydantic import BaseModel, HttpUrl, ValidationError


class Model(BaseModel):
    x: HttpUrl


try:
    Model(x='ftp://example.com')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'url_scheme'
```

## `url_syntax_violation`

当 URL 语法无效时，会引发此错误：

```python
from pydantic import BaseModel, Field, HttpUrl, ValidationError


class Model(BaseModel):
    x: HttpUrl = Field(strict=True)


try:
    Model(x='http:////example.com')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'url_syntax_violation'
```

## `url_too_long`

当 URL 长度大于 2083 时，会引发此错误：

```python
from pydantic import BaseModel, HttpUrl, ValidationError


class Model(BaseModel):
    x: HttpUrl


try:
    Model(x='x' * 2084)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'url_too_long'
```

## `url_type`

当输入值的类型对于 URL 字段无效时，会引发此错误：

```python
from pydantic import BaseModel, HttpUrl, ValidationError


class Model(BaseModel):
    x: HttpUrl


try:
    Model(x=None)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'url_type'
```

## `uuid_parsing`

当输入值的类型对于 UUID 字段无效时，会引发此错误：

```python
from uuid import UUID

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    u: UUID


try:
    Model(u='12345678-124-1234-1234-567812345678')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'uuid_parsing'
```

## `uuid_type`

当输入值的类型不是 UUID 字段的有效实例（str、bytes 或 UUID）时，会引发此错误：

```python
from uuid import UUID

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    u: UUID


try:
    Model(u=1234567812412341234567812345678)
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'uuid_type'
```

## `uuid_version`

当输入值的类型与 UUID 版本不匹配时，会引发此错误：

```python
from pydantic import UUID5, BaseModel, ValidationError


class Model(BaseModel):
    u: UUID5


try:
    Model(u='a6cc5730-2261-11ee-9c43-2eb5a363657c')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'uuid_version'
```

## `value_error`

当在验证过程中引发 `ValueError` 时，会引发此错误：

```python
from pydantic import BaseModel, ValidationError, field_validator


class Model(BaseModel):
    x: str

    @field_validator('x')
    @classmethod
    def repeat_b(cls, v):
        raise ValueError()


try:
    Model(x='test')
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
    #> 'value_error'
```