---
subtitle: 验证 HTTP 请求数据
description: 使用 Pydantic 验证 HTTP 请求数据：学习如何在 FastAPI、Flask、Django 和 HTTPX 等 Web 框架中使用 Pydantic 模型验证请求和响应数据，包括完整的代码示例和实现方法。
---

Pydantic 模型是验证和序列化请求和响应数据的绝佳方式。
Pydantic 在许多 Web 框架和库中发挥着重要作用，例如 FastAPI、Django、Flask 和 HTTPX。

## `httpx` 请求

[`httpx`](https://www.python-httpx.org/) 是一个用于 Python 3 的 HTTP 客户端，具有同步和异步 API。
在下面的示例中，我们查询 [JSONPlaceholder API](https://jsonplaceholder.typicode.com/) 来获取用户数据，并使用 Pydantic 模型进行验证。

```python {test="skip"}
import httpx

from pydantic import BaseModel, EmailStr


class User(BaseModel):
    id: int
    name: str
    email: EmailStr


url = 'https://jsonplaceholder.typicode.com/users/1'

response = httpx.get(url)
response.raise_for_status()

user = User.model_validate(response.json())
print(repr(user))
#> User(id=1, name='Leanne Graham', email='Sincere@april.biz')
```

Pydantic 的 [`TypeAdapter`][pydantic.type_adapter.TypeAdapter] 工具在处理 HTTP 请求时非常方便。
考虑一个类似的示例，我们正在验证用户列表：

```python {test="skip"}
from pprint import pprint

import httpx

from pydantic import BaseModel, EmailStr, TypeAdapter


class User(BaseModel):
    id: int
    name: str
    email: EmailStr


url = 'https://jsonplaceholder.typicode.com/users/'  # (1)!

response = httpx.get(url)
response.raise_for_status()

users_list_adapter = TypeAdapter(list[User])

users = users_list_adapter.validate_python(response.json())
pprint([u.name for u in users])
"""
['Leanne Graham',
 'Ervin Howell',
 'Clementine Bauch',
 'Patricia Lebsack',
 'Chelsey Dietrich',
 'Mrs. Dennis Schulist',
 'Kurtis Weissnat',
 'Nicholas Runolfsdottir V',
 'Glenna Reichert',
 'Clementina DuBuque']
"""
```

1. 注意，我们在这里查询 `/users/` 端点来获取用户列表。

<!-- TODO: httpx, flask, Django rest framework, FastAPI -->