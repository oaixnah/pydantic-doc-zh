---
subtitle: 验证 ORM 数据
description: Pydantic 是定义 ORM（对象关系映射）库模型的绝佳工具，可用于将对象映射到数据库表。本文档介绍了 Pydantic 与 SQLAlchemy 的集成方法，展示了如何通过别名功能避免字段冲突，同时提供了代码示例演示如何验证 ORM 数据。
---

Pydantic 是定义 ORM（对象关系映射）库模型的绝佳工具。
ORM 用于将对象映射到数据库表，反之亦然。

## SQLAlchemy

Pydantic 可以与 SQLAlchemy 配合使用，因为它可以用于定义数据库模型的模式。

!!! warning "代码重复"
    如果您将 Pydantic 与 SQLAlchemy 一起使用，可能会遇到代码重复的困扰。
    如果您遇到这种困难，也可以考虑使用 [`SQLModel`](https://sqlmodel.tiangolo.com/)，它将 Pydantic 与 SQLAlchemy 集成，从而消除了大部分代码重复。

如果您更倾向于使用纯 Pydantic 与 SQLAlchemy，我们建议将 Pydantic 模型与 SQLAlchemy 模型一起使用，
如下面的示例所示。在这种情况下，我们利用 Pydantic 的别名功能，将 `Column` 命名为保留的 SQLAlchemy 字段之后，从而避免冲突。

```python
import sqlalchemy as sa
from sqlalchemy.orm import declarative_base

from pydantic import BaseModel, ConfigDict, Field


class MyModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    metadata: dict[str, str] = Field(alias='metadata_')


Base = declarative_base()


class MyTableModel(Base):
    __tablename__ = 'my_table'
    id = sa.Column('id', sa.Integer, primary_key=True)
    # 'metadata' 是 SQLAlchemy 的保留字段，因此添加了 '_'
    metadata_ = sa.Column('metadata', sa.JSON)


sql_model = MyTableModel(metadata_={'key': 'val'}, id=1)
pydantic_model = MyModel.model_validate(sql_model)

print(pydantic_model.model_dump())
#> {'metadata': {'key': 'val'}}
print(pydantic_model.model_dump(by_alias=True))
#> {'metadata_': {'key': 'val'}}
```

!!! note
    上面的示例之所以有效，是因为别名在字段填充时优先于字段名称。
    访问 `SQLModel` 的 `metadata` 属性将导致 `ValidationError`。

<!-- TODO: 添加 Django 与 Pydantic 模型的示例 -->