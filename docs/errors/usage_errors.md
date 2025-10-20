---
subtitle: 使用错误
description: Pydantic 使用错误详解：全面介绍开发人员在使用 Pydantic 数据验证库时可能遇到的常见错误类型及解决方案，包括类未完全定义、自定义 JSON Schema、鉴别器错误、验证器配置错误等，帮助开发者快速定位并修复 Pydantic 相关问题。
---

Pydantic 尝试提供有用的错误信息。以下部分详细介绍了开发人员在使用 Pydantic 时可能遇到的常见错误，以及解决错误条件的建议。

## 类未完全定义 {#class-not-fully-defined}

当在 pydantic 验证类型的注解中引用的类型（例如 `BaseModel` 的子类或 pydantic `dataclass`）未定义时，会引发此错误：

```python
from typing import ForwardRef

from pydantic import BaseModel, PydanticUserError

UndefinedType = ForwardRef('UndefinedType')


class Foobar(BaseModel):
    a: UndefinedType


try:
    Foobar(a=1)
except PydanticUserError as exc_info:
    assert exc_info.code == 'class-not-fully-defined'
```

或者当类型在使用后才定义时：

```python
from typing import Optional

from pydantic import BaseModel, PydanticUserError


class Foo(BaseModel):
    a: Optional['Bar'] = None


try:
    # 这不起作用，请查看引发的错误
    foo = Foo(a={'b': {'a': None}})
except PydanticUserError as exc_info:
    assert exc_info.code == 'class-not-fully-defined'


class Bar(BaseModel):
    b: 'Foo'


# 不过，这样可以工作
foo = Foo(a={'b': {'a': None}})
```

对于 BaseModel 子类，可以通过定义类型然后调用 `.model_rebuild()` 来修复：

```python
from typing import Optional

from pydantic import BaseModel


class Foo(BaseModel):
    a: Optional['Bar'] = None


class Bar(BaseModel):
    b: 'Foo'


Foo.model_rebuild()

foo = Foo(a={'b': {'a': None}})
```

在其他情况下，错误消息应指示如何使用适当的类型定义重新构建类。

## 自定义 JSON Schema {#custom-json-schema}

`__modify_schema__` 方法在 V2 中不再受支持。您应该改用 `__get_pydantic_json_schema__` 方法。

`__modify_schema__` 过去接收一个表示 JSON schema 的参数。请参见下面的示例：

```python {title="旧方式"}
from pydantic import BaseModel, PydanticUserError

try:

    class Model(BaseModel):
        @classmethod
        def __modify_schema__(cls, field_schema):
            field_schema.update(examples=['example'])

except PydanticUserError as exc_info:
    assert exc_info.code == 'custom-json-schema'
```

新的 `__get_pydantic_json_schema__` 方法接收两个参数：第一个是表示为 `CoreSchema` 的字典，
第二个是一个可调用的 `handler`，它接收一个 `CoreSchema` 作为参数，并返回一个 JSON schema。请参见下面的示例：

```python {title="新方式"}
from typing import Any

from pydantic_core import CoreSchema

from pydantic import BaseModel, GetJsonSchemaHandler


class Model(BaseModel):
    @classmethod
    def __get_pydantic_json_schema__(
        cls, core_schema: CoreSchema, handler: GetJsonSchemaHandler
    ) -> dict[str, Any]:
        json_schema = super().__get_pydantic_json_schema__(core_schema, handler)
        json_schema = handler.resolve_ref_schema(json_schema)
        json_schema.update(examples=['example'])
        return json_schema


print(Model.model_json_schema())
"""
{'examples': ['example'], 'properties': {}, 'title': 'Model', 'type': 'object'}
"""
```

## 装饰器应用于缺失的字段 {#decorator-missing-field}

当您使用无效的字段定义装饰器时，会引发此错误。

```python
from typing import Any

from pydantic import BaseModel, PydanticUserError, field_validator

try:

    class Model(BaseModel):
        a: str

        @field_validator('b')
        def check_b(cls, v: Any):
            return v

except PydanticUserError as exc_info:
    assert exc_info.code == 'decorator-missing-field'
```

如果您从模型继承并且有意这样做，可以使用 `check_fields=False`。

```python
from typing import Any

from pydantic import BaseModel, create_model, field_validator


class Model(BaseModel):
    @field_validator('a', check_fields=False)
    def check_a(cls, v: Any):
        return v


model = create_model('FooModel', a=(str, 'cake'), __base__=Model)
```

## 鉴别器无字段 {#discriminator-no-field}

当鉴别联合中的模型未定义鉴别器字段时，会引发此错误。

```python
from typing import Literal, Union

from pydantic import BaseModel, Field, PydanticUserError


class Cat(BaseModel):
    c: str


class Dog(BaseModel):
    pet_type: Literal['dog']
    d: str


try:

    class Model(BaseModel):
        pet: Union[Cat, Dog] = Field(discriminator='pet_type')
        number: int

except PydanticUserError as exc_info:
    assert exc_info.code == 'discriminator-no-field'
```

## 鉴别器别名类型 {#discriminator-alias-type}

当您在鉴别器字段上定义非字符串别名时，会引发此错误。

```python
from typing import Literal, Union

from pydantic import AliasChoices, BaseModel, Field, PydanticUserError


class Cat(BaseModel):
    pet_type: Literal['cat'] = Field(
        validation_alias=AliasChoices('Pet', 'PET')
    )
    c: str


class Dog(BaseModel):
    pet_type: Literal['dog']
    d: str


try:

    class Model(BaseModel):
        pet: Union[Cat, Dog] = Field(discriminator='pet_type')
        number: int

except PydanticUserError as exc_info:
    assert exc_info.code == 'discriminator-alias-type'
```

## 鉴别器需要字面量 {#discriminator-needs-literal}

当您在鉴别器字段上定义非 `Literal` 类型时，会引发此错误。

```python
from typing import Literal, Union

from pydantic import BaseModel, Field, PydanticUserError


class Cat(BaseModel):
    pet_type: int
    c: str


class Dog(BaseModel):
    pet_type: Literal['dog']
    d: str


try:

    class Model(BaseModel):
        pet: Union[Cat, Dog] = Field(discriminator='pet_type')
        number: int

except PydanticUserError as exc_info:
    assert exc_info.code == 'discriminator-needs-literal'
```

## 鉴别器别名 {#discriminator-alias}

当您在鉴别器字段上定义不同的别名时，会引发此错误。

```python
from typing import Literal, Union

from pydantic import BaseModel, Field, PydanticUserError


class Cat(BaseModel):
    pet_type: Literal['cat'] = Field(validation_alias='PET')
    c: str


class Dog(BaseModel):
    pet_type: Literal['dog'] = Field(validation_alias='Pet')
    d: str


try:

    class Model(BaseModel):
        pet: Union[Cat, Dog] = Field(discriminator='pet_type')
        number: int

except PydanticUserError as exc_info:
    assert exc_info.code == 'discriminator-alias'
```

## 无效的鉴别器验证器 {#discriminator-validator}

当您在鉴别器字段上使用 before、wrap 或 plain 验证器时，会引发此错误。

这是不允许的，因为鉴别器字段用于确定用于验证的模型类型，
因此您不能使用可能改变其值的验证器。

```python
from typing import Literal, Union

from pydantic import BaseModel, Field, PydanticUserError, field_validator


class Cat(BaseModel):
    pet_type: Literal['cat']

    @field_validator('pet_type', mode='before')
    @classmethod
    def validate_pet_type(cls, v):
        if v == 'kitten':
            return 'cat'
        return v


class Dog(BaseModel):
    pet_type: Literal['dog']


try:

    class Model(BaseModel):
        pet: Union[Cat, Dog] = Field(discriminator='pet_type')
        number: int

except PydanticUserError as exc_info:
    assert exc_info.code == 'discriminator-validator'
```

可以通过使用标准的 `Union` 并去掉鉴别器来解决这个问题：

```python
from typing import Literal, Union

from pydantic import BaseModel, field_validator


class Cat(BaseModel):
    pet_type: Literal['cat']

    @field_validator('pet_type', mode='before')
    @classmethod
    def validate_pet_type(cls, v):
        if v == 'kitten':
            return 'cat'
        return v


class Dog(BaseModel):
    pet_type: Literal['dog']


class Model(BaseModel):
    pet: Union[Cat, Dog]


assert Model(pet={'pet_type': 'kitten'}).pet.pet_type == 'cat'
```

## 可调用鉴别器情况无标签 {#callable-discriminator-no-tag}

当使用可调用 `Discriminator` 的 `Union` 没有为所有情况提供 `Tag` 注解时，会引发此错误。

```python
from typing import Annotated, Union

from pydantic import BaseModel, Discriminator, PydanticUserError, Tag


def model_x_discriminator(v):
    if isinstance(v, str):
        return 'str'
    if isinstance(v, (dict, BaseModel)):
        return 'model'


# 联合选择缺少标签
try:

    class DiscriminatedModel(BaseModel):
        x: Annotated[
            Union[str, 'DiscriminatedModel'],
            Discriminator(model_x_discriminator),
        ]

except PydanticUserError as exc_info:
    assert exc_info.code == 'callable-discriminator-no-tag'

# `'DiscriminatedModel'` 联合选择缺少标签
try:

    class DiscriminatedModel(BaseModel):
        x: Annotated[
            Union[Annotated[str, Tag('str')], 'DiscriminatedModel'],
            Discriminator(model_x_discriminator),
        ]

except PydanticUserError as exc_info:
    assert exc_info.code == 'callable-discriminator-no-tag'

# `str` 联合选择缺少标签
try:

    class DiscriminatedModel(BaseModel):
        x: Annotated[
            Union[str, Annotated['DiscriminatedModel', Tag('model')]],
            Discriminator(model_x_discriminator),
        ]

except PydanticUserError as exc_info:
    assert exc_info.code == 'callable-discriminator-no-tag'
```

## `TypedDict` 版本 {#typed-dict-version}

当您在 Python < 3.12 上使用 [typing.TypedDict][] 而不是 `typing_extensions.TypedDict` 时，会引发此错误。

## 模型父类字段被覆盖 {#model-field-overridden}

当基类上定义的字段被非注解属性覆盖时，会引发此错误。

```python
from pydantic import BaseModel, PydanticUserError


class Foo(BaseModel):
    a: float


try:

    class Bar(Foo):
        x: float = 12.3
        a = 123.0

except PydanticUserError as exc_info:
    assert exc_info.code == 'model-field-overridden'
```

## 模型字段缺少注解 {#model-field-missing-annotation}

当字段没有注解时，会引发此错误。

```python
from pydantic import BaseModel, Field, PydanticUserError

try:

    class Model(BaseModel):
        a = Field('foobar')
        b = None

except PydanticUserError as exc_info:
    assert exc_info.code == 'model-field-missing-annotation'
```

如果该字段不打算成为字段，您可以通过将其注解为 `ClassVar` 来解决错误：

```python
from typing import ClassVar

from pydantic import BaseModel


class Model(BaseModel):
    a: ClassVar[str]
```

或者更新 `model_config['ignored_types']`：

```python
from pydantic import BaseModel, ConfigDict


class IgnoredType:
    pass


class MyModel(BaseModel):
    model_config = ConfigDict(ignored_types=(IgnoredType,))

    _a = IgnoredType()
    _b: int = IgnoredType()
    _c: IgnoredType
    _d: IgnoredType = IgnoredType()
```

## `Config` 和 `model_config` 同时定义 {#config-both}

当 `class Config` 和 `model_config` 一起使用时，会引发此错误。

```python
from pydantic import BaseModel, ConfigDict, PydanticUserError

try:

    class Model(BaseModel):
        model_config = ConfigDict(from_attributes=True)

        a: str

        class Config:
            from_attributes = True

except PydanticUserError as exc_info:
    assert exc_info.code == 'config-both'
```

## 关键字参数已移除 {#removed-kwargs}

当关键字参数在 Pydantic V2 中不可用时，会引发此错误。

例如，`regex` 已从 Pydantic V2 中移除：

```python
from pydantic import BaseModel, Field, PydanticUserError

try:

    class Model(BaseModel):
        x: str = Field(regex='test')

except PydanticUserError as exc_info:
    assert exc_info.code == 'removed-kwargs'
```

## 循环引用模式 {#circular-reference-schema}

当发现会导致无限递归的循环引用时，会引发此错误。

例如，这是一个有效的类型别名：

```python {test="skip" lint="skip" upgrade="skip"}
type A = list[A] | None
```

而这些不是：

```python {test="skip" lint="skip" upgrade="skip"}
type A = A

type B = C
type C = B
```

## JSON schema 无效类型 {#invalid-for-json-schema}

当 Pydantic 无法为某些 `CoreSchema` 生成 JSON schema 时，会引发此错误。

```python
from pydantic import BaseModel, ImportString, PydanticUserError


class Model(BaseModel):
    a: ImportString


try:
    Model.model_json_schema()
except PydanticUserError as exc_info:
    assert exc_info.code == 'invalid-for-json-schema'
```

## JSON schema 已使用 {#json-schema-already-used}

当 JSON schema 生成器已被用于生成 JSON schema 时，会引发此错误。
您必须创建一个新实例来生成新的 JSON schema。

## BaseModel 被实例化 {#base-model-instantiated}

当您直接实例化 `BaseModel` 时，会引发此错误。Pydantic 模型应该继承自 `BaseModel`。

```python
from pydantic import BaseModel, PydanticUserError

try:
    BaseModel()
except PydanticUserError as exc_info:
    assert exc_info.code == 'base-model-instantiated'
```

## 未定义的注解 {#undefined-annotation}

在 `CoreSchema` 生成过程中处理未定义的注解时，会引发此错误。

```python
from pydantic import BaseModel, PydanticUndefinedAnnotation


class Model(BaseModel):
    a: 'B'  # noqa F821


try:
    Model.model_rebuild()
except PydanticUndefinedAnnotation as exc_info:
    assert exc_info.code == 'undefined-annotation'
```

## 未知类型的模式 {#schema-for-unknown-type}

当 Pydantic 无法为某些类型生成 `CoreSchema` 时，会引发此错误。

```python
from pydantic import BaseModel, PydanticUserError

try:

    class Model(BaseModel):
        x: 43 = 123

except PydanticUserError as exc_info:
    assert exc_info.code == 'schema-for-unknown-type'
```

## 导入错误 {#import-error}

当您尝试导入在 Pydantic V1 中可用但在 Pydantic V2 中已被移除的对象时，会引发此错误。

有关更多信息，请参阅[迁移指南](../migration.md)。

## `create_model` 字段定义 {#create-model-field-definitions}

当您在 [`create_model()`][pydantic.create_model] 中提供无效的字段定义时，会引发此错误。

```python
from pydantic import PydanticUserError, create_model

try:
    create_model('FooModel', foo=(str, 'default value', 'more'))
except PydanticUserError as exc_info:
    assert exc_info.code == 'create-model-field-definitions'
```

字段定义语法可以在[动态模型创建](../concepts/models.md#dynamic-model-creation)文档中找到。

## 验证器无字段 {#validator-no-fields}

当您使用裸验证器（没有字段）时，会引发此错误。

```python
from pydantic import BaseModel, PydanticUserError, field_validator

try:

    class Model(BaseModel):
        a: str

        @field_validator
        def checker(cls, v):
            return v

except PydanticUserError as exc_info:
    assert exc_info.code == 'validator-no-fields'
```

验证器应该与字段和关键字参数一起使用。

```python
from pydantic import BaseModel, field_validator


class Model(BaseModel):
    a: str

    @field_validator('a')
    def checker(cls, v):
        return v
```

## 无效的验证器字段 {#validator-invalid-fields}

当您使用非字符串字段的验证器时，会引发此错误。

```python
from pydantic import BaseModel, PydanticUserError, field_validator

try:

    class Model(BaseModel):
        a: str
        b: str

        @field_validator(['a', 'b'])
        def check_fields(cls, v):
            return v

except PydanticUserError as exc_info:
    assert exc_info.code == 'validator-invalid-fields'
```

字段应该作为单独的字符串参数传递：

```python
from pydantic import BaseModel, field_validator


class Model(BaseModel):
    a: str
    b: str

    @field_validator('a', 'b')
    def check_fields(cls, v):
        return v
```

## 验证器应用于实例方法 {#validator-instance-method}

当您将验证器应用于实例方法时，会引发此错误。

```python
from pydantic import BaseModel, PydanticUserError, field_validator

try:

    class Model(BaseModel):
        a: int = 1

        @field_validator('a')
        def check_a(self, value):
            return value

except PydanticUserError as exc_info:
    assert exc_info.code == 'validator-instance-method'
```

## `json_schema_input_type` 与错误的模式一起使用 {#validator-input-type}

当您明确为 `json_schema_input_type` 参数指定值，但 `mode` 未设置为 `'before'`、`'plain'` 或 `'wrap'` 时，会引发此错误。

```python
from pydantic import BaseModel, PydanticUserError, field_validator

try:

    class Model(BaseModel):
        a: int = 1

        @field_validator('a', mode='after', json_schema_input_type=int)
        @classmethod
        def check_a(self, value):
            return value

except PydanticUserError as exc_info:
    assert exc_info.code == 'validator-input-type'
```

记录 JSON Schema 输入类型仅适用于给定值可以是任何内容的验证器。这就是为什么它不适用于 `after` 验证器，因为在 `after` 验证器中，值首先根据类型注解进行验证。

## 根验证器，`pre`，`skip_on_failure` {#root-validator-pre-skip}

如果您使用 `@root_validator` 且 `pre=False`（默认值），则必须指定 `skip_on_failure=True`。
`skip_on_failure=False` 选项不再可用。

如果您没有尝试设置 `skip_on_failure=False`，可以安全地设置 `skip_on_failure=True`。
如果这样做，当任何字段验证失败时，此根验证器将不再被调用。

有关更多详细信息，请参阅[迁移指南](../migration.md)。

## `model_serializer` 实例方法 {#model-serializer-instance-method}

`@model_serializer` 必须应用于实例方法。

当您在实例方法上应用 `model_serializer` 但没有 `self` 时，会引发此错误：

```python
from pydantic import BaseModel, PydanticUserError, model_serializer

try:

    class MyModel(BaseModel):
        a: int

        @model_serializer
        def _serialize(slf, x, y, z):
            return slf

except PydanticUserError as exc_info:
    assert exc_info.code == 'model-serializer-instance-method'
```

或者在类方法上：

```python
from pydantic import BaseModel, PydanticUserError, model_serializer

try:

    class MyModel(BaseModel):
        a: int

        @model_serializer
        @classmethod
        def _serialize(self, x, y, z):
            return self

except PydanticUserError as exc_info:
    assert exc_info.code == 'model-serializer-instance-method'
```

## `validator`、`field`、`config` 和 `info` {#validator-field-config-info}

`field` 和 `config` 参数在 Pydantic V2 中不可用。
请改用 `info` 参数。

您可以通过 `info.config` 访问配置，
但它是一个字典，而不是像 Pydantic V1 中那样的对象。

`field` 参数不再可用。

## Pydantic V1 验证器签名 {#validator-v1-signature}

当您使用不支持的 Pydantic V1 风格验证器签名时，会引发此错误。

```python
import warnings

from pydantic import BaseModel, PydanticUserError, validator

warnings.filterwarnings('ignore', category=DeprecationWarning)

try:

    class Model(BaseModel):
        a: int

        @validator('a')
        def check_a(cls, value, foo):
            return value

except PydanticUserError as exc_info:
    assert exc_info.code == 'validator-v1-signature'
```

## 无法识别的 `field_validator` 签名 {#validator-signature}

当 `field_validator` 或 `model_validator` 函数具有错误的签名时，会引发此错误。

```python
from pydantic import BaseModel, PydanticUserError, field_validator

try:

    class Model(BaseModel):
        a: str

        @field_validator('a')
        @classmethod
        def check_a(cls):
            return 'a'

except PydanticUserError as exc_info:
    assert exc_info.code == 'validator-signature'
```

## 无法识别的 `field_serializer` 签名 {#field-serializer-signature}

当 `field_serializer` 函数具有错误的签名时，会引发此错误。

```python
from pydantic import BaseModel, PydanticUserError, field_serializer

try:

    class Model(BaseModel):
        x: int

        @field_serializer('x')
        def no_args():
            return 'x'

except PydanticUserError as exc_info:
    assert exc_info.code == 'field-serializer-signature'
```

有效的字段序列化器签名是：

```python {test="skip" lint="skip" upgrade="skip"}
from pydantic import FieldSerializationInfo, SerializerFunctionWrapHandler, field_serializer

# 具有默认模式或 `mode='plain'` 的实例方法
@field_serializer('x')  # 或 @field_serializer('x', mode='plain')
def ser_x(self, value: Any, info: FieldSerializationInfo): ...

# 具有默认模式或 `mode='plain'` 的静态方法或函数
@field_serializer('x')  # 或 @field_serializer('x', mode='plain')
@staticmethod
def ser_x(value: Any, info: FieldSerializationInfo): ...

# 等同于
def ser_x(value: Any, info: FieldSerializationInfo): ...
serializer('x')(ser_x)

# 具有 `mode='wrap'` 的实例方法
@field_serializer('x', mode='wrap')
def ser_x(self, value: Any, nxt: SerializerFunctionWrapHandler, info: FieldSerializationInfo): ...

# 具有 `mode='wrap'` 的静态方法或函数
@field_serializer('x', mode='wrap')
@staticmethod
def ser_x(value: Any, nxt: SerializerFunctionWrapHandler, info: FieldSerializationInfo): ...

# 等同于
def ser_x(value: Any, nxt: SerializerFunctionWrapHandler, info: FieldSerializationInfo): ...
serializer('x')(ser_x)

# 对于所有这些，您也可以选择省略 `info` 参数，例如：
@field_serializer('x')
def ser_x(self, value: Any): ...

@field_serializer('x', mode='wrap')
def ser_x(self, value: Any, handler: SerializerFunctionWrapHandler): ...
```

## 无法识别的 `model_serializer` 签名 {#model-serializer-signature}

当 `model_serializer` 函数具有错误的签名时，会引发此错误。

```python
from pydantic import BaseModel, PydanticUserError, model_serializer

try:

    class MyModel(BaseModel):
        a: int

        @model_serializer
        def _serialize(self, x, y, z):
            return self

except PydanticUserError as exc_info:
    assert exc_info.code == 'model-serializer-signature'
```

有效的模型序列化器签名是：

```python {test="skip" lint="skip" upgrade="skip"}
from pydantic import SerializerFunctionWrapHandler, SerializationInfo, model_serializer

# 具有默认模式或 `mode='plain'` 的实例方法
@model_serializer  # 或 model_serializer(mode='plain')
def mod_ser(self, info: SerializationInfo): ...

# 具有 `mode='wrap'` 的实例方法
@model_serializer(mode='wrap')
def mod_ser(self, handler: SerializerFunctionWrapHandler, info: SerializationInfo):

# 对于所有这些，您也可以选择省略 `info` 参数，例如：
@model_serializer(mode='plain')
def mod_ser(self): ...

@model_serializer(mode='wrap')
def mod_ser(self, handler: SerializerFunctionWrapHandler): ...
```

## 多个字段序列化器 {#multiple-field-serializers}

当为字段定义了多个 `model_serializer` 函数时，会引发此错误。

```python
from pydantic import BaseModel, PydanticUserError, field_serializer

try:

    class MyModel(BaseModel):
        x: int
        y: int

        @field_serializer('x', 'y')
        def serializer1(v):
            return f'{v:,}'

        @field_serializer('x')
        def serializer2(v):
            return v

except PydanticUserError as exc_info:
    assert exc_info.code == 'multiple-field-serializers'
```

## 无效的注解类型 {#invalid-annotated-type}

当注解无法注解类型时，会引发此错误。

```python
from typing import Annotated

from pydantic import BaseModel, FutureDate, PydanticUserError

try:

    class Model(BaseModel):
        foo: Annotated[str, FutureDate()]

except PydanticUserError as exc_info:
    assert exc_info.code == 'invalid-annotated-type'
```

## `config` 与 `TypeAdapter` 一起使用时未使用 {#type-adapter-config-unused}

如果您尝试将 `config` 传递给 `TypeAdapter`，但该类型具有无法被覆盖的自己的配置（目前只有 `BaseModel`、`TypedDict` 和 `dataclass`），您将收到此错误：

```python
from typing_extensions import TypedDict

from pydantic import ConfigDict, PydanticUserError, TypeAdapter


class MyTypedDict(TypedDict):
    x: int


try:
    TypeAdapter(MyTypedDict, config=ConfigDict(strict=True))
except PydanticUserError as exc_info:
    assert exc_info.code == 'type-adapter-config-unused'
```

相反，您需要子类化该类型并在其上覆盖或设置配置：

```python
from typing_extensions import TypedDict

from pydantic import ConfigDict, TypeAdapter


class MyTypedDict(TypedDict):
    x: int

    # 或者对于 BaseModel 使用 `model_config = ...`
    __pydantic_config__ = ConfigDict(strict=True)


TypeAdapter(MyTypedDict)  # 正常
```

## 无法为 `RootModel` 指定 `model_config['extra']` {#root-model-extra}

由于 `RootModel` 无法在初始化期间存储甚至接受额外字段，如果您尝试在创建 `RootModel` 的子类时为配置设置 `'extra'` 指定值，我们会引发错误：

```python
from pydantic import PydanticUserError, RootModel

try:

    class MyRootModel(RootModel):
        model_config = {'extra': 'allow'}
        root: int

except PydanticUserError as exc_info:
    assert exc_info.code == 'root-model-extra'
```

## 无法评估类型注解 {#unevaluable-type-annotation}

由于类型注解在赋值*之后*进行评估，当使用与字段名称冲突的类型注解名称时，您可能会得到意外的结果。在以下情况下我们会引发错误：

```python {test="skip"}
from datetime import date

from pydantic import BaseModel, Field


class Model(BaseModel):
    date: date = Field(description='A date')
```

作为解决方法，您可以使用别名或更改导入：

```python {lint="skip"}
import datetime
# 或者 `from datetime import date as _date`

from pydantic import BaseModel, Field


class Model(BaseModel):
    date: datetime.date = Field(description='A date')
```

## 不兼容的 `dataclass` `init` 和 `extra` 设置 {#dataclass-init-false-extra-allow}

Pydantic 不允许在数据类上指定 `extra='allow'` 设置，同时任何字段设置了 `init=False`。

因此，您不能执行以下操作：

```python {test="skip"}
from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass


@dataclass(config=ConfigDict(extra='allow'))
class A:
    a: int = Field(init=False, default=1)
```

上述代码片段在构建数据类 `A` 的模式时会导致以下错误：

```output
pydantic.errors.PydanticUserError: Field a has `init=False` and dataclass has config setting `extra="allow"`.
This combination is not allowed.
```

## `dataclass` 字段上不兼容的 `init` 和 `init_var` 设置 {#clashing-init-and-init-var}

`init=False` 和 `init_var=True` 设置是互斥的。这样做会导致如下示例中所示的 `PydanticUserError`。

```python {test="skip"}
from pydantic import Field
from pydantic.dataclasses import dataclass


@dataclass
class Foo:
    bar: str = Field(init=False, init_var=True)


"""
pydantic.errors.PydanticUserError: Dataclass field bar has init=False and init_var=True, but these are mutually exclusive.
"""
```

## `model_config` 被用作模型字段 {#model-config-invalid-field-name}

当 `model_config` 被用作字段名称时，会引发此错误。

```python
from pydantic import BaseModel, PydanticUserError

try:

    class Model(BaseModel):
        model_config: str

except PydanticUserError as exc_info:
    assert exc_info.code == 'model-config-invalid-field-name'
```

## [`with_config`][pydantic.config.with_config] 在 `BaseModel` 子类上使用 {#with-config-on-model}

当 [`with_config`][pydantic.config.with_config] 装饰器用于已经是 Pydantic 模型的类时，会引发此错误（请改用 `model_config` 属性）。

```python
from pydantic import BaseModel, PydanticUserError, with_config

try:

    @with_config({'allow_inf_nan': True})
    class Model(BaseModel):
        bar: str

except PydanticUserError as exc_info:
    assert exc_info.code == 'with-config-on-model'
```

## `dataclass` 在 `BaseModel` 子类上使用 {#dataclass-on-model}

当 Pydantic `dataclass` 装饰器用于已经是 Pydantic 模型的类时，会引发此错误。

```python
from pydantic import BaseModel, PydanticUserError
from pydantic.dataclasses import dataclass

try:

    @dataclass
    class Model(BaseModel):
        bar: str

except PydanticUserError as exc_info:
    assert exc_info.code == 'dataclass-on-model'
```

## `validate_call` 不支持的类型 {#validate-call-type}

`validate_call` 对其可以验证的可调用对象有一些限制。当您尝试将其与不支持的可调用对象一起使用时，会引发此错误。
目前支持的可调用对象包括函数（包括 lambda，但不包括内置函数）、方法以及 [`partial`][functools.partial] 的实例。
对于 [`partial`][functools.partial]，被部分应用的函数必须是受支持的可调用对象之一。

### `@classmethod`、`@staticmethod` 和 `@property`

这些装饰器必须放在 `validate_call` 之前。

```python
from pydantic import PydanticUserError, validate_call

# 错误
try:

    class A:
        @validate_call
        @classmethod
        def f1(cls): ...

except PydanticUserError as exc_info:
    assert exc_info.code == 'validate-call-type'


# 正确
@classmethod
@validate_call
def f2(cls): ...
```

### 类

虽然类本身是可调用对象，但 `validate_call` 不能应用于它们，因为它需要知道使用哪个方法（`__init__` 或 `__new__`）来获取类型注解。如果您想验证类的构造函数，应该将 `validate_call` 放在适当的方法上。

```python
from pydantic import PydanticUserError, validate_call

# 错误
try:

    @validate_call
    class A1: ...

except PydanticUserError as exc_info:
    assert exc_info.code == 'validate-call-type'


# 正确
class A2:
    @validate_call
    def __init__(self): ...

    @validate_call
    def __new__(cls): ...
```

### 可调用实例

虽然实例可以通过实现 `__call__` 方法变得可调用，但目前这些类型的实例无法使用 `validate_call` 进行验证。
这可能会在未来改变，但目前，您应该明确在 `__call__` 上使用 `validate_call`。

```python
from pydantic import PydanticUserError, validate_call

# 错误
try:

    class A1:
        def __call__(self): ...

    validate_call(A1())

except PydanticUserError as exc_info:
    assert exc_info.code == 'validate-call-type'


# 正确
class A2:
    @validate_call
    def __call__(self): ...
```

### 无效签名

这种情况通常较少见，但可能的原因是您尝试验证一个没有至少一个参数（通常是 `self`）的方法。

```python
from pydantic import PydanticUserError, validate_call

try:

    class A:
        def f(): ...

    validate_call(A().f)
except PydanticUserError as exc_info:
    assert exc_info.code == 'validate-call-type'
```

## [`Unpack`][typing.Unpack] 与非 [`TypedDict`][typing.TypedDict] 一起使用 {#unpack-typed-dict}

当 [`Unpack`][typing.Unpack] 与不是有效 [`TypedDict`][typing.TypedDict] 的 [`TypedDict`][typing.TypedDict] 类对象一起使用时，会引发此错误。

有关参考，请参阅[相关规范部分]和[PEP 692]。

```python
from typing_extensions import TypedDict, Unpack

from pydantic import PydanticUserError, validate_call

try:

    class TD(TypedDict):
        x: int

    @validate_call
    def func(**kwargs: Unpack[TD]):
        pass

except PydanticUserError as exc_info:
    assert exc_info.code == 'unpack-typed-dict'
```

## 重叠的解包 [`TypedDict`][typing.TypedDict] 字段和参数 {#overlapping-unpack-typed-dict}

当用于类型提示可变关键字参数的类型字典的字段名称与其他参数重叠时（除非是[仅位置参数][positional-only_parameter]），会引发此错误。

有关参考，请参阅[相关规范部分]和[PEP 692]。

```python
from typing_extensions import TypedDict, Unpack

from pydantic import PydanticUserError, validate_call


class TD(TypedDict):
    a: int


try:

    @validate_call
    def func(a: int, **kwargs: Unpack[TD]):
        pass

except PydanticUserError as exc_info:
    assert exc_info.code == 'overlapping-unpack-typed-dict'
```

[related specification section]: https://typing.readthedocs.io/en/latest/spec/callables.html#unpack-for-keyword-arguments
[PEP 692]: https://peps.python.org/pep-0692/

## 无效的 `Self` 类型 {#invalid-self-type}

目前，[`Self`][typing.Self] 只能用于注解类的字段（特别是 [`BaseModel`][pydantic.BaseModel]、[`NamedTuple`][typing.NamedTuple]、[`TypedDict`][typing.TypedDict] 或数据类的子类）。尝试以任何其他方式使用 [`Self`][typing.Self] 都会引发此错误。

```python
from typing_extensions import Self

from pydantic import PydanticUserError, validate_call

try:

    @validate_call
    def func(self: Self):
        pass

except PydanticUserError as exc_info:
    assert exc_info.code == 'invalid-self-type'
```

以下 [`validate_call()`][pydantic.validate_call] 示例也会引发此错误，即使从类型检查的角度来看是正确的。这可能会在未来得到支持。

```python
from typing_extensions import Self

from pydantic import BaseModel, PydanticUserError, validate_call

try:

    class A(BaseModel):
        @validate_call
        def func(self, arg: Self):
            pass

except PydanticUserError as exc_info:
    assert exc_info.code == 'invalid-self-type'
```

## `validate_by_alias` 和 `validate_by_name` 都设置为 `False` {#validate-by-alias-and-name-false}

当您在配置中将 `validate_by_alias` 和 `validate_by_name` 都设置为 `False` 时，会引发此错误。

这是不允许的，因为它会使填充属性变得不可能。

```python
from pydantic import BaseModel, ConfigDict, Field, PydanticUserError

try:

    class Model(BaseModel):
        a: int = Field(alias='A')

        model_config = ConfigDict(
            validate_by_alias=False, validate_by_name=False
        )

except PydanticUserError as exc_info:
    assert exc_info.code == 'validate-by-alias-and-name-false'
```