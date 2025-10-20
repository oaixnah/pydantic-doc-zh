---
subtitle: 解析注解
---

!!! note
    本节是*内部*文档的一部分，主要面向贡献者。

Pydantic 在运行时严重依赖[类型提示][type hint]来构建用于验证、序列化等的模式。

虽然类型提示主要是为静态类型检查器（如 [Mypy] 或 [Pyright]）引入的，但它们在运行时是可访问的（有时会被求值）。这意味着以下代码在运行时将失败，因为 `Node` 在当前模块中尚未定义：

```python {test="skip" lint="skip"}
class Node:
    """二叉树节点。"""

    # NameError: name 'Node' is not defined:
    def __init__(self, l: Node, r: Node) -> None:
        self.left = l
        self.right = r
```

为了规避这个问题，可以使用前向引用（通过将注解用引号括起来）。

在 Python 3.7 中，[PEP 563] 引入了*延迟注解求值*的概念，意味着使用 `from __future__ import annotations` [future statement] 时，类型提示默认会被字符串化：

```python {requires="3.12" lint="skip"}
from __future__ import annotations

from pydantic import BaseModel


class Foo(BaseModel):
    f: MyType
    # 给定上面的 future 导入，这等价于：
    # f: 'MyType'


type MyType = int

print(Foo.__annotations__)
#> {'f': 'MyType'}
```

## 运行时求值的挑战

静态类型检查器利用<abbr title="抽象语法树">AST</abbr>来分析已定义的注解。
对于前面的示例，这样做的好处是能够在分析 `Foo` 的类定义时理解 `MyType` 指的是什么，即使 `MyType` 在运行时尚未定义。

然而，对于像 Pydantic 这样的运行时工具，正确解析这些前向注解更具挑战性。
Python 标准库提供了一些工具来实现这一点（[`typing.get_type_hints()`][typing.get_type_hints],
[`inspect.get_annotations()`][inspect.get_annotations]），但它们有一些局限性。因此，这些工具正在 Pydantic 中重新实现，以改进对边缘情况的支持。

随着 Pydantic 的发展，它已经适应了支持许多需要不规则注解求值模式的边缘情况。
其中一些用例从静态类型检查的角度来看不一定合理。在 v2.10 中，内部逻辑被重构，试图简化和标准化注解求值。
诚然，向后兼容性带来了一些挑战，并且由于这个原因，代码库中仍然存在一些明显的遗留问题。
希望 [PEP 649]（在 Python 3.14 中引入）将大大简化这个过程，特别是在处理函数的局部变量时。

为了求值前向引用，Pydantic 大致遵循 [`typing.get_type_hints()`][typing.get_type_hints] 函数文档中描述的逻辑。
也就是说，通过传递前向引用、全局命名空间和局部命名空间来使用内置的 [`eval()`][eval] 函数。
命名空间获取逻辑在下面的章节中定义。

## 在类定义时解析注解 {#resolving-annotations-at-class-definition}

以下示例将在本节中作为参考：

```python {test="skip" lint="skip"}
# module1.py:
type MyType = int

class Base:
    f1: 'MyType'

# module2.py:
from pydantic import BaseModel

from module1 import Base

type MyType = str


def inner() -> None:
    type InnerType = bool

    class Model(BaseModel, Base):
        type LocalType = bytes

        f2: 'MyType'
        f3: 'InnerType'
        f4: 'LocalType'
        f5: 'UnknownType'

    type InnerType2 = complex
```

当 `Model` 类正在构建时，不同的[命名空间][namespace]在起作用。对于 `Model` 的[MRO][method resolution order]中的每个基类（按相反顺序——即从 `Base` 开始），应用以下逻辑：

1. 从当前基类的 `__dict__` 中获取 `__annotations__` 键（如果存在）。对于 `Base`，这将是 `{'f1': 'MyType'}`。
2. 遍历 `__annotations__` 项，并尝试使用围绕内置 [`eval()`][eval] 函数的自定义包装器来求值注解[^1]。此函数接受两个 `globals` 和 `locals` 参数：
     * 当前模块的 `__dict__` 自然用作 `globals`。对于 `Base`，这将是 `sys.modules['module1'].__dict__`。
     * 对于 `locals` 参数，Pydantic 将尝试按以下优先级顺序在以下命名空间中解析符号：
         * 一个即时创建的命名空间，包含当前类名（`{cls.__name__: cls}`）。这样做是为了支持递归引用。
         * 当前类的局部变量（即 `cls.__dict__`）。对于 `Model`，这将包括 `LocalType`。
         * 类的父命名空间，如果与上述 globals 不同。这是类正在定义的帧的[locals][frame.f_locals]。对于 `Base`，因为类直接在模块中定义，所以不会使用此命名空间，因为它将导致再次使用 globals。对于 `Model`，父命名空间是 `inner()` 帧的局部变量。
3. 如果注解求值失败，则保持原样，以便可以在稍后阶段重新构建模型。`f5` 就是这种情况。

下表列出了 `Model` 类创建后每个字段的已解析类型注解：

| 字段名 | 已解析的注解 |
|--------|--------------|
| `f1`   | [`int`][]    |
| `f2`   | [`str`][]    |
| `f3`   | [`bool`][]   |
| `f4`   | [`bytes`][]  |
| `f5`   | `'UnknownType'` |

### 局限性和向后兼容性问题

虽然命名空间获取逻辑试图尽可能准确，但我们仍然面临一些局限性：

<div class="annotate" markdown>

* 当前类的局部变量（`cls.__dict__`）可能包含不相关的条目，其中大部分是双下划线属性。
  这意味着以下注解：`f: '__doc__'` 将成功（且意外地）被解析。
* 当 `Model` 类在函数内部创建时，我们会保留帧的[locals][frame.f_locals]的副本。
  此副本仅包含 `Model` 正在定义时局部变量中定义的符号，这意味着 `InnerType2` 不会被包含在内
  （并且如果在稍后点进行模型重建，也**不会**被包含！）。
    * 为了避免内存泄漏，我们对函数的局部变量使用[弱引用][weakref]，这意味着一些前向引用可能在函数外部无法解析（1）。
    * 函数的局部变量仅对 Pydantic 模型考虑，但此模式不适用于数据类、类型化字典或命名元组。

</div>

1. 以下是一个示例：

    ```python {test="skip" lint="skip"}
    def func():
        A = int

        class Model(BaseModel):
            f: 'A | Forward'

        return Model


    Model = func()

    Model.model_rebuild(_types_namespace={'Forward': str})
    # pydantic.errors.PydanticUndefinedAnnotation: name 'A' is not defined
    ```

出于向后兼容性的原因，并且为了能够支持有效的用例而无需重建模型，
上述命名空间逻辑在核心模式生成时略有不同。
以以下示例为例：
{#backwards-compatibility-logic}

```python
from dataclasses import dataclass

from pydantic import BaseModel


@dataclass
class Foo:
    a: 'Bar | None' = None


class Bar(BaseModel):
    b: Foo
```

一旦 `Bar` 的字段被收集（意味着注解已解析），`GenerateSchema` 类将每个字段转换为核心模式。
当它遇到另一个类字段类型（如数据类）时，它将尝试求值注解，大致遵循[上述描述的逻辑](#resolving-annotations-at-class-definition)。
然而，为了求值 `'Bar | None'` 注解，`Bar` 需要出现在 globals 或 locals 中，这通常*不是*情况：`Bar` 正在创建中，因此此时它没有被"分配"到当前模块的 `__dict__` 中。

为了避免必须在 `Bar` 上调用 [`model_rebuild()`][pydantic.BaseModel.model_rebuild]，父命名空间
（如果 `Bar` 要在函数内部定义，以及[模型重建期间提供的命名空间](#model-rebuild-semantics)）
和 `{Bar.__name__: Bar}` 命名空间在 `Foo` 的注解求值期间都包含在 locals 中
（优先级最低）（1）。
{ .annotate }

1. 这种向后兼容性逻辑可能会引入一些不一致性，例如以下情况：

    ```python {lint="skip"}
    from dataclasses import dataclass

    from pydantic import BaseModel


    @dataclass
    class Foo:
        # `a` 和 `b` 不应该解析：
        a: 'Model'
        b: 'Inner'


    def func():
        Inner = int

        class Model(BaseModel):
            foo: Foo

        Model.__pydantic_complete__
        #> True, 应该是 False。
    ```

## 重建模型时解析注解

当前向引用求值失败时，Pydantic 将静默失败并停止核心模式生成过程。
这可以通过检查模型类的 `__pydantic_core_schema__` 来看到：

```python {lint="skip"}
from pydantic import BaseModel


class Foo(BaseModel):
    f: 'MyType'


Foo.__pydantic_core_schema__
#> <pydantic._internal._mock_val_ser.MockCoreSchema object at 0x73cd0d9e6d00>
```

如果您随后正确定义 `MyType`，您可以重建模型：

```python {test="skip" lint="skip"}
type MyType = int

Foo.model_rebuild()
Foo.__pydantic_core_schema__
#> {'type': 'model', 'schema': {...}, ...}
```

[`model_rebuild()`][pydantic.BaseModel.model_rebuild] 方法使用*重建命名空间*，具有以下语义：
{#model-rebuild-semantics}

* 如果提供了显式的 `_types_namespace` 参数，则将其用作重建命名空间。
* 如果没有提供命名空间，则调用该方法的命名空间将用作重建命名空间。

此*重建命名空间*将与模型的父命名空间（如果它在函数中定义）合并并按原样使用
（参见上述[向后兼容性逻辑](#backwards-compatibility-logic)）。

[Mypy]: https://www.mypy-lang.org/
[Pyright]: https://github.com/microsoft/pyright/
[PEP 563]: https://peps.python.org/pep-0563/
[PEP 649]: https://peps.python.org/pep-0649/
[future statement]: https://docs.python.org/3/reference/simple_stmts.html#future

[^1]: 这是无条件完成的，因为前向注解可能*仅作为*类型提示的一部分出现（例如 `Optional['int']`），
      如[类型规范](https://typing.readthedocs.io/en/latest/spec/annotations.html#string-annotations)所规定。