!!! note
    **承认声明：** 我（Pydantic 的主要开发者）也开发了 python-devtools。

[python-devtools](https://python-devtools.helpmanual.io/) (`pip install devtools`) 提供了一系列在 Python 开发过程中有用的工具，包括 `debug()`，它是 `print()` 的替代方案，以更易于阅读的方式格式化输出，同时提供有关打印语句所在文件/行以及打印值的信息。

Pydantic 通过在大多数公共类上实现 `__pretty__` 方法与 *devtools* 集成。

特别是 `debug()` 在检查模型时非常有用：

```python {test="no-print-intercept"}
from datetime import datetime

from devtools import debug

from pydantic import BaseModel


class Address(BaseModel):
    street: str
    country: str
    lat: float
    lng: float


class User(BaseModel):
    id: int
    name: str
    signup_ts: datetime
    friends: list[int]
    address: Address


user = User(
    id='123',
    name='John Doe',
    signup_ts='2019-06-01 12:22',
    friends=[1234, 4567, 7890],
    address=dict(street='Testing', country='uk', lat=51.5, lng=0),
)
debug(user)
print('\n应该比以下内容更容易阅读：\n')
print('user:', user)
```

将在您的终端输出：

{{ devtools_example }}

!!! note
    `python-devtools` 目前还不支持 Python 3.13。