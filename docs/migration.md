---
subtitle: 迁移指南
description: 从 Pydantic V1 迁移。
---

# 迁移指南

Pydantic V2 引入了许多 API 变更，包括一些破坏性变更。

本页面提供了一个指南，重点介绍了最重要的变更，以帮助您将代码从 Pydantic V1 迁移到 Pydantic V2。

## 安装 Pydantic V2

Pydantic V2 现在是 Pydantic 的当前生产版本。
您可以从 PyPI 安装 Pydantic V2：

```bash
pip install -U pydantic
```

如果遇到任何问题，请使用 `bug V2` 标签在 [GitHub 上创建问题](https://github.com/pydantic/pydantic/issues)。这将帮助我们积极监控和跟踪错误，并继续改进库的性能。

如果出于任何原因需要使用最新的 Pydantic V1，请参阅下面的 [继续使用 Pydantic V1 功能](#continue-using-pydantic-v1-features) 部分，了解有关从 `pydantic.v1` 安装和导入的详细信息。

## 代码转换工具

我们创建了一个工具来帮助您迁移代码。这个工具仍处于测试阶段，但我们希望它能帮助您更快地迁移代码。

您可以从 PyPI 安装该工具：

```bash
pip install bump-pydantic
```

使用方法很简单。如果您的项目结构是：

    * repo_folder
        * my_package
            * <python 源文件> ...

那么您需要执行：

    cd /path/to/repo_folder
    bump-pydantic my_package

有关更多信息，请参阅 [Bump Pydantic](https://github.com/pydantic/bump-pydantic) 仓库。

## 继续使用 Pydantic V1 功能 {#continue-using-pydantic-v1-features}

当您需要时，Pydantic V1 仍然可用，但我们建议迁移到 Pydantic V2 以获得其改进和新功能。

如果您需要使用最新的 Pydantic V1，可以使用以下命令安装：

```bash
pip install "pydantic==1.*"
```

Pydantic V2 包还继续通过 `pydantic.v1` 导入提供对 Pydantic V1 API 的访问。

例如，您可以使用 Pydantic V1 的 `BaseModel` 类而不是 Pydantic V2 的 `pydantic.BaseModel` 类：

```python {test="skip" lint="skip" upgrade="skip"}
from pydantic.v1 import BaseModel
```

您还可以导入已从 Pydantic V2 中移除的函数，例如 `lenient_isinstance`：

```python {test="skip" lint="skip" upgrade="skip"}
from pydantic.v1.utils import lenient_isinstance
```

Pydantic V1 文档可在 [https://docs.pydantic.dev/1.10/](https://docs.pydantic.dev/1.10/) 获取。

### 在 v1/v2 环境中使用 Pydantic v1 功能

从 `pydantic>=1.10.17` 开始，`pydantic.v1` 命名空间可以在 V1 中使用。
这使得迁移到 V2 更容易，因为 V2 也支持 `pydantic.v1` 命名空间。为了解除 `pydantic<2` 依赖并继续使用 V1 功能，请执行以下步骤：

1. 将 `pydantic<2` 替换为 `pydantic>=1.10.17`
2. 查找并替换所有出现的：

```python {test="skip" lint="skip" upgrade="skip"}
from pydantic.<module> import <object>
```

替换为：

```python {test="skip" lint="skip" upgrade="skip"}
from pydantic.v1.<module> import <object>
```

以下是您可以根据 Pydantic 版本导入 `pydantic` 的 v1 功能的方式：

=== "`pydantic>=1.10.17,<3`"
    从 `v1.10.17` 开始，`.v1` 命名空间在 V1 中可用，允许如下导入：

    ```python {test="skip" lint="skip" upgrade="skip"}
    from pydantic.v1.fields import ModelField
    ```

=== "`pydantic<3`"
    所有版本的 Pydantic V1 和 V2 都支持以下导入模式，以防您不知道正在使用哪个版本的 Pydantic：

    ```python {test="skip" lint="skip" upgrade="skip"}
    try:
        from pydantic.v1.fields import ModelField
    except ImportError:
        from pydantic.fields import ModelField
    ```

!!! note
    当使用 `pydantic>=1.10.17,<2` 和 `.v1` 命名空间导入模块时，这些模块将*不*是与没有 `.v1` 命名空间的相同导入**相同**的模块，但导入的符号*将*是相同的。例如 `pydantic.v1.fields is not pydantic.fields`，但 `pydantic.v1.fields.ModelField is pydantic.fields.ModelField`。幸运的是，这在绝大多数情况下不太可能相关。这只是提供更平滑迁移体验的不幸后果。

## 迁移指南

以下部分提供了 Pydantic V2 中最重要变更的详细信息。

### `pydantic.BaseModel` 的变更 {#changes-to-pydanticbasemodel}

各种方法名称已更改；所有非弃用的 `BaseModel` 方法现在都具有匹配 `model_.*` 或 `__.*pydantic.*__` 格式的名称。在可能的情况下，我们保留了具有旧名称的已弃用方法以帮助简化迁移，但调用它们将发出 `DeprecationWarning`。

| Pydantic V1 | Pydantic V2  |
| ----------- | ------------ |
| `__fields__` | `model_fields` |
| `__private_attributes__` | `__pydantic_private__` |
| `__validators__` | `__pydantic_validator__` |
| `construct()` | `model_construct()` |
| `copy()` | `model_copy()` |
| `dict()` | `model_dump()` |
| `json_schema()` | `model_json_schema()` |
| `json()` | `model_dump_json()` |
| `parse_obj()` | `model_validate()` |
| `update_forward_refs()` | `model_rebuild()` |

* 一些内置的数据加载功能已被计划移除。特别是，`parse_raw` 和 `parse_file` 现在已被弃用。在 Pydantic V2 中，`model_validate_json` 的工作方式类似于 `parse_raw`。否则，您应该加载数据然后将其传递给 `model_validate`。
* `from_orm` 方法已被弃用；您现在可以使用 `model_validate`（相当于 Pydantic V1 中的 `parse_obj`）来实现类似的功能，只要您在模型配置中设置了 `from_attributes=True`。
* 模型的 `__eq__` 方法已更改。
    * 模型只能与其他 `BaseModel` 实例相等。
    * 两个模型实例要相等，它们必须具有相同的：
        * 类型（或者，对于泛型模型，非参数化的泛型原始类型）
        * 字段值
        * 额外值（仅当 `model_config['extra'] == 'allow'` 时相关）
        * 私有属性值；具有不同私有属性值的模型不再相等。
        * 模型不再等于包含其数据的字典。
        * 不同类型的非泛型模型永远不相等。
        * 具有不同原始类型的泛型模型永远不相等。我们不要求*精确*的类型相等性，因此，例如，`MyGenericModel[Any]` 的实例可以与 `MyGenericModel[int]` 的实例相等。
* 我们已替换了使用 `__root__` 字段来指定"自定义根模型"的方式，改用名为 [`RootModel`](concepts/models.md#rootmodel-and-custom-root-types) 的新类型，旨在替换 Pydantic V1 中使用名为 `__root__` 字段的功能。请注意，`RootModel` 类型不再支持 `arbitrary_types_allowed` 配置设置。有关说明，请参阅[此问题评论](https://github.com/pydantic/pydantic/issues/6710#issuecomment-1700948167)。
* 我们显著扩展了 Pydantic 在自定义序列化方面的能力。特别是，我们添加了 [`@field_serializer`](api/functional_serializers.md#pydantic.functional_serializers.field_serializer)、[`@model_serializer`](api/functional_serializers.md#pydantic.functional_serializers.model_serializer) 和 [`@computed_field`](api/fields.md#pydantic.fields.computed_field) 装饰器，每个都解决了 Pydantic V1 中的各种缺点。
    * 有关这些新装饰器的使用文档，请参阅[自定义序列化器](concepts/serialization.md#serializers)。
    * 由于性能开销和实现复杂性，我们现在已弃用在模型配置中指定 `json_encoders` 的支持。此功能最初是为了实现自定义序列化逻辑而添加的，我们认为新的序列化装饰器在大多数常见场景中是更好的选择。
* 我们更改了当模型子类作为父模型中的嵌套字段出现时的序列化行为。在 V1 中，我们总是包含子类实例的所有字段。在 V2 中，当我们转储模型时，我们只包含在字段的注释类型上定义的字段。这有助于防止一些意外的安全错误。您可以在模型导出文档的[相关部分](concepts/serialization.md#subclasses-of-model-like-types)中阅读更多相关信息（包括如何选择退出此行为）。
* `GetterDict` 已被移除，因为它只是 `orm_mode` 的实现细节，而 `orm_mode` 已被移除。
* 在许多情况下，传递给构造函数的参数将被**复制**以执行验证，并在必要时进行强制转换（请参阅[文档](./concepts/models.md#attribute-copies)）。
  这在将可变对象作为参数传递给构造函数时尤其值得注意。
* `.json()` 方法已被弃用，尝试使用此弃用方法并带有参数（如 `indent` 或 `ensure_ascii`）可能会导致混淆的错误。为了获得最佳结果，请切换到 V2 的等效方法 `model_dump_json()`。
如果您仍然想使用上述参数，可以使用[此解决方法](https://github.com/pydantic/pydantic/issues/8825#issuecomment-1946206415)。
* 非字符串键值的 JSON 序列化通常使用 `str(key)` 完成，这导致了一些行为变化，例如：

```python {test="skip"}
from typing import Optional

from pydantic import BaseModel as V2BaseModel
from pydantic.v1 import BaseModel as V1BaseModel


class V1Model(V1BaseModel):
    a: dict[Optional[str], int]


class V2Model(V2BaseModel):
    a: dict[Optional[str], int]


v1_model = V1Model(a={None: 123})
v2_model = V2Model(a={None: 123})

# V1
print(v1_model.json())
#> {"a": {"null": 123}}

# V2
print(v2_model.model_dump_json())
#> {"a":{"None":123}}
```

* `model_dump_json()` 结果经过压缩以节省空间，并不总是与 `json.dumps()` 输出完全匹配。
话虽如此，您可以轻松修改 `json.dumps()` 结果中使用的分隔符以使两个输出对齐：

```python {test="skip"}
import json

from pydantic import BaseModel as V2BaseModel
from pydantic.v1 import BaseModel as V1BaseModel


class V1Model(V1BaseModel):
    a: list[str]


class V2Model(V2BaseModel):
    a: list[str]


v1_model = V1Model(a=['fancy', 'sushi'])
v2_model = V2Model(a=['fancy', 'sushi'])

# V1
print(v1_model.json())
#> {"a": ["fancy", "sushi"]}

# V2
print(v2_model.model_dump_json())
#> {"a":["fancy","sushi"]}

# Plain json.dumps
print(json.dumps(v2_model.model_dump()))
#> {"a": ["fancy", "sushi"]}

# Modified json.dumps
print(json.dumps(v2_model.model_dump(), separators=(',', ':')))
#> {"a":["fancy","sushi"]}
```

### `pydantic.generics.GenericModel` 的变更

`GenericModel` 已被移除。相反，您可以直接继承 `typing.Generic` 或 `typing_extensions.Generic`。

现在，您可以通过直接在 `BaseModel` 子类上添加 `Generic` 作为父类来创建泛型 `BaseModel` 子类。
这看起来像 `class MyGenericModel(BaseModel, Generic[T]): ...`。

不支持混合使用 V1 和 V2 模型，这意味着此类泛型 `BaseModel`（V2）的类型参数不能是 V1 模型。

虽然可能不会引发错误，但我们强烈建议不要在 `isinstance` 检查中使用*参数化*泛型。

* 例如，您不应该执行 `isinstance(my_model, MyGenericModel[int])`。
    但是，执行 `isinstance(my_model, MyGenericModel)` 是可以的。（请注意，对于标准泛型，使用参数化泛型进行子类检查会引发错误。）
* 如果您需要对参数化泛型执行 `isinstance` 检查，可以通过子类化参数化泛型类来实现。这看起来像 `class MyIntModel(MyGenericModel[int]): ...` 和
    `isinstance(my_model, MyIntModel)`。

更多信息请参阅[泛型模型](concepts/models.md#generic-models)文档。

### `pydantic.Field` 的变更

`Field` 不再支持向 JSON 模式添加任意关键字参数。相反，您想要添加到 JSON 模式的任何额外数据都应作为字典传递给 `json_schema_extra` 关键字参数。

在 Pydantic V1 中，当未设置别名时，`alias` 属性返回字段的名称。
在 Pydantic V2 中，此行为已更改为当未设置别名时返回 `None`。

以下属性已从 `Field` 中移除或更改：

* `const`
* `min_items`（改用 `min_length`）
* `max_items`（改用 `max_length`）
* `unique_items`
* `allow_mutation`（改用 `frozen`）
* `regex`（改用 `pattern`）
* `final`（改用 [typing.Final][] 类型提示）

字段约束不再自动推送到泛型的参数中。例如，您不能再通过提供 `my_list: list[str] = Field(pattern=".*")` 来验证列表中的每个元素是否匹配正则表达式。相反，使用 [`typing.Annotated`][] 在 `str` 本身上提供注释：`my_list: list[Annotated[str, Field(pattern=".*")]]`

### 数据类的变更

Pydantic [数据类](concepts/dataclasses.md) 继续用于为标准数据类启用数据验证，而无需子类化 `BaseModel`。Pydantic V2 对此数据类行为引入了以下更改：

* 当用作字段时，数据类（Pydantic 或普通数据类）不再接受元组作为验证输入；应改用字典。
* Pydantic 数据类中的 `__post_init__` 现在将在验证*之后*调用，而不是之前。
    * 因此，`__post_init_post_parse__` 方法变得冗余，因此已被移除。
* Pydantic 不再支持 Pydantic 数据类的 `extra='allow'`，其中传递给初始化程序的额外字段将作为额外属性存储在数据类上。`extra='ignore'` 仍然支持用于在解析数据时忽略意外字段，只是它们不会存储在实例上。
* Pydantic 数据类不再具有属性 `__pydantic_model__`，并且不再使用底层的 `BaseModel` 来执行验证或提供其他功能。
    * 要执行验证、生成 JSON 模式或使用任何其他在 V1 中可能需要 `__pydantic_model__` 的功能，您现在应该将数据类包装在 [`TypeAdapter`][pydantic.type_adapter.TypeAdapter] 中（[下面讨论更多](#introduction-of-typeadapter)）并使用其方法。
* 在 Pydantic V1 中，如果您使用普通（即非 Pydantic）数据类作为字段，父类型的配置将被用作数据类本身的配置。在 Pydantic V2 中，情况不再如此。
    * 在 Pydantic V2 中，要覆盖配置（就像您在 `BaseModel` 上使用 `model_config` 一样），您可以使用 `@dataclass` 装饰器上的 `config` 参数。
        有关示例，请参阅[数据类配置](concepts/dataclasses.md#dataclass-config)。

### 配置的变更

* 在 Pydantic V2 中，要在模型上指定配置，您应该设置一个名为 `model_config` 的类属性，该属性是一个包含您想要用作配置的键/值对的字典。Pydantic V1 在父 `BaseModel` 子类的命名空间中创建名为 `Config` 的类的行为现在已被弃用。

* 当子类化模型时，`model_config` 属性会被继承。这在您希望为许多模型使用具有给定配置的基类时很有帮助。请注意，如果您从多个 `BaseModel` 子类继承，例如 `class MyModel(Model1, Model2)`，来自两个模型的 `model_config` 属性中的非默认设置将被合并，对于在两个模型中定义的任何设置，来自 `Model2` 的设置将覆盖来自 `Model1` 的设置。

* 以下配置设置已被移除：
    * `allow_mutation` — 这已被移除。您应该能够等效地使用 [frozen](api/config.md#pydantic.config.ConfigDict)（与当前使用相反）。
    * `error_msg_templates`
    * `fields` — 这是各种错误的来源，因此已被移除。
      您应该能够使用 `Annotated` 在字段上按需修改它们。
    * `getter_dict` — `orm_mode` 已被移除，此实现细节不再必要。
    * `smart_union` - Pydantic V2 中的默认 `union_mode` 是 `'smart'`。
    * `underscore_attrs_are_private` — Pydantic V2 的行为现在与在 Pydantic V1 中始终设置为 `True` 相同。
    * `json_loads`
    * `json_dumps`
    * `copy_on_model_validation`
    * `post_init_call`

* 以下配置设置已重命名：
    * `allow_population_by_field_name` → `populate_by_name`（或从 v2.11 开始使用 `validate_by_name`）
    * `anystr_lower` → `str_to_lower`
    * `anystr_strip_whitespace` → `str_strip_whitespace`
    * `anystr_upper` → `str_to_upper`
    * `keep_untouched` → `ignored_types`
    * `max_anystr_length` → `str_max_length`
    * `min_anystr_length` → `str_min_length`
    * `orm_mode` → `from_attributes`
    * `schema_extra` → `json_schema_extra`
    * `validate_all` → `validate_default`

有关更多详细信息，请参阅 [`ConfigDict` API 参考][pydantic.config.ConfigDict]。

### 验证器的变更

#### `@validator` 和 `@root_validator` 已弃用

* `@validator` 已被弃用，应替换为 [`@field_validator`](concepts/validators.md)，它提供了各种新功能和改进。
    * 新的 `@field_validator` 装饰器没有 `each_item` 关键字参数；您想要应用于泛型容器内项目的验证器应通过注释类型参数来添加。有关详细信息，请参阅[Annotated 元数据中的验证器](concepts/types.md#using-the-annotated-pattern)。
        这看起来像 `list[Annotated[int, Field(ge=0)]]`
    * 即使您继续使用已弃用的 `@validator` 装饰器，您也不能再向验证器函数的签名添加 `field` 或 `config` 参数。如果您需要访问这些参数，您需要迁移到 `@field_validator` — 有关更多详细信息，请参阅[下一节](#changes-to-validators-allowed-signatures)。
    * 如果您使用 `always=True` 关键字参数到验证器函数，请注意注释类型的标准验证器*也*将应用于默认值，而不仅仅是自定义验证器。例如，尽管下面的验证器永远不会出错，但以下代码会引发 `ValidationError`：

!!! note
    为避免这种情况，您可以使用 `Field` 函数中的 `validate_default` 参数。当设置为 `True` 时，它模拟了 Pydantic v1 中 `always=True` 的行为。但是，鼓励使用新的 `validate_default` 方式，因为它提供了更多的灵活性和控制。

```python {test="skip"}
from pydantic import BaseModel, validator


class Model(BaseModel):
    x: str = 1

    @validator('x', always=True)
    @classmethod
    def validate_x(cls, v):
        return v


Model()
```

* `@root_validator` 已被弃用，应替换为
    [`@model_validator`](api/functional_validators.md#pydantic.functional_validators.model_validator)，它也提供了新功能和改进。
    * 在某些情况下（例如当 `model_config['validate_assignment'] is True` 时进行赋值），
        `@model_validator` 装饰器将接收模型的实例，而不是值的字典。您可能需要小心处理这种情况。
    * 即使您继续使用已弃用的 `@root_validator` 装饰器，由于验证逻辑的重构，
        您不能再使用 `skip_on_failure=False` 运行（这是此关键字参数的默认值，因此必须显式设置为 `True`）。

#### `@validator` 允许签名的变更 {#changes-to-validators-allowed-signatures}

在 Pydantic V1 中，由 `@validator` 包装的函数可以接收带有关于正在验证内容的元数据的关键字参数。其中一些参数已从 Pydantic V2 中的 `@field_validator` 中移除：

* `config`：Pydantic V2 的配置现在是一个字典而不是类，这意味着此参数不再向后兼容。如果您需要访问配置，您应该迁移到 `@field_validator` 并使用 `info.config`。
* `field`：此参数过去是一个 `ModelField` 对象，这是一个准内部类，在 Pydantic V2 中不再存在。
    通过使用 `info.field_name` 中的字段名索引到 `cls.model_fields` 中，仍然可以访问大部分此信息。

```python
from pydantic import BaseModel, ValidationInfo, field_validator


class Model(BaseModel):
    x: int

    @field_validator('x')
    def val_x(cls, v: int, info: ValidationInfo) -> int:
        assert info.config is not None
        print(info.config.get('title'))
        #> Model
        print(cls.model_fields[info.field_name].is_required())
        #> True
        return v


Model(x=1)
```

#### 验证器中 `TypeError` 不再转换为 `ValidationError`

以前，在验证器函数中引发 `TypeError` 时，该错误将被包装到 `ValidationError` 中，并且在某些情况下（例如使用 FastAPI），这些错误可能会显示给最终用户。这导致了各种不良行为 &mdash; 例如，使用错误签名调用函数可能会产生面向用户的 `ValidationError`。

然而，在 Pydantic V2 中，当在验证器中引发 `TypeError` 时，它不再转换为 `ValidationError`：

```python
import pytest

from pydantic import BaseModel, field_validator


class Model(BaseModel):
    x: int

    @field_validator('x')
    def val_x(cls, v: int) -> int:
        return str.lower(v)  # 引发 TypeError


with pytest.raises(TypeError):
    Model(x=1)
```

这适用于所有验证装饰器。

#### 验证器行为变更

Pydantic V2 包含一些类型强制转换的更改。例如：

* 将 `int`、`float` 和 `Decimal` 值强制转换为字符串现在是可选的，默认情况下禁用，请参阅
  [将数字强制转换为字符串][pydantic.config.ConfigDict.coerce_numbers_to_str]。
* 成对的可迭代对象不再强制转换为字典。

有关 Pydantic V2 类型强制转换默认值的详细信息，请参阅[转换表](concepts/conversion_table.md)。

#### `allow_reuse` 关键字参数不再必要

以前，Pydantic 跟踪装饰器中的"重用"函数，因为这是一个常见的错误来源。
我们通过比较函数的完全限定名（模块名 + 函数名）来实现这一点，这可能导致误报。
当有意重用时，可以使用 `allow_reuse` 关键字参数来禁用此功能。

我们检测重复定义函数的方法已经彻底改革，现在只对在单个类内重新定义报错，
减少了误报，并使行为更符合类型检查器和 linter 在单个类定义中多次定义同名方法时会给出的错误。

在几乎所有情况下，如果您使用了 `allow_reuse=True`，您应该能够简单地删除该关键字参数，
并让一切按预期继续工作。

#### `@validate_arguments` 已重命名为 `@validate_call`

在 Pydantic V2 中，`@validate_arguments` 装饰器已重命名为 `@validate_call`。

在 Pydantic V1 中，装饰的函数添加了各种属性，例如 `raw_function` 和 `validate`
（可用于验证参数而无需实际调用装饰的函数）。由于这些属性的使用有限，以及实现中面向性能的更改，
我们未在 `@validate_call` 中保留此功能。

### 输入类型不保留

在 Pydantic V1 中，我们努力保留泛型集合的所有字段输入类型，当它们是字段注释的适当子类型时。例如，给定注释 `Mapping[str, int]`，如果您传入 `collection.Counter()`，您将得到 `collection.Counter()` 作为值。

在 V2 中支持此行为将对一般情况产生负面性能影响（我们必须每次都检查类型），并且会给验证增加很多复杂性。此外，即使在 V1 中，此行为也不一致且部分损坏：它对许多类型（`str`、`UUID` 等）不起作用，并且对于泛型集合，没有大量特殊情况处理，无法正确重建原始输入（考虑 `ChainMap`；重建输入是必要的，因为我们需要在验证后替换值，例如，如果强制转换字符串为整数）。

在 Pydantic V2 中，我们不再尝试在所有情况下保留输入类型；相反，我们只承诺输出类型将匹配类型注释。

回到 `Mapping` 示例，我们承诺输出将是有效的 `Mapping`，实际上它将是一个普通的 `dict`：

```python
from collections.abc import Mapping

from pydantic import TypeAdapter


class MyDict(dict):
    pass


ta = TypeAdapter(Mapping[str, int])
v = ta.validate_python(MyDict())
print(type(v))
#> <class 'dict'>
```

如果您希望输出类型是特定类型，请考虑将其注释为特定类型或实现自定义验证器：

```python
from collections.abc import Mapping
from typing import Annotated, Any, TypeVar

from pydantic import (
    TypeAdapter,
    ValidationInfo,
    ValidatorFunctionWrapHandler,
    WrapValidator,
)


def restore_input_type(
    value: Any, handler: ValidatorFunctionWrapHandler, _info: ValidationInfo
) -> Any:
    return type(value)(handler(value))


T = TypeVar('T')
PreserveType = Annotated[T, WrapValidator(restore_input_type)]


ta = TypeAdapter(PreserveType[Mapping[str, int]])


class MyDict(dict):
    pass


v = ta.validate_python(MyDict())
assert type(v) is MyDict
```

虽然我们不承诺在所有地方保留输入类型，但我们*确实*为 `BaseModel` 的子类以及数据类保留它们：

```python
import pydantic.dataclasses
from pydantic import BaseModel


class InnerModel(BaseModel):
    x: int


class OuterModel(BaseModel):
    inner: InnerModel


class SubInnerModel(InnerModel):
    y: int


m = OuterModel(inner=SubInnerModel(x=1, y=2))
print(m)
#> inner=SubInnerModel(x=1, y=2)


@pydantic.dataclasses.dataclass
class InnerDataclass:
    x: int


@pydantic.dataclasses.dataclass
class SubInnerDataclass(InnerDataclass):
    y: int


@pydantic.dataclasses.dataclass
class OuterDataclass:
    inner: InnerDataclass


d = OuterDataclass(inner=SubInnerDataclass(x=1, y=2))
print(d)
#> OuterDataclass(inner=SubInnerDataclass(x=1, y=2))
```

### 标准类型处理的变更

#### 字典

成对的可迭代对象（包括空可迭代对象）不再通过 `dict` 类型字段的验证。

#### 联合类型

虽然联合类型仍会从左到右尝试验证每个选项，但它们现在尽可能保留输入的类型，
即使正确的类型不是输入会通过验证的第一个选项。
作为演示，请考虑以下示例：

```python
from typing import Union

from pydantic import BaseModel


class Model(BaseModel):
    x: Union[int, str]


print(Model(x='1'))
#> x='1'
```

在 Pydantic V1 中，打印结果将是 `x=1`，因为该值将作为 `int` 通过验证。
在 Pydantic V2 中，我们识别该值是其中一个情况的实例，并短路标准联合验证。

要恢复到 V1 的非短路从左到右行为，请使用 `Field(union_mode='left_to_right')` 注释联合类型。
有关详细信息，请参阅[联合模式](./concepts/unions.md#union-modes)。

#### 必需、可选和可空字段 {#required-optional-and-nullable-fields}

Pydantic V2 更改了指定注释为 `Optional` 的字段是必需（即没有默认值）还是非必需（即具有 `None` 默认值或相应类型的任何其他值）的部分逻辑，现在更接近 `dataclasses` 的行为。类似地，注释为 `Any` 的字段不再具有 `None` 的默认值。

下表描述了 V2 中字段注释的行为：

| 状态                                                 | 字段定义            |
|-------------------------------------------------------|-----------------------------|
| 必需，不能为 `None`                            | `f1: str`                   |
| 非必需，不能为 `None`，默认为 `'abc'` | `f2: str = 'abc'`           |
| 必需，可以为 `None`                               | `f3: Optional[str]`         |
| 非必需，可以为 `None`，默认为 `None`     | `f4: Optional[str] = None`  |
| 非必需，可以为 `None`，默认为 `'abc'`    | `f5: Optional[str] = 'abc'` |
| 必需，可以是任何类型（包括 `None`）          | `f6: Any`                   |
| 非必需，可以是任何类型（包括 `None`）      | `f7: Any = None`            |

!!! note
     注释为 `typing.Optional[T]` 的字段将是必需的，并且允许值为 `None`。
     这并不意味着该字段具有 `None` 的默认值。*（这是与 V1 的破坏性变更。）*

!!! note
     如果提供了任何默认值，都会使字段变为非必需。

以下是演示上述内容的代码示例：

```python
from typing import Optional

from pydantic import BaseModel, ValidationError


class Foo(BaseModel):
    f1: str  # 必需，不能为 None
    f2: Optional[str]  # 必需，可以为 None - 与 str | None 相同
    f3: Optional[str] = None  # 非必需，可以为 None
    f4: str = 'Foobar'  # 非必需，但不能为 None


try:
    Foo(f1=None, f2=None, f4='b')
except ValidationError as e:
    print(e)
    """
    1 validation error for Foo
    f1
      Input should be a valid string [type=string_type, input_value=None, input_type=NoneType]
    """
```

#### 模式/字符串正则表达式

Pydantic V1 使用 Python 的 regex 库。Pydantic V2 使用 Rust 的 [regex crate]。
这个 crate 不仅仅是"Rust 版本的正则表达式"，它是一种完全不同的正则表达式方法。
特别是，它承诺线性时间字符串搜索，以放弃几个功能为代价（即环视和反向引用）。
我们认为这是一个值得做的权衡，特别是因为 Pydantic 用于验证不受信任的输入，确保不会因不受信任的输入而意外运行指数时间很重要。
另一方面，对于不使用这些功能的任何人来说，复杂的正则表达式验证应该快几个数量级，因为它是在 Rust 中完成的并且是线性时间。

如果您仍想使用 Python 的 regex 库，可以使用 [`regex_engine`](./api/config.md#pydantic.config.ConfigDict.regex_engine) 配置设置。

[regex crate]: https://github.com/rust-lang/regex

### 浮点数到整数的类型转换

在 V1 中，每当字段被注释为 `int` 时，任何浮点数值都会被接受，如果浮点数值包含非零小数部分，这可能导致潜在的数据丢失。在 V2 中，只有当小数部分为零时才允许从浮点数到整数的类型转换：

```python
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: int


print(Model(x=10.0))
#> x=10
try:
    Model(x=10.2)
except ValidationError as err:
    print(err)
    """
    1 validation error for Model
    x
      Input should be a valid integer, got a number with a fractional part [type=int_from_float, input_value=10.2, input_type=float]
    """
```

### `TypeAdapter` 的介绍 {#introduction-of-typeadapter}

Pydantic V1 对验证或序列化非 `BaseModel` 类型的支持较弱。

要处理这些类型，您必须创建一个"根"模型或使用 `pydantic.tools` 中的实用函数
（即 `parse_obj_as` 和 `schema_of`）。

在 Pydantic V2 中，这*容易得多*：[`TypeAdapter`][pydantic.type_adapter.TypeAdapter] 类允许您创建一个对象，
该对象具有验证、序列化和为任意类型生成 JSON 模式的方法。
这完全替代了 `parse_obj_as` 和 `schema_of`（现已弃用），
并且还涵盖了一些"根"模型的使用场景。（[`RootModel`](concepts/models.md#rootmodel-and-custom-root-types)，
[上面讨论过](#changes-to-pydanticbasemodel)，涵盖了其他场景。）

```python
from pydantic import TypeAdapter

adapter = TypeAdapter(list[int])
assert adapter.validate_python(['1', '2', '3']) == [1, 2, 3]
print(adapter.json_schema())
#> {'items': {'type': 'integer'}, 'type': 'array'}
```

由于常见类型检查器推断泛型类型的限制，在某些情况下要获得正确的类型，
您可能需要显式指定泛型参数：

```python {test="skip"}
from pydantic import TypeAdapter

adapter = TypeAdapter[str | int](str | int)
...
```

有关更多信息，请参阅[类型适配器](concepts/type_adapter.md)。

### 定义自定义类型

我们彻底改革了在 pydantic 中定义自定义类型的方式。

我们公开了用于生成 `pydantic-core` 和 JSON 模式的钩子，允许您在使用自己的自定义类型时获得 Pydantic V2 的所有性能优势。

我们还引入了使用 [`typing.Annotated`][] 向自己的类型添加自定义验证的方法。

主要变更包括：

* `__get_validators__` 应替换为 `__get_pydantic_core_schema__`。
  有关更多信息，请参阅[自定义数据类型](concepts/types.md#customizing_validation_with_get_pydantic_core_schema)。
* `__modify_schema__` 变为 `__get_pydantic_json_schema__`。
  有关更多信息，请参阅[JSON 模式自定义](concepts/json_schema.md#customizing-json-schema)。

此外，您可以使用 [`typing.Annotated`][] 通过注释类型来修改或提供类型的 `__get_pydantic_core_schema__` 和
`__get_pydantic_json_schema__` 函数，而不是修改类型本身。
这为将第三方类型与 Pydantic 集成提供了强大而灵活的机制，并且在某些情况下
可能帮助您移除 Pydantic V1 中为绕过自定义类型限制而引入的 hack。

有关更多信息，请参阅[自定义数据类型](concepts/types.md#custom-types)。

### JSON 模式生成的变更

多年来，我们收到了许多关于更改 pydantic 生成的 JSON 模式的请求。

在 Pydantic V2 中，我们尝试解决了许多常见请求：

* `Optional` 字段的 JSON 模式现在指示允许值 `null`。
* `Decimal` 类型现在在 JSON 模式中（并序列化）作为字符串公开。
* JSON 模式不再将命名元组保留为命名元组。
* 我们默认生成的 JSON 模式现在针对草案 2020-12（带有一些 OpenAPI 扩展）。
* 当它们不同时，您现在可以指定是要表示验证输入的 JSON 模式，还是序列化输出的 JSON 模式。

然而，多年来有许多合理的更改请求我们选择不实现。

在 Pydantic V1 中，即使您愿意自己实现更改，也非常困难，因为 JSON 模式
生成过程涉及各种递归函数调用；要覆盖一个，您必须复制并修改整个实现。

在 Pydantic V2 中，我们的设计目标之一是使自定义 JSON 模式生成更容易。为此，我们
引入了 [`GenerateJsonSchema`](api/json_schema.md#pydantic.json_schema.GenerateJsonSchema) 类，
它实现了将类型的 pydantic-core 模式转换为 JSON 模式。通过设计，该类将 JSON 模式生成过程分解为更小的方法，这些方法可以
在子类中轻松重写以修改生成 JSON 模式的"全局"方法。

可用于生成 JSON 模式的各种方法（例如 `BaseModel.model_json_schema` 或
`TypeAdapter.json_schema`）接受关键字参数 `schema_generator: type[GenerateJsonSchema] = GenerateJsonSchema`，
您可以将自定义子类传递给这些方法，以便使用自己的 JSON 模式生成方法。

希望这意味着如果您不同意我们做出的任何选择，或者如果您依赖于 Pydantic V1 中
在 Pydantic V2 中已更改的行为，您可以使用自定义 `schema_generator`，根据需要修改
`GenerateJsonSchema` 类以适应您的应用程序。

### `BaseSettings` 已迁移到 `pydantic-settings` {#basesettings-has-moved-to-pydantic-settings}

[`BaseSettings`](api/pydantic_settings.md#pydantic_settings.BaseSettings)，Pydantic
[设置管理](concepts/pydantic_settings.md)的基础对象，已迁移到单独的包
[`pydantic-settings`](https://github.com/pydantic/pydantic-settings)。

此外，`parse_env_var` 类方法已被移除。因此，您需要
[自定义设置源](concepts/pydantic_settings.md#customise-settings-sources)
以拥有自己的解析函数。

### 颜色和支付卡号已迁移到 `pydantic-extra-types` {#color-and-payment-card-numbers-moved-to-pydantic-extra-types}

以下特殊用途类型已迁移到
[Pydantic Extra Types](https://github.com/pydantic/pydantic-extra-types) 包，
如果需要，可以单独安装。

* [颜色类型](api/pydantic_extra_types_color.md)
* [支付卡号](api/pydantic_extra_types_payment.md)

### `pydantic.networks` 中的 URL 和 DSN 类型不再继承自 `str`

在 Pydantic V1 中，[`AnyUrl`][pydantic.networks.AnyUrl] 类型继承自 `str`，所有其他
`Url` 和 `Dsn` 类型都继承自这些类型。在 Pydantic V2 中，这些类型基于两个新的 `Url` 和 `MultiHostUrl`
类构建，使用 `Annotated`。

继承自 `str` 有优点也有缺点，对于 V2，我们决定最好移除这一点。要在期望 `str` 的 API 中使用这些
类型，您现在需要转换它们（使用 `str(url)`）。

Pydantic V2 使用 Rust 的 [Url](https://crates.io/crates/url) crate 进行 URL 验证。
一些 URL 验证与 V1 中的先前行为略有不同。
一个显著的区别是，如果不包含路径，新的 `Url` 类型会在验证版本后附加斜杠，
即使在 `Url` 类型构造函数的参数中未指定斜杠。请参阅以下示例了解此行为：

```python
from pydantic import AnyUrl

assert str(AnyUrl(url='https://google.com')) == 'https://google.com/'
assert str(AnyUrl(url='https://google.com/')) == 'https://google.com/'
assert str(AnyUrl(url='https://google.com/api')) == 'https://google.com/api'
assert str(AnyUrl(url='https://google.com/api/')) == 'https://google.com/api/'
```

如果您仍想使用没有附加斜杠的旧行为，请查看此[解决方案](https://github.com/pydantic/pydantic/issues/7186#issuecomment-1690235887)。

### 约束类型

`Constrained*` 类已被*移除*，您应该使用 `Annotated[<type>, Field(...)]` 替换它们，例如：

```python {test="skip"}
from pydantic import BaseModel, ConstrainedInt


class MyInt(ConstrainedInt):
    ge = 0


class Model(BaseModel):
    x: MyInt
```

...变为：

```python
from typing import Annotated

from pydantic import BaseModel, Field

MyInt = Annotated[int, Field(ge=0)]


class Model(BaseModel):
    x: MyInt
```

有关更多信息，请参阅[通过 `Annotated` 组合类型](concepts/types.md#using-the-annotated-pattern)文档。

对于 `ConstrainedStr`，您可以使用 [`StringConstraints`][pydantic.types.StringConstraints] 代替。

### Mypy 插件

Pydantic V2 包含一个 [mypy](https://mypy.readthedocs.io/en/stable/extending_mypy.html#configuring-mypy-to-use-plugins) 插件，位于
`pydantic.mypy` 中。

当使用 [V1 功能](migration.md#continue-using-pydantic-v1-features)时，
可能还需要启用 `pydantic.v1.mypy` 插件。

配置 mypy 插件的方法如下：

=== "`mypy.ini`"

    ```ini
    [mypy]
    plugins = pydantic.mypy, pydantic.v1.mypy  # 如果需要，包含 `.v1.mypy`。
    ```

=== "`pyproject.toml`"

    ```toml
    [tool.mypy]
    plugins = [
        "pydantic.mypy",
        "pydantic.v1.mypy",  # 如果需要，包含 `.v1.mypy`。
    ]
    ```

## 其他变更

* 放弃了对 [`email-validator<2.0.0`](https://github.com/JoshData/python-email-validator) 的支持。请确保使用
  `pip install -U email-validator` 进行更新。

## 在 Pydantic V2 中迁移的

| Pydantic V1 | Pydantic V2 |
| --- | --- |
| `pydantic.BaseSettings` | [`pydantic_settings.BaseSettings`](#basesettings-has-moved-to-pydantic-settings) |
| `pydantic.color` | [`pydantic_extra_types.color`][pydantic_extra_types.color] |
| `pydantic.types.PaymentCardBrand` | [`pydantic_extra_types.PaymentCardBrand`](#color-and-payment-card-numbers-moved-to-pydantic-extra-types) |
| `pydantic.types.PaymentCardNumber` | [`pydantic_extra_types.PaymentCardNumber`](#color-and-payment-card-numbers-moved-to-pydantic-extra-types) |
| `pydantic.utils.version_info` | [`pydantic.version.version_info`][pydantic.version.version_info] |
| `pydantic.error_wrappers.ValidationError` | [`pydantic.ValidationError`][pydantic_core.ValidationError] |
| `pydantic.utils.to_camel` | [`pydantic.alias_generators.to_pascal`][pydantic.alias_generators.to_pascal] |
| `pydantic.utils.to_lower_camel` | [`pydantic.alias_generators.to_camel`][pydantic.alias_generators.to_camel] |
| `pydantic.PyObject` | [`pydantic.ImportString`][pydantic.types.ImportString] |

## 已弃用并在 Pydantic V2 中迁移的

| Pydantic V1 | Pydantic V2 |
| --- | --- |
| `pydantic.tools.schema_of` | `pydantic.deprecated.tools.schema_of` |
| `pydantic.tools.parse_obj_as` | `pydantic.deprecated.tools.parse_obj_as` |
| `pydantic.tools.schema_json_of` | `pydantic.deprecated.tools.schema_json_of` |
| `pydantic.json.pydantic_encoder` | `pydantic.deprecated.json.pydantic_encoder` |
| `pydantic.validate_arguments` | `pydantic.deprecated.decorator.validate_arguments` |
| `pydantic.json.custom_pydantic_encoder` | `pydantic.deprecated.json.custom_pydantic_encoder` |
| `pydantic.json.ENCODERS_BY_TYPE` | `pydantic.deprecated.json.ENCODERS_BY_TYPE` |
| `pydantic.json.timedelta_isoformat` | `pydantic.deprecated.json.timedelta_isoformat` |
| `pydantic.decorator.validate_arguments` | `pydantic.deprecated.decorator.validate_arguments` |
| `pydantic.class_validators.validator` | `pydantic.deprecated.class_validators.validator` |
| `pydantic.class_validators.root_validator` | `pydantic.deprecated.class_validators.root_validator` |
| `pydantic.utils.deep_update` | `pydantic.v1.utils.deep_update` |
| `pydantic.utils.GetterDict` | `pydantic.v1.utils.GetterDict` |
| `pydantic.utils.lenient_issubclass` | `pydantic.v1.utils.lenient_issubclass` |
| `pydantic.utils.lenient_isinstance` | `pydantic.v1.utils.lenient_isinstance` |
| `pydantic.utils.is_valid_field` | `pydantic.v1.utils.is_valid_field` |
| `pydantic.utils.update_not_none` | `pydantic.v1.utils.update_not_none` |
| `pydantic.utils.import_string` | `pydantic.v1.utils.import_string` |
| `pydantic.utils.Representation` | `pydantic.v1.utils.Representation` |
| `pydantic.utils.ROOT_KEY` | `pydantic.v1.utils.ROOT_KEY` |
| `pydantic.utils.smart_deepcopy` | `pydantic.v1.utils.smart_deepcopy` |
| `pydantic.utils.sequence_like` | `pydantic.v1.utils.sequence_like` |

## 在 Pydantic V2 中移除的

* `pydantic.ConstrainedBytes`
* `pydantic.ConstrainedDate`
* `pydantic.ConstrainedDecimal`
* `pydantic.ConstrainedFloat`
* `pydantic.ConstrainedFrozenSet`
* `pydantic.ConstrainedInt`
* `pydantic.ConstrainedList`
* `pydantic.ConstrainedSet`
* `pydantic.ConstrainedStr`
* `pydantic.JsonWrapper`
* `pydantic.NoneBytes`
    * 这是 `None | bytes` 的别名。
* `pydantic.NoneStr`
    * 这是 `None | str` 的别名。
* `pydantic.NoneStrBytes`
    * 这是 `None | str | bytes` 的别名。
* `pydantic.Protocol`
* `pydantic.Required`
* `pydantic.StrBytes`
    * 这是 `str | bytes` 的别名。
* `pydantic.compiled`
* `pydantic.config.get_config`
* `pydantic.config.inherit_config`
* `pydantic.config.prepare_config`
* `pydantic.create_model_from_namedtuple`
* `pydantic.create_model_from_typeddict`
* `pydantic.dataclasses.create_pydantic_model_from_dataclass`
* `pydantic.dataclasses.make_dataclass_validator`
* `pydantic.dataclasses.set_validation`
* `pydantic.datetime_parse.parse_date`
* `pydantic.datetime_parse.parse_time`
* `pydantic.datetime_parse.parse_datetime`
* `pydantic.datetime_parse.parse_duration`
* `pydantic.error_wrappers.ErrorWrapper`
* `pydantic.errors.AnyStrMaxLengthError`
* `pydantic.errors.AnyStrMinLengthError`
* `pydantic.errors.ArbitraryTypeError`
* `pydantic.errors.BoolError`
* `pydantic.errors.BytesError`
* `pydantic.errors.CallableError`
* `pydantic.errors.ClassError`
* `pydantic.errors.ColorError`
* `pydantic.errors.ConfigError`
* `pydantic.errors.DataclassTypeError`
* `pydantic.errors.DateError`
* `pydantic.errors.DateNotInTheFutureError`
* `pydantic.errors.DateNotInThePastError`
* `pydantic.errors.DateTimeError`
* `pydantic.errors.DecimalError`
* `pydantic.errors.DecimalIsNotFiniteError`
* `pydantic.errors.DecimalMaxDigitsError`
* `pydantic.errors.DecimalMaxPlacesError`
* `pydantic.errors.DecimalWholeDigitsError`
* `pydantic.errors.DictError`
* `pydantic.errors.DurationError`
* `pydantic.errors.EmailError`
* `pydantic.errors.EnumError`
* `pydantic.errors.EnumMemberError`
* `pydantic.errors.ExtraError`
* `pydantic.errors.FloatError`
* `pydantic.errors.FrozenSetError`
* `pydantic.errors.FrozenSetMaxLengthError`
* `pydantic.errors.FrozenSetMinLengthError`
* `pydantic.errors.HashableError`
* `pydantic.errors.IPv4AddressError`
* `pydantic.errors.IPv4InterfaceError`
* `pydantic.errors.IPv4NetworkError`
* `pydantic.errors.IPv6AddressError`
* `pydantic.errors.IPv6InterfaceError`
* `pydantic.errors.IPv6NetworkError`
* `pydantic.errors.IPvAnyAddressError`
* `pydantic.errors.IPvAnyInterfaceError`
* `pydantic.errors.IPvAnyNetworkError`
* `pydantic.errors.IntEnumError`
* `pydantic.errors.IntegerError`
* `pydantic.errors.InvalidByteSize`
* `pydantic.errors.InvalidByteSizeUnit`
* `pydantic.errors.InvalidDiscriminator`
* `pydantic.errors.InvalidLengthForBrand`
* `pydantic.errors.JsonError`
* `pydantic.errors.JsonTypeError`
* `pydantic.errors.ListError`
* `pydantic.errors.ListMaxLengthError`
* `pydantic.errors.ListMinLengthError`
* `pydantic.errors.ListUniqueItemsError`
* `pydantic.errors.LuhnValidationError`
* `pydantic.errors.MissingDiscriminator`
* `pydantic.errors.MissingError`
* `pydantic.errors.NoneIsAllowedError`
* `pydantic.errors.NoneIsNotAllowedError`
* `pydantic.errors.NotDigitError`
* `pydantic.errors.NotNoneError`
* `pydantic.errors.NumberNotGeError`
* `pydantic.errors.NumberNotGtError`
* `pydantic.errors.NumberNotLeError`
* `pydantic.errors.NumberNotLtError`
* `pydantic.errors.NumberNotMultipleError`
* `pydantic.errors.PathError`
* `pydantic.errors.PathNotADirectoryError`
* `pydantic.errors.PathNotAFileError`
* `pydantic.errors.PathNotExistsError`
* `pydantic.errors.PatternError`
* `pydantic.errors.PyObjectError`
* `pydantic.errors.PydanticTypeError`
* `pydantic.errors.PydanticValueError`
* `pydantic.errors.SequenceError`
* `pydantic.errors.SetError`
* `pydantic.errors.SetMaxLengthError`
* `pydantic.errors.SetMinLengthError`
* `pydantic.errors.StrError`
* `pydantic.errors.StrRegexError`
* `pydantic.errors.StrictBoolError`
* `pydantic.errors.SubclassError`
* `pydantic.errors.TimeError`
* `pydantic.errors.TupleError`
* `pydantic.errors.TupleLengthError`
* `pydantic.errors.UUIDError`
* `pydantic.errors.UUIDVersionError`
* `pydantic.errors.UrlError`
* `pydantic.errors.UrlExtraError`
* `pydantic.errors.UrlHostError`
* `pydantic.errors.UrlHostTldError`
* `pydantic.errors.UrlPortError`
* `pydantic.errors.UrlSchemeError`
* `pydantic.errors.UrlSchemePermittedError`
* `pydantic.errors.UrlUserInfoError`
* `pydantic.errors.WrongConstantError`
* `pydantic.main.validate_model`
* `pydantic.networks.stricturl`
* `pydantic.parse_file_as`
* `pydantic.parse_raw_as`
* `pydantic.stricturl`
* `pydantic.tools.parse_file_as`
* `pydantic.tools.parse_raw_as`
* `pydantic.types.JsonWrapper`
* `pydantic.types.NoneBytes`
* `pydantic.types.NoneStr`
* `pydantic.types.NoneStrBytes`
* `pydantic.types.PyObject`
* `pydantic.types.StrBytes`
* `pydantic.typing.evaluate_forwardref`
* `pydantic.typing.AbstractSetIntStr`
* `pydantic.typing.AnyCallable`
* `pydantic.typing.AnyClassMethod`
* `pydantic.typing.CallableGenerator`
* `pydantic.typing.DictAny`
* `pydantic.typing.DictIntStrAny`
* `pydantic.typing.DictStrAny`
* `pydantic.typing.IntStr`
* `pydantic.typing.ListStr`
* `pydantic.typing.MappingIntStrAny`
* `pydantic.typing.NoArgAnyCallable`
* `pydantic.typing.NoneType`
* `pydantic.typing.ReprArgs`
* `pydantic.typing.SetStr`
* `pydantic.typing.StrPath`
* `pydantic.typing.TupleGenerator`
* `pydantic.typing.WithArgsTypes`
* `pydantic.typing.all_literal_values`
* `pydantic.typing.display_as_type`
* `pydantic.typing.get_all_type_hints`
* `pydantic.typing.get_args`
* `pydantic.typing.get_origin`
* `pydantic.typing.get_sub_types`
* `pydantic.typing.is_callable_type`
* `pydantic.typing.is_classvar`
* `pydantic.typing.is_finalvar`
* `pydantic.typing.is_literal_type`
* `pydantic.typing.is_namedtuple`
* `pydantic.typing.is_new_type`
* `pydantic.typing.is_none_type`
* `pydantic.typing.is_typeddict`
* `pydantic.typing.is_typeddict_special`
* `pydantic.typing.is_union`
* `pydantic.typing.new_type_supertype`
* `pydantic.typing.resolve_annotations`
* `pydantic.typing.typing_base`
* `pydantic.typing.update_field_forward_refs`
* `pydantic.typing.update_model_forward_refs`
* `pydantic.utils.ClassAttribute`
* `pydantic.utils.DUNDER_ATTRIBUTES`
* `pydantic.utils.PyObjectStr`
* `pydantic.utils.ValueItems`
* `pydantic.utils.almost_equal_floats`
* `pydantic.utils.get_discriminator_alias_and_values`
* `pydantic.utils.get_model`
* `pydantic.utils.get_unique_discriminator_alias`
* `pydantic.utils.in_ipython`
* `pydantic.utils.is_valid_identifier`
* `pydantic.utils.path_type`
* `pydantic.utils.validate_field_name`
* `pydantic.validate_model`