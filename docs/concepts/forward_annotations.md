---
description: 学习 Pydantic 中的前向注解功能，包括使用字符串注解和 from future import annotations。了解如何创建自引用和递归模型，处理循环引用问题，以及在验证和序列化过程中如何安全地处理递归数据结构。包含完整的代码示例和错误处理策略。
---

前向注解（用引号包裹）或使用 `from __future__ import annotations` [future statement]
（如 [PEP563](https://www.python.org/dev/peps/pep-0563/) 中引入的）是受支持的：

```python
from __future__ import annotations

from pydantic import BaseModel

MyInt = int


class Model(BaseModel):
    a: MyInt
    # 如果没有 future 导入，等价于：
    # a: 'MyInt'


print(Model(a='1'))
#> a=1
```

如以下部分所示，当您想要引用代码中尚未定义的类型时，前向注解非常有用。

解析前向注解的内部逻辑在[此章节](../internals/resolving_annotations.md)中有详细描述。

## 自引用（或"递归"）模型 {#self-referencing-or-recursive-models}

支持具有自引用字段的模型。这些注解将在模型创建期间解析。

在模型内部，您可以添加 `from __future__ import annotations` 导入或将注解包装在字符串中：

```python
from typing import Optional

from pydantic import BaseModel


class Foo(BaseModel):
    a: int = 123
    sibling: 'Optional[Foo]' = None


print(Foo())
#> a=123 sibling=None
print(Foo(sibling={'a': '321'}))
#> a=123 sibling=Foo(a=321, sibling=None)
```

### 循环引用

在使用自引用递归模型时，您可能会在验证输入中遇到循环引用。例如，当验证具有来自属性的反向引用的 ORM 实例时，可能会发生这种情况。

Pydantic 不会在尝试验证具有循环引用的数据时引发 [`RecursionError`][]，而是能够检测到循环引用并引发适当的 [`ValidationError`][pydantic_core.ValidationError]：

```python
from typing import Optional

from pydantic import BaseModel, ValidationError


class ModelA(BaseModel):
    b: 'Optional[ModelB]' = None


class ModelB(BaseModel):
    a: Optional[ModelA] = None


cyclic_data = {}
cyclic_data['a'] = {'b': cyclic_data}
print(cyclic_data)
#> {'a': {'b': {...}}}

try:
    ModelB.model_validate(cyclic_data)
except ValidationError as exc:
    print(exc)
    """
    1 validation error for ModelB
    a.b
      Recursion error - cyclic reference detected [type=recursion_loop, input_value={'a': {'b': {...}}}, input_type=dict]
    """
```

由于此错误是在未实际超过最大递归深度的情况下引发的，您可以捕获并处理引发的 [`ValidationError`][pydantic_core.ValidationError]，而无需担心有限的剩余递归深度：

```python
from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import field

from pydantic import BaseModel, ValidationError, field_validator


def is_recursion_validation_error(exc: ValidationError) -> bool:
    errors = exc.errors()
    return len(errors) == 1 and errors[0]['type'] == 'recursion_loop'


@contextmanager
def suppress_recursion_validation_error() -> Generator[None]:
    try:
        yield
    except ValidationError as exc:
        if not is_recursion_validation_error(exc):
            raise exc


class Node(BaseModel):
    id: int
    children: list[Node] = field(default_factory=list)

    @field_validator('children', mode='wrap')
    @classmethod
    def drop_cyclic_references(cls, children, h):
        try:
            return h(children)
        except ValidationError as exc:
            if not (
                is_recursion_validation_error(exc)
                and isinstance(children, list)
            ):
                raise exc

            value_without_cyclic_refs = []
            for child in children:
                with suppress_recursion_validation_error():
                    value_without_cyclic_refs.extend(h([child]))
            return h(value_without_cyclic_refs)


# Create data with cyclic references representing the graph 1 -> 2 -> 3 -> 1
node_data = {'id': 1, 'children': [{'id': 2, 'children': [{'id': 3}]}]}
node_data['children'][0]['children'][0]['children'] = [node_data]

print(Node.model_validate(node_data))
#> id=1 children=[Node(id=2, children=[Node(id=3, children=[])])]
```

类似地，如果 Pydantic 在*序列化*期间遇到递归引用，而不是等待超过最大递归深度，会立即引发 [`ValueError`][]：

```python
from pydantic import TypeAdapter

# Create data with cyclic references representing the graph 1 -> 2 -> 3 -> 1
node_data = {'id': 1, 'children': [{'id': 2, 'children': [{'id': 3}]}]}
node_data['children'][0]['children'][0]['children'] = [node_data]

try:
    # Try serializing the circular reference as JSON
    TypeAdapter(dict).dump_json(node_data)
except ValueError as exc:
    print(exc)
    """
    Error serializing to JSON: ValueError: Circular reference detected (id repeated)
    """
```

如果需要，也可以处理这种情况：

```python
from dataclasses import field
from typing import Any

from pydantic import (
    SerializerFunctionWrapHandler,
    TypeAdapter,
    field_serializer,
)
from pydantic.dataclasses import dataclass


@dataclass
class NodeReference:
    id: int


@dataclass
class Node(NodeReference):
    children: list['Node'] = field(default_factory=list)

    @field_serializer('children', mode='wrap')
    def serialize(
        self, children: list['Node'], handler: SerializerFunctionWrapHandler
    ) -> Any:
        """
        序列化节点列表，通过排除子节点来处理循环引用。
        """
        try:
            return handler(children)
        except ValueError as exc:
            if not str(exc).startswith('Circular reference'):
                raise exc

            result = []
            for node in children:
                try:
                    serialized = handler([node])
                except ValueError as exc:
                    if not str(exc).startswith('Circular reference'):
                        raise exc
                    result.append({'id': node.id})
                else:
                    result.append(serialized)
            return result


# Create a cyclic graph:
nodes = [Node(id=1), Node(id=2), Node(id=3)]
nodes[0].children.append(nodes[1])
nodes[1].children.append(nodes[2])
nodes[2].children.append(nodes[0])

print(nodes[0])
#> Node(id=1, children=[Node(id=2, children=[Node(id=3, children=[...])])])

# Serialize the cyclic graph:
print(TypeAdapter(Node).dump_python(nodes[0]))
"""
{
    'id': 1,
    'children': [{'id': 2, 'children': [{'id': 3, 'children': [{'id': 1}]}]}],
}
"""
```

[future statement]: https://docs.python.org/3/reference/simple_stmts.html#future