Pydantic 与 [mypy](http://mypy-lang.org) 开箱即用配合良好。

然而，Pydantic 还附带了一个 mypy 插件，该插件添加了许多重要的 Pydantic 特定功能，提高了其类型检查代码的能力。

例如，考虑以下脚本：

```python {test="skip" linenums="1"}
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class Model(BaseModel):
    age: int
    first_name = 'John'
    last_name: Optional[str] = None
    signup_ts: Optional[datetime] = None
    list_of_ints: list[int]


m = Model(age=42, list_of_ints=[1, '2', b'3'])
print(m.middle_name)  # not a model field!
Model()  # will raise a validation error for age and list_of_ints
```

没有任何特殊配置的情况下，mypy 不会捕获 [缺失的模型字段注解](../errors/usage_errors.md#model-field-missing-annotation)
以及关于 `list_of_ints` 参数的错误，而 Pydantic 可以正确解析：

```output
15: error: List item 1 has incompatible type "str"; expected "int"  [list-item]
15: error: List item 2 has incompatible type "bytes"; expected "int"  [list-item]
16: error: "Model" has no attribute "middle_name"  [attr-defined]
17: error: Missing named argument "age" for "Model"  [call-arg]
17: error: Missing named argument "list_of_ints" for "Model"  [call-arg]
```

但是 [启用插件后](#enabling-the-plugin)，它会给出正确的错误：

```output
9: error: Untyped fields disallowed  [pydantic-field]
16: error: "Model" has no attribute "middle_name"  [attr-defined]
17: error: Missing named argument "age" for "Model"  [call-arg]
17: error: Missing named argument "list_of_ints" for "Model"  [call-arg]
```

使用 pydantic mypy 插件，您可以放心地重构模型，因为知道如果字段名称或类型发生变化，mypy 会捕获任何错误。

请注意，mypy 已经支持一些功能而无需使用 Pydantic 插件，例如为 Pydantic 模型和数据类合成 `__init__` 方法。
有关其他功能的列表，请参阅 [mypy 插件功能](#mypy-plugin-capabilities)。

Pydantic mypy 插件针对最新的 mypy 版本进行了测试。旧版本可能有效但不会被测试。

## 启用插件 {#enabling-the-plugin}

要启用插件，只需将 `pydantic.mypy` 添加到您的 [mypy 配置文件](https://mypy.readthedocs.io/en/latest/config_file.html) 中的插件列表中：

=== "`mypy.ini`"

    ```ini
    [mypy]
    plugins = pydantic.mypy
    ```

=== "`pyproject.toml`"

    ```toml
    [tool.mypy]
    plugins = ['pydantic.mypy']
    ```

!!! note

    如果您使用的是 `pydantic.v1` 模型，您需要将 `pydantic.v1.mypy` 添加到您的插件列表中。

有关更多详细信息，请参阅 [插件配置](#configuring-the-plugin)。

## Mypy 插件功能 {#mypy-plugin-capabilities}

### 为 Pydantic 模型生成 `__init__` 签名

* 任何没有动态确定别名的必需字段都将作为必需的关键字参数包含在内。
* 如果 [`validate_by_name`][pydantic.ConfigDict.validate_by_name] 模型配置值设置为 `True`，生成的签名将使用字段名称而不是别名。
* [`init_forbid_extra`](#init_forbid_extra) 和 [`init_typed`](#init_typed) 插件配置值可以进一步微调合成的 `__init__` 方法。

### 为 `model_construct` 生成类型化签名

* [`model_construct`][pydantic.BaseModel.model_construct] 方法是模型验证的替代方案，当输入数据已知有效且不应解析时使用（请参阅 [文档](../concepts/models.md#creating-models-without-validation)）。
  由于此方法不执行运行时验证，静态检查对于检测错误非常重要。

### 支持冻结模型

* 如果 [`frozen`][pydantic.ConfigDict.frozen] 配置设置为 `True`，当您尝试修改模型字段时会出现错误（请参阅 [伪不可变性](../concepts/models.md#faux-immutability)）

### 尊重 `Field` 的 `default` 和 `default_factory` 类型

* 同时具有 `default` 和 `default_factory` 的字段将在静态检查期间导致错误。
* `default` 和 `default_factory` 值的类型必须与字段的类型兼容。

### 警告使用无类型字段

* 虽然定义没有注解的字段会导致 [运行时错误](../errors/usage_errors.md#model-field-missing-annotation)，但插件也会发出类型检查错误。

### 防止使用必需的动态别名

请参阅 [`warn_required_dynamic_aliases`](#warn_required_dynamic_aliases) 插件配置值的文档。

## 配置插件 {#configuring-the-plugin}

要更改插件设置的值，请在您的 mypy 配置文件中创建一个名为 `[pydantic-mypy]` 的部分，并添加您想要覆盖的设置键值对。

启用所有插件严格性标志（以及一些其他 mypy 严格性标志）的配置文件可能如下所示：

=== "`mypy.ini`"

    ```ini
    [mypy]
    plugins = pydantic.mypy

    follow_imports = silent
    warn_redundant_casts = True
    warn_unused_ignores = True
    disallow_any_generics = True
    no_implicit_reexport = True
    disallow_untyped_defs = True

    [pydantic-mypy]
    init_forbid_extra = True
    init_typed = True
    warn_required_dynamic_aliases = True
    ```

=== "`pyproject.toml`"

    ```toml
    [tool.mypy]
    plugins = ["pydantic.mypy"]

    follow_imports = "silent"
    warn_redundant_casts = true
    warn_unused_ignores = true
    disallow_any_generics = true
    no_implicit_reexport = true
    disallow_untyped_defs = true

    [tool.pydantic-mypy]
    init_forbid_extra = true
    init_typed = true
    warn_required_dynamic_aliases = true
    ```

### `init_typed`

由于 Pydantic 默认执行 [数据转换](../concepts/models.md#data-conversion)，以下代码在运行时仍然有效：

```python {test="skip" lint="skip"}
class Model(BaseModel):
    a: int


Model(a='1')
```

因此，插件在合成 `__init__` 方法时将使用 [`Any`][typing.Any] 作为字段注解，除非设置了 `init_typed` 或在模型上启用了 [严格模式](../concepts/strict_mode.md)。

### `init_forbid_extra`

默认情况下，Pydantic 允许（并忽略）任何额外提供的参数：

```python {test="skip" lint="skip"}
class Model(BaseModel):
    a: int = 1


Model(unrelated=2)
```

因此，插件在合成 `__init__` 方法时将添加一个额外的 `**kwargs: Any` 参数，除非设置了 `init_forbid_extra` 或将 [`extra`][pydantic.ConfigDict.extra] 设置为 `'forbid'`。

### `warn_required_dynamic_aliases`

是否在使用动态确定的别名或别名生成器时出错，当模型上的 [`validate_by_name`][pydantic.ConfigDict.validate_by_name] 设置为 `False` 时。如果存在这样的别名，mypy 无法正确类型检查对 `__init__` 的调用。在这种情况下，它将默认将所有参数视为非必需。

!!! note "与禁用 `Any` 的兼容性"
    一些 mypy 配置选项（例如 [`disallow_any_explicit`](https://mypy.readthedocs.io/en/stable/config_file.html#confval-disallow_any_explicit)）
    会出错，因为合成的 `__init__` 方法包含 [`Any`][typing.Any] 注解。要规避此问题，您必须同时启用 `init_forbid_extra` 和 `init_typed`。