---
description: Pydantic 验证器完整指南：学习如何使用字段级别和模型级别的自定义验证器强制执行复杂数据约束。包括 After、Before、Plain 和 Wrap 四种字段验证器模式，以及模型验证器的使用方法。掌握验证器排序、错误处理、验证上下文和 JSON Schema 集成，确保数据完整性和类型安全。
---

除了 Pydantic 的[内置验证功能](./fields.md#field-constraints)之外，您还可以利用字段级别和模型级别的自定义验证器来强制执行更复杂的约束并确保数据的完整性。

!!! tip
    想要快速跳转到相关的验证器部分？

    <div class="grid cards" markdown>

    *   字段验证器

        ---

        * [字段 *after* 验证器](#field-after-validator)
        * [字段 *before* 验证器](#field-before-validator)
        * [字段 *plain* 验证器](#field-plain-validator)
        * [字段 *wrap* 验证器](#field-wrap-validator)

    *   模型验证器

        ---

        * [模型 *before* 验证器](#model-before-validator)
        * [模型 *after* 验证器](#model-after-validator)
        * [模型 *wrap* 验证器](#model-wrap-validator)

    </div>

## 字段验证器 {#field-validators}

??? api "API 文档"
    [`pydantic.functional_validators.WrapValidator`][pydantic.functional_validators.WrapValidator]<br>
    [`pydantic.functional_validators.PlainValidator`][pydantic.functional_validators.PlainValidator]<br>
    [`pydantic.functional_validators.BeforeValidator`][pydantic.functional_validators.BeforeValidator]<br>
    [`pydantic.functional_validators.AfterValidator`][pydantic.functional_validators.AfterValidator]<br>
    [`pydantic.functional_validators.field_validator`][pydantic.functional_validators.field_validator]<br>

在最简单的形式中，字段验证器是一个可调用对象，它接收要验证的值作为参数并**返回验证后的值**。该可调用对象可以执行特定条件的检查（参见[引发验证错误](#raising-validation-errors)）并对验证后的值进行更改（强制转换或修改）。

可以使用**四种**不同类型的验证器。它们都可以使用[注解模式](./fields.md#the-annotated-pattern)或使用 [`field_validator()`][pydantic.field_validator] 装饰器来定义，应用于[类方法][classmethod]：

* ***After* 验证器**：在Pydantic的内部验证之后运行。它们通常更类型安全，因此更容易实现。
{#field-after-validator}

    === "注解模式"

        这是一个执行验证检查并返回未更改值的验证器示例。

        ```python
        from typing import Annotated

        from pydantic import AfterValidator, BaseModel, ValidationError


        def is_even(value: int) -> int:
            if value % 2 == 1:
                raise ValueError(f'{value} is not an even number')
            return value  # (1)!


        class Model(BaseModel):
            number: Annotated[int, AfterValidator(is_even)]


        try:
            Model(number=1)
        except ValidationError as err:
            print(err)
            """
            1 validation error for Model
            number
              Value error, 1 is not an even number [type=value_error, input_value=1, input_type=int]
            """
        ```

        1. 注意返回验证后的值很重要。

    === "装饰器模式"

        这是一个执行验证检查并返回未更改值的验证器示例，
        这次使用 [`field_validator()`][pydantic.field_validator] 装饰器。

        ```python
        from pydantic import BaseModel, ValidationError, field_validator


        class Model(BaseModel):
            number: int

            @field_validator('number', mode='after')  # (1)!
            @classmethod
            def is_even(cls, value: int) -> int:
                if value % 2 == 1:
                    raise ValueError(f'{value} is not an even number')
                return value  # (2)!


        try:
            Model(number=1)
        except ValidationError as err:
            print(err)
            """
            1 validation error for Model
            number
              Value error, 1 is not an even number [type=value_error, input_value=1, input_type=int]
            """
        ```

        1. `'after'` 是装饰器的默认模式，可以省略。
        2. 注意返回验证后的值很重要。

    ??? example "修改值的示例"
        这是一个对验证后的值进行更改的验证器示例（不引发异常）。

        === "注解模式"

            ```python
            from typing import Annotated

            from pydantic import AfterValidator, BaseModel


            def double_number(value: int) -> int:
                return value * 2


            class Model(BaseModel):
                number: Annotated[int, AfterValidator(double_number)]


            print(Model(number=2))
            #> number=4
            ```

        === "装饰器模式"

            ```python
            from pydantic import BaseModel, field_validator


            class Model(BaseModel):
                number: int

                @field_validator('number', mode='after')  # (1)!
                @classmethod
                def double_number(cls, value: int) -> int:
                    return value * 2


            print(Model(number=2))
            #> number=4
            ```

            1. `'after'`是装饰器的默认模式，可以省略。

* ***Before* 验证器**：在 Pydantic 的内部解析和验证之前运行（例如，将 `str` 强制转换为 `int`）。
  这些比 [*after* 验证器](#field-after-validator)更灵活，但它们也必须处理原始输入，
  理论上可以是任何任意对象。如果您稍后在验证器函数中引发[验证错误](#raising-validation-errors)，
  还应避免直接修改值，因为如果使用[联合类型](./unions.md)，修改后的值可能会传递给其他验证器。
  {#field-before-validator}

    然后，Pydantic 会根据提供的类型注解验证从此可调用对象返回的值。

    === "注解模式"

        ```python
        from typing import Annotated, Any

        from pydantic import BaseModel, BeforeValidator, ValidationError


        def ensure_list(value: Any) -> Any:  # (1)!
            if not isinstance(value, list):  # (2)!
                return [value]
            else:
                return value


        class Model(BaseModel):
            numbers: Annotated[list[int], BeforeValidator(ensure_list)]


        print(Model(numbers=2))
        #> numbers=[2]
        try:
            Model(numbers='str')
        except ValidationError as err:
            print(err)  # (3)!
            """
            1 validation error for Model
            numbers.0
              Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='str', input_type=str]
            """
        ```

        1. 注意使用 [`Any`][typing.Any] 作为 `value` 的类型提示。*Before* 验证器接收原始输入，
           可以是任何东西。

        2. 注意您可能想要检查其他序列类型（例如元组），这些类型通常可以成功验证为`list`类型。
           *Before* 验证器给您更多灵活性，但您必须考虑所有可能的情况。

        3. Pydantic 仍然对 `int` 类型执行验证，无论我们的 `ensure_list` 验证器是否对原始输入类型进行了操作。

    === "装饰器模式"

        ```python
        from typing import Any

        from pydantic import BaseModel, ValidationError, field_validator


        class Model(BaseModel):
            numbers: list[int]

            @field_validator('numbers', mode='before')
            @classmethod
            def ensure_list(cls, value: Any) -> Any:  # (1)!
                if not isinstance(value, list):  # (2)!
                    return [value]
                else:
                    return value


        print(Model(numbers=2))
        #> numbers=[2]
        try:
            Model(numbers='str')
        except ValidationError as err:
            print(err)  # (3)!
            """
            1 validation error for Model
            numbers.0
              Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='str', input_type=str]
            """
        ```

        1. 注意使用 [`Any`][typing.Any] 作为 `value` 的类型提示。*Before* 验证器接收原始输入，
           可以是任何东西。

        2. 注意您可能想要检查其他序列类型（例如元组），这些类型通常可以成功验证为 `list` 类型。
           *Before* 验证器给您更多灵活性，但您必须考虑所有可能的情况。

        3. Pydantic 仍然对 `int` 类型执行验证，无论我们的 `ensure_list` 验证器是否对原始输入类型进行了操作。

* ***Plain* 验证器**：行为类似于 *before* 验证器，但它们在返回后**立即终止验证**，
  因此不会调用其他验证器，Pydantic 也不会对字段类型进行任何内部验证。
  {#field-plain-validator}

    === "注解模式"

        ```python
        from typing import Annotated, Any

        from pydantic import BaseModel, PlainValidator


        def val_number(value: Any) -> Any:
            if isinstance(value, int):
                return value * 2
            else:
                return value


        class Model(BaseModel):
            number: Annotated[int, PlainValidator(val_number)]


        print(Model(number=4))
        #> number=8
        print(Model(number='invalid'))  # (1)!
        #> number='invalid'
        ```

        1. 虽然 `'invalid'` 不应该验证为 `int` 类型，但 Pydantic 接受了输入。

    === "装饰器模式"

        ```python
        from typing import Any

        from pydantic import BaseModel, field_validator


        class Model(BaseModel):
            number: int

            @field_validator('number', mode='plain')
            @classmethod
            def val_number(cls, value: Any) -> Any:
                if isinstance(value, int):
                    return value * 2
                else:
                    return value


        print(Model(number=4))
        #> number=8
        print(Model(number='invalid'))  # (1)!
        #> number='invalid'
        ```

        1. 虽然 `'invalid'` 不应该验证为 `int` 类型，但 Pydantic 接受了输入。

* ***Wrap* 验证器**：是所有验证器中最灵活的。您可以在 Pydantic 和其他验证器处理输入之前或之后运行代码，
  或者通过提前返回值或引发错误来立即终止验证。
  {#field-wrap-validator}

    此类验证器必须定义**强制**的额外参数 `handler`：一个接收要验证的值作为参数的可调用对象。
    在内部，此处理程序将把值的验证委托给 Pydantic。您可以自由地将对处理程序的调用包装在
    [`try..except`][handling exceptions] 块中，或者根本不调用它。

    [handling exceptions]: https://docs.python.org/3/tutorial/errors.html#handling-exceptions

    === "注解模式"

        ```python {lint="skip"}
        from typing import Any

        from typing import Annotated

        from pydantic import BaseModel, Field, ValidationError, ValidatorFunctionWrapHandler, WrapValidator


        def truncate(value: Any, handler: ValidatorFunctionWrapHandler) -> str:
            try:
                return handler(value)
            except ValidationError as err:
                if err.errors()[0]['type'] == 'string_too_long':
                    return handler(value[:5])
                else:
                    raise


        class Model(BaseModel):
            my_string: Annotated[str, Field(max_length=5), WrapValidator(truncate)]


        print(Model(my_string='abcde'))
        #> my_string='abcde'
        print(Model(my_string='abcdef'))
        #> my_string='abcde'
        ```

    === "装饰器模式"

        ```python {lint="skip"}
        from typing import Any

        from typing import Annotated

        from pydantic import BaseModel, Field, ValidationError, ValidatorFunctionWrapHandler, field_validator


        class Model(BaseModel):
            my_string: Annotated[str, Field(max_length=5)]

            @field_validator('my_string', mode='wrap')
            @classmethod
            def truncate(cls, value: Any, handler: ValidatorFunctionWrapHandler) -> str:
                try:
                    return handler(value)
                except ValidationError as err:
                    if err.errors()[0]['type'] == 'string_too_long':
                        return handler(value[:5])
                    else:
                        raise


        print(Model(my_string='abcde'))
        #> my_string='abcde'
        print(Model(my_string='abcdef'))
        #> my_string='abcde'
        ```

!!! note "默认值的验证"
    如[字段文档](./fields.md#validate-default-values)中所述，字段的默认值
    *不会*被验证，除非配置为这样做，因此自定义验证器也不会被应用。

### 选择哪种验证器模式

虽然两种方法可以实现相同的功能，但每种模式都提供不同的好处。

#### 使用注解模式 {#using-the-annotated-pattern}

使用[注解模式](./fields.md#the-annotated-pattern)的一个关键好处是使验证器可重用：

```python
from typing import Annotated

from pydantic import AfterValidator, BaseModel


def is_even(value: int) -> int:
    if value % 2 == 1:
        raise ValueError(f'{value} is not an even number')
    return value


EvenNumber = Annotated[int, AfterValidator(is_even)]


class Model1(BaseModel):
    my_number: EvenNumber


class Model2(BaseModel):
    other_number: Annotated[EvenNumber, AfterValidator(lambda v: v + 2)]


class Model3(BaseModel):
    list_of_even_numbers: list[EvenNumber]  # (1)!
```

1. 如[注解模式](./fields.md#the-annotated-pattern)文档中所述，我们还可以对注解的特定部分使用验证器（在这种情况下，验证应用于列表项，而不是整个列表）。

通过查看字段注解，也更容易理解哪些验证器应用于类型。

#### 使用装饰器模式 {#using-the-decorator-pattern}

使用  [`field_validator()`][pydantic.field_validator] 装饰器的一个关键好处是将函数应用于多个字段：

```python
from pydantic import BaseModel, field_validator


class Model(BaseModel):
    f1: str
    f2: str

    @field_validator('f1', 'f2', mode='before')
    @classmethod
    def capitalize(cls, value: str) -> str:
        return value.capitalize()
```

以下是关于装饰器用法的一些额外说明：

* 如果您希望验证器应用于所有字段（包括子类中定义的字段），可以传递 `'*'` 作为字段名称参数。
* 默认情况下，装饰器将确保提供的字段名称在模型上定义。如果您想在类创建期间禁用此检查，可以通过将 `False` 传递给 `check_fields` 参数来实现。当字段验证器在基类上定义，并且期望字段存在于子类上时，这很有用。

## 模型验证器 {#model-validators}

??? api "API 文档"
    [`pydantic.functional_validators.model_validator`][pydantic.functional_validators.model_validator]<br>

也可以使用 [`model_validator()`][pydantic.model_validator] 装饰器对整个模型的数据执行验证。

可以使用**三种**不同类型的模型验证器：

* ***After* 验证器**：在整个模型验证之后运行。因此，它们被定义为*实例*方法，
  可以看作是后初始化钩子。重要说明：应返回验证后的实例。
  {#model-after-validator}

    ```python
    from typing_extensions import Self

    from pydantic import BaseModel, model_validator


    class UserModel(BaseModel):
        username: str
        password: str
        password_repeat: str

        @model_validator(mode='after')
        def check_passwords_match(self) -> Self:
            if self.password != self.password_repeat:
                raise ValueError('Passwords do not match')
            return self
    ```

* ***Before* 验证器**：在模型实例化之前运行。这些比 *after* 验证器更灵活，
  但它们也必须处理原始输入，理论上可以是任何任意对象。如果您稍后在验证器函数中
  引发[验证错误](#raising-validation-errors)，还应避免直接修改值，因为如果使用
  [联合类型](./unions.md)，修改后的值可能会传递给其他验证器。
  {#model-before-validator}

    ```python
    from typing import Any

    from pydantic import BaseModel, model_validator


    class UserModel(BaseModel):
        username: str

        @model_validator(mode='before')
        @classmethod
        def check_card_number_not_present(cls, data: Any) -> Any:  # (1)!
            if isinstance(data, dict):  # (2)!
                if 'card_number' in data:
                    raise ValueError("'card_number' should not be included")
            return data
    ```

    1. 注意使用 [`Any`][typing.Any] 作为 `data` 的类型提示。*Before* 验证器接收原始输入，
       可以是任何东西。
    2. 大多数情况下，输入数据将是一个字典（例如，当调用 `UserModel(username='...')` 时）。然而，
       情况并非总是如此。例如，如果设置了 [`from_attributes`][pydantic.ConfigDict.from_attributes]
       配置值，您可能会收到一个任意类实例作为 `data` 参数。

* ***Wrap* 验证器**：是所有验证器中最灵活的。您可以在Pydantic和其他验证器处理输入数据之前或之后运行代码，
  或者通过提前返回数据或引发错误来立即终止验证。
  {#model-wrap-validator}

    ```python {lint="skip"}
    import logging
    from typing import Any

    from typing_extensions import Self

    from pydantic import BaseModel, ModelWrapValidatorHandler, ValidationError, model_validator


    class UserModel(BaseModel):
        username: str

        @model_validator(mode='wrap')
        @classmethod
        def log_failed_validation(cls, data: Any, handler: ModelWrapValidatorHandler[Self]) -> Self:
            try:
                return handler(data)
            except ValidationError:
                logging.error('Model %s failed to validate with data %s', cls, data)
                raise
    ```

!!! note "关于继承"
    在基类中定义的模型验证器将在子类实例验证期间被调用。

    在子类中重写模型验证器将覆盖基类的验证器，因此只会调用该验证器的子类版本。

## 引发验证错误 {#raising-validation-errors}

要引发验证错误，可以使用三种类型的异常：

* [`ValueError`][]：这是在验证器内部引发的最常见异常。
* [`AssertionError`][]：使用 [`assert`][] 语句也有效，但请注意当 Python 使用 [-O][] 优化标志运行时，这些语句会被跳过。
* [`PydanticCustomError`][pydantic_core.PydanticCustomError]：稍微冗长一些，但提供了额外的灵活性：

    ```python
    from pydantic_core import PydanticCustomError

    from pydantic import BaseModel, ValidationError, field_validator


    class Model(BaseModel):
        x: int

        @field_validator('x', mode='after')
        @classmethod
        def validate_x(cls, v: int) -> int:
            if v % 42 == 0:
                raise PydanticCustomError(
                    'the_answer_error',
                    '{number} is the answer!',
                    {'number': v},
                )
            return v


    try:
        Model(x=42 * 2)
    except ValidationError as e:
        print(e)
        """
        1 validation error for Model
        x
          84 is the answer! [type=the_answer_error, input_value=84, input_type=int]
        """
    ```

## 验证信息

字段和模型验证器的可调用对象（在所有模式下）都可以选择性地接受一个额外的
[`ValidationInfo`][pydantic.ValidationInfo] 参数，提供有用的额外信息，例如：

* [已验证的数据](#validation-data)
* [用户定义的上下文](#validation-context)
* 当前验证模式：`'python'` 或 `'json'`（参见 [`mode`][pydantic.ValidationInfo.mode] 属性）
* 当前字段名称，如果使用[字段验证器](#field-validators)（参见 [`field_name`][pydantic.ValidationInfo.field_name] 属性）。

### 验证数据 {#validation-data}

对于字段验证器，可以使用 [`data`][pydantic.ValidationInfo.data] 属性访问已验证的数据。
以下是一个可以作为   [*after*    模型验证器](#model-after-validator)示例替代方案的示例：

```python
from pydantic import BaseModel, ValidationInfo, field_validator


class UserModel(BaseModel):
    password: str
    password_repeat: str
    username: str

    @field_validator('password_repeat', mode='after')
    @classmethod
    def check_passwords_match(cls, value: str, info: ValidationInfo) -> str:
        if value != info.data['password']:
            raise ValueError('Passwords do not match')
        return value
```

!!! warning
    由于验证是按照[字段定义的顺序](./models.md#field-ordering)执行的，您必须
    确保不访问尚未验证的字段。例如，在上面的代码中，
    `username` 的验证值尚不可用，因为它是在 `password_repeat` *之后* 定义的。

对于[模型验证器](#model-validators)，[`data`][pydantic.ValidationInfo.data] 属性为 `None`。

### 验证上下文 {#validation-context}

您可以向[验证方法](./models.md#validating-data)传递一个上下文对象，该对象可以在验证器函数内部
通过 [`context`][pydantic.ValidationInfo.context] 属性访问：

```python
from pydantic import BaseModel, ValidationInfo, field_validator


class Model(BaseModel):
    text: str

    @field_validator('text', mode='after')
    @classmethod
    def remove_stopwords(cls, v: str, info: ValidationInfo) -> str:
        if isinstance(info.context, dict):
            stopwords = info.context.get('stopwords', set())
            v = ' '.join(w for w in v.split() if w.lower() not in stopwords)
        return v


data = {'text': 'This is an example document'}
print(Model.model_validate(data))  # 无上下文
#> text='This is an example document'
print(Model.model_validate(data, context={'stopwords': ['this', 'is', 'an']}))
#> text='example document'
```

类似地，您可以[为序列化使用上下文](../concepts/serialization.md#serialization-context)。

??? note "在直接实例化模型时提供上下文"
    目前无法在直接实例化模型时提供上下文
    （即调用 `Model(...)` 时）。您可以通过使用
    [`ContextVar`][contextvars.ContextVar] 和自定义 `__init__` 方法来变通解决：

    ```python
    from __future__ import annotations

    from collections.abc import Generator
    from contextlib import contextmanager
    from contextvars import ContextVar
    from typing import Any

    from pydantic import BaseModel, ValidationInfo, field_validator

    _init_context_var = ContextVar('_init_context_var', default=None)


    @contextmanager
    def init_context(value: dict[str, Any]) -> Generator[None]:
        token = _init_context_var.set(value)
        try:
            yield
        finally:
            _init_context_var.reset(token)


    class Model(BaseModel):
        my_number: int

        def __init__(self, /, **data: Any) -> None:
            self.__pydantic_validator__.validate_python(
                data,
                self_instance=self,
                context=_init_context_var.get(),
            )

        @field_validator('my_number')
        @classmethod
        def multiply_with_context(cls, value: int, info: ValidationInfo) -> int:
            if isinstance(info.context, dict):
                multiplier = info.context.get('multiplier', 1)
                value = value * multiplier
            return value


    print(Model(my_number=2))
    #> my_number=2

    with init_context({'multiplier': 3}):
        print(Model(my_number=2))
        #> my_number=6

    print(Model(my_number=2))
    #> my_number=2
    ```

## 验证器排序

使用[注解模式](#using-the-annotated-pattern)时，验证器的应用顺序定义如下：
[*before*](#field-before-validator) 和 [*wrap*](#field-wrap-validator) 验证器从右到左运行，
然后 [*after*](#field-after-validator) 验证器从左到右运行：

```python {lint="skip" test="skip"}
from pydantic import AfterValidator, BaseModel, BeforeValidator, WrapValidator


class Model(BaseModel):
    name: Annotated[
        str,
        AfterValidator(runs_3rd),
        AfterValidator(runs_4th),
        BeforeValidator(runs_2nd),
        WrapValidator(runs_1st),
    ]
```

在内部，使用[装饰器模式](#using-the-decorator-pattern)定义的验证器会被转换为其注解形式的对应物，
并添加到字段现有元数据的最后。这意味着相同的排序逻辑适用。

## 特殊类型

Pydantic 提供了一些特殊实用程序，可用于自定义验证。

* [`InstanceOf`][pydantic.functional_validators.InstanceOf] 可用于验证值是否为给定类的实例。

    ```python
    from pydantic import BaseModel, InstanceOf, ValidationError


    class Fruit:
        def __repr__(self):
            return self.__class__.__name__


    class Banana(Fruit): ...


    class Apple(Fruit): ...


    class Basket(BaseModel):
        fruits: list[InstanceOf[Fruit]]


    print(Basket(fruits=[Banana(), Apple()]))
    #> fruits=[Banana, Apple]
    try:
        Basket(fruits=[Banana(), 'Apple'])
    except ValidationError as e:
        print(e)
        """
        1 validation error for Basket
        fruits.1
          Input should be an instance of Fruit [type=is_instance_of, input_value='Apple', input_type=str]
        """
    ```

* [`SkipValidation`][pydantic.functional_validators.SkipValidation] 可用于跳过字段的验证。

    ```python
    from pydantic import BaseModel, SkipValidation


    class Model(BaseModel):
        names: list[SkipValidation[str]]


    m = Model(names=['foo', 'bar'])
    print(m)
    #> names=['foo', 'bar']

    m = Model(names=['foo', 123])  # (1)!
    print(m)
    #> names=['foo', 123]
    ```

    1. 注意第二个项目的验证被跳过了。如果类型错误，它将在序列化期间发出警告。

* [`ValidateAs`][pydantic.functional_validators.ValidateAs] 可用于从 Pydantic 原生支持的类型验证自定义类型。
  这在处理具有多个字段的自定义类型时特别有用。

    ```python {lint="skip"}
    from typing import Annotated

    from pydantic import BaseModel, TypeAdapter, ValidateAs

    class MyCls:
        def __init__(self, a: int) -> None:
            self.a = a

        def __repr__(self) -> str:
            return f"MyCls(a={self.a})"

    class ValModel(BaseModel):
        a: int


    ta = TypeAdapter(
        Annotated[MyCls, ValidateAs(ValModel, lambda v: MyCls(a=v.a))]
    )

    print(ta.validate_python({'a': 1}))
    #> MyCls(a=1)
    ```

* [`PydanticUseDefault`][pydantic_core.PydanticUseDefault] 可用于通知 Pydantic 应使用默认值。

    ```python
    from typing import Annotated, Any

    from pydantic_core import PydanticUseDefault

    from pydantic import BaseModel, BeforeValidator


    def default_if_none(value: Any) -> Any:
        if value is None:
            raise PydanticUseDefault()
        return value


    class Model(BaseModel):
        name: Annotated[str, BeforeValidator(default_if_none)] = 'default_name'


    print(Model(name=None))
    #> name='default_name'
    ```

## JSON Schema 和字段验证器 {#json-schema-and-field-validators}

使用 [*before*](#field-before-validator)、[*plain*](#field-plain-validator) 或 [*wrap*](#field-wrap-validator)
字段验证器时，接受的输入类型可能与字段注解不同。

考虑以下示例：

```python
from typing import Any

from pydantic import BaseModel, field_validator


class Model(BaseModel):
    value: str

    @field_validator('value', mode='before')
    @classmethod
    def cast_ints(cls, value: Any) -> Any:
        if isinstance(value, int):
            return str(value)
        else:
            return value


print(Model(value='a'))
#> value='a'
print(Model(value=1))
#> value='1'
```

虽然 `value` 的类型提示是 `str`，但 `cast_ints` 验证器也允许整数。要指定正确的输入类型，
可以提供 `json_schema_input_type` 参数：

```python
from typing import Any, Union

from pydantic import BaseModel, field_validator


class Model(BaseModel):
    value: str

    @field_validator(
        'value', mode='before', json_schema_input_type=Union[int, str]
    )
    @classmethod
    def cast_ints(cls, value: Any) -> Any:
        if isinstance(value, int):
            return str(value)
        else:
            return value


print(Model.model_json_schema()['properties']['value'])
#> {'anyOf': [{'type': 'integer'}, {'type': 'string'}], 'title': 'Value'}
```

为方便起见，如果未提供参数，Pydantic 将使用字段类型（除非您使用的是 [*plain*](#field-plain-validator) 验证器，
在这种情况下，`json_schema_input_type`默认为 [`Any`][typing.Any]，因为字段类型被完全丢弃）。
