---
description: Pydantic validate_call 装饰器教程：学习如何使用函数参数验证、类型注解、字段配置和异步函数支持，提升 Python 代码的健壮性和类型安全性。
---

??? api "API 文档"
    [`pydantic.validate_call_decorator.validate_call`][pydantic.validate_call_decorator.validate_call]<br>

[`validate_call()`][pydantic.validate_call] 装饰器允许在函数被调用之前，使用函数的注解来解析和验证传递给函数的参数。

虽然在底层这使用了与模型创建和初始化相同的方法（详见[验证器](validators.md)），但它提供了一种极其简单的方式来为你的代码应用验证，且样板代码最少。

使用示例：

```python
from pydantic import ValidationError, validate_call


@validate_call
def repeat(s: str, count: int, *, separator: bytes = b'') -> bytes:
    b = s.encode()
    return separator.join(b for _ in range(count))


a = repeat('hello', 3)
print(a)
#> b'hellohellohello'

b = repeat('x', '4', separator=b' ')
print(b)
#> b'x x x x'

try:
    c = repeat('hello', 'wrong')
except ValidationError as exc:
    print(exc)
    """
    1 validation error for repeat
    1
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='wrong', input_type=str]
    """
```

## 参数类型

参数类型是从函数的类型注解中推断出来的，如果没有注解，则推断为 [`Any`][typing.Any]。[类型](types.md)中列出的所有类型都可以被验证，包括 Pydantic 模型和[自定义类型](types.md#custom-types)。
与 Pydantic 的其他部分一样，类型在传递给实际函数之前默认会被装饰器强制转换：

```python
from datetime import date

from pydantic import validate_call


@validate_call
def greater_than(d1: date, d2: date, *, include_equal=False) -> date:  # (1)!
    if include_equal:
        return d1 >= d2
    else:
        return d1 > d2


d1 = '2000-01-01'  # (2)!
d2 = date(2001, 1, 1)
greater_than(d1, d2, include_equal=True)
```

1. 因为 `include_equal` 没有类型注解，它将被推断为 [`Any`][typing.Any]。
2. 虽然 `d1` 是一个字符串，但它将被转换为 [`date`][datetime.date] 对象。

像这样的类型强制转换可能非常有帮助，但也可能令人困惑或不希望发生（参见[模型数据转换](models.md#data-conversion)）。可以通过使用[自定义配置](#custom-configuration)来启用[严格模式](strict_mode.md)。

!!! note "验证返回值"
    默认情况下，函数的返回值**不会**被验证。要验证返回值，可以将装饰器的 `validate_return` 参数设置为 `True`。

## 函数签名

[`validate_call()`][pydantic.validate_call] 装饰器设计用于处理使用所有可能的[参数配置][parameter]及其所有组合的函数：

* 带或不带默认值的位置参数或关键字参数
* 仅关键字参数：`*,` 之后的参数
* 仅位置参数：`, /` 之前的参数
* 通过 `*` 定义的变量位置参数（通常是 `*args`）
* 通过 `**` 定义的变量关键字参数（通常是 `**kwargs`）

??? example

    ```python
    from pydantic import validate_call


    @validate_call
    def pos_or_kw(a: int, b: int = 2) -> str:
        return f'a={a} b={b}'


    print(pos_or_kw(1, b=3))
    #> a=1 b=3


    @validate_call
    def kw_only(*, a: int, b: int = 2) -> str:
        return f'a={a} b={b}'


    print(kw_only(a=1))
    #> a=1 b=2
    print(kw_only(a=1, b=3))
    #> a=1 b=3


    @validate_call
    def pos_only(a: int, b: int = 2, /) -> str:
        return f'a={a} b={b}'


    print(pos_only(1))
    #> a=1 b=2


    @validate_call
    def var_args(*args: int) -> str:
        return str(args)


    print(var_args(1))
    #> (1,)
    print(var_args(1, 2, 3))
    #> (1, 2, 3)


    @validate_call
    def var_kwargs(**kwargs: int) -> str:
        return str(kwargs)


    print(var_kwargs(a=1))
    #> {'a': 1}
    print(var_kwargs(a=1, b=2))
    #> {'a': 1, 'b': 2}


    @validate_call
    def armageddon(
        a: int,
        /,
        b: int,
        *c: int,
        d: int,
        e: int = None,
        **f: int,
    ) -> str:
        return f'a={a} b={b} c={c} d={d} e={e} f={f}'


    print(armageddon(1, 2, d=3))
    #> a=1 b=2 c=() d=3 e=None f={}
    print(armageddon(1, 2, 3, 4, 5, 6, d=8, e=9, f=10, spam=11))
    #> a=1 b=2 c=(3, 4, 5, 6) d=8 e=9 f={'f': 10, 'spam': 11}
    ```

!!! note "关键字参数的 [`Unpack`][typing.Unpack]"
    [`Unpack`][typing.Unpack] 和类型化字典可用于注解函数的变量关键字参数：

    ```python
    from typing_extensions import TypedDict, Unpack

    from pydantic import validate_call


    class Point(TypedDict):
        x: int
        y: int


    @validate_call
    def add_coords(**kwargs: Unpack[Point]) -> int:
        return kwargs['x'] + kwargs['y']


    add_coords(x=1, y=2)
    ```

    有关参考，请参阅[相关规范部分]和 [PEP 692]。

    [相关规范部分]: https://typing.readthedocs.io/en/latest/spec/callables.html#unpack-for-keyword-arguments
    [PEP 692]: https://peps.python.org/pep-0692/

## 使用 [`Field()`][pydantic.Field] 函数描述函数参数

[`Field()` 函数](fields.md)也可以与装饰器一起使用，以提供有关字段和验证的额外信息。如果你不使用 `default` 或 `default_factory` 参数，建议使用[注解模式](./fields.md#the-annotated-pattern)（以便类型检查器推断参数是必需的）。否则，[`Field()`][pydantic.Field] 函数可以用作默认值（再次，以欺骗类型检查器认为为该参数提供了默认值）。

```python
from typing import Annotated

from pydantic import Field, ValidationError, validate_call


@validate_call
def how_many(num: Annotated[int, Field(gt=10)]):
    return num


try:
    how_many(1)
except ValidationError as e:
    print(e)
    """
    1 validation error for how_many
    0
      Input should be greater than 10 [type=greater_than, input_value=1, input_type=int]
    """


@validate_call
def return_value(value: str = Field(default='default value')):
    return value


print(return_value())
#> default value
```

[别名](fields.md#field-aliases)可以正常与装饰器一起使用：

```python
from typing import Annotated

from pydantic import Field, validate_call


@validate_call
def how_many(num: Annotated[int, Field(gt=10, alias='number')]):
    return num


how_many(number=42)
```

## 访问原始函数 {#accessing-the-original-function}

被装饰的原始函数仍然可以通过使用 `raw_function` 属性来访问。
这在某些情况下很有用，如果你信任输入参数并希望以最有效的方式调用函数（参见下面的[性能说明](#performance)）：

```python
from pydantic import validate_call


@validate_call
def repeat(s: str, count: int, *, separator: bytes = b'') -> bytes:
    b = s.encode()
    return separator.join(b for _ in range(count))


a = repeat('hello', 3)
print(a)
#> b'hellohellohello'

b = repeat.raw_function('good bye', 2, separator=b', ')
print(b)
#> b'good bye, good bye'
```

## 异步函数

[`validate_call()`][pydantic.validate_call] 也可以用于异步函数：

```python
class Connection:
    async def execute(self, sql, *args):
        return 'testing@example.com'


conn = Connection()
# ignore-above
import asyncio

from pydantic import PositiveInt, ValidationError, validate_call


@validate_call
async def get_user_email(user_id: PositiveInt):
    # `conn` is some fictional connection to a database
    email = await conn.execute('select email from users where id=$1', user_id)
    if email is None:
        raise RuntimeError('user not found')
    else:
        return email


async def main():
    email = await get_user_email(123)
    print(email)
    #> testing@example.com
    try:
        await get_user_email(-4)
    except ValidationError as exc:
        print(exc.errors())
        """
        [
            {
                'type': 'greater_than',
                'loc': (0,),
                'msg': 'Input should be greater than 0',
                'input': -4,
                'ctx': {'gt': 0},
                'url': 'https://errors.pydantic.dev/2/v/greater_than',
            }
        ]
        """


asyncio.run(main())
# requires: `conn.execute()` that will return `'testing@example.com'`
```

## 与类型检查器的兼容性

由于 [`validate_call()`][pydantic.validate_call] 装饰器保留了被装饰函数的签名，它应该与类型检查器（如 mypy 和 pyright）兼容。然而，由于当前 Python 类型系统的限制，[`raw_function`](#accessing-the-original-function) 或其他属性将不会被识别，你需要使用（通常使用 `# type: ignore` 注释）来抑制错误。

## 自定义配置 {#custom-configuration}

与 Pydantic 模型类似，装饰器的 `config` 参数可用于指定自定义配置：

```python
from pydantic import ConfigDict, ValidationError, validate_call


class Foobar:
    def __init__(self, v: str):
        self.v = v

    def __add__(self, other: 'Foobar') -> str:
        return f'{self} + {other}'

    def __str__(self) -> str:
        return f'Foobar({self.v})'


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def add_foobars(a: Foobar, b: Foobar):
    return a + b


c = add_foobars(Foobar('a'), Foobar('b'))
print(c)
#> Foobar(a) + Foobar(b)

try:
    add_foobars(1, 2)
except ValidationError as e:
    print(e)
    """
    2 validation errors for add_foobars
    0
      Input should be an instance of Foobar [type=is_instance_of, input_value=1, input_type=int]
    1
      Input should be an instance of Foobar [type=is_instance_of, input_value=2, input_type=int]
    """
```

## 扩展 — 在调用函数之前验证参数

在某些情况下，将函数参数的验证与函数调用本身分开可能会很有帮助。
当特定函数成本高/耗时较长时，这可能很有用。

以下是一个你可以用于该模式的变通方法示例：

```python
from pydantic import validate_call


@validate_call
def validate_foo(a: int, b: int):
    def foo():
        return a + b

    return foo


foo = validate_foo(a=1, b=2)
print(foo())
#> 3
```

## 限制

### 验证异常

目前，在验证失败时，会引发标准的 Pydantic [`ValidationError`][pydantic_core.ValidationError]
（详见[模型错误处理](models.md#error-handling)）。对于缺少必需参数的情况也是如此，
而 Python 通常会引发 [`TypeError`][]。

### 性能 {#performance}

我们已经付出了巨大努力，使 Pydantic 尽可能高性能。虽然对被装饰函数的检查只执行一次，
但与使用原始函数相比，调用函数时仍然会有性能影响。

在许多情况下，这几乎没有或没有明显的影响。但是，请注意
[`validate_call()`][pydantic.validate_call] 并不是强类型语言中函数定义的等价物或替代品，
而且永远不会是。