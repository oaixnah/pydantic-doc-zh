## 安装

安装非常简单：

```bash
pip install pydantic-settings
```

## 使用

如果你创建一个继承自 `BaseSettings` 的模型，模型初始化器将尝试通过从环境中读取来确定任何未作为关键字参数传递的字段的值。（如果未设置匹配的环境变量，仍将使用默认值。）

这使得以下操作变得容易：

* 创建一个明确定义、类型提示的应用程序配置类
* 自动从环境变量中读取配置的修改
* 在需要时手动覆盖初始化器中的特定设置（例如在单元测试中）

例如：

```py
from collections.abc import Callable
from typing import Any

from pydantic import (
    AliasChoices,
    AmqpDsn,
    BaseModel,
    Field,
    ImportString,
    PostgresDsn,
    RedisDsn,
)

from pydantic_settings import BaseSettings, SettingsConfigDict


class SubModel(BaseModel):
    foo: str = 'bar'
    apple: int = 1


class Settings(BaseSettings):
    auth_key: str = Field(validation_alias='my_auth_key')  # (1)!

    api_key: str = Field(alias='my_api_key')  # (2)!

    redis_dsn: RedisDsn = Field(
        'redis://user:pass@localhost:6379/1',
        validation_alias=AliasChoices('service_redis_dsn', 'redis_url'),  # (3)!
    )
    pg_dsn: PostgresDsn = 'postgres://user:pass@localhost:5432/foobar'
    amqp_dsn: AmqpDsn = 'amqp://user:pass@localhost:5672/'

    special_function: ImportString[Callable[[Any], Any]] = 'math.cos'  # (4)!

    # to override domains:
    # export my_prefix_domains='["foo.com", "bar.com"]'
    domains: set[str] = set()

    # to override more_settings:
    # export my_prefix_more_settings='{"foo": "x", "apple": 1}'
    more_settings: SubModel = SubModel()

    model_config = SettingsConfigDict(env_prefix='my_prefix_')  # (5)!


print(Settings().model_dump())
"""
{
    'auth_key': 'xxx',
    'api_key': 'xxx',
    'redis_dsn': RedisDsn('redis://user:pass@localhost:6379/1'),
    'pg_dsn': PostgresDsn('postgres://user:pass@localhost:5432/foobar'),
    'amqp_dsn': AmqpDsn('amqp://user:pass@localhost:5672/'),
    'special_function': math.cos,
    'domains': set(),
    'more_settings': {'foo': 'bar', 'apple': 1},
}
"""
```

1. 使用 `validation_alias` 覆盖环境变量名称。在这种情况下，将读取环境变量 `my_auth_key` 而不是 `auth_key`。

    查看 [`Field` 文档](fields.md) 获取更多信息。

2. 使用 `alias` 覆盖环境变量名称。在这种情况下，环境变量 `my_api_key` 将用于验证和序列化，而不是 `api_key`。

    查看 [`Field` 文档](fields.md#field-aliases) 获取更多信息。

3. [`AliasChoices`][pydantic.AliasChoices] 类允许为单个字段设置多个环境变量名称。将使用找到的第一个环境变量。

    查看 [别名选择文档](alias.md#aliaspath-and-aliaschoices) 获取更多信息。

4. [`ImportString`][pydantic.types.ImportString] 类允许从字符串导入对象。
   在这种情况下，将读取环境变量 `special_function` 并导入函数 [`math.cos`][]。

5. `env_prefix` 配置设置允许为所有环境变量设置前缀。

    查看 [环境变量名称文档](#environment-variable-names) 获取更多信息。

## 默认值验证

与 pydantic `BaseModel` 不同，`BaseSettings` 字段的默认值默认会被验证。
你可以通过在 `model_config` 中设置 `validate_default=False` 或在字段级别通过 `Field(validate_default=False)` 来禁用此行为：

```py
from pydantic import Field

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(validate_default=False)

    # 默认值不会被验证
    foo: int = 'test'


print(Settings())
#> foo='test'


class Settings1(BaseSettings):
    # 默认值不会被验证
    foo: int = Field('test', validate_default=False)


print(Settings1())
#> foo='test'
```

查看 [默认值验证](fields.md#validate-default-values) 获取更多信息。

## 环境变量名称

默认情况下，环境变量名称与字段名称相同。

你可以通过设置 `env_prefix` 配置设置或在实例化时通过 `_env_prefix` 关键字参数来更改所有环境变量的前缀：

```py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='my_prefix_')

    auth_key: str = 'xxx'  # 将从 `my_prefix_auth_key` 读取
```

!!! note
    默认的 `env_prefix` 是 `''`（空字符串）。`env_prefix` 不仅适用于环境设置，还适用于
    dotenv 文件、密钥和其他源。

如果你想更改单个字段的环境变量名称，可以使用别名。

有两种方法可以做到这一点：

* 使用 `Field(alias=...)`（参见上面的 `api_key`）
* 使用 `Field(validation_alias=...)`（参见上面的 `auth_key`）

查看 [`Field` 别名文档](fields.md#field-aliases) 获取有关别名的更多信息。

`env_prefix` 不适用于带有别名的字段。这意味着环境变量名称与字段别名相同：

```py
from pydantic import Field

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='my_prefix_')

    foo: str = Field('xxx', alias='FooAlias')  # (1)!
```

1. `env_prefix` 将被忽略，值将从 `FooAlias` 环境变量中读取。

### 大小写敏感性

默认情况下，环境变量名称是大小写不敏感的。

如果你想使环境变量名称大小写敏感，可以设置 `case_sensitive` 配置设置：

```py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=True)

    redis_host: str = 'localhost'
```

当 `case_sensitive` 为 `True` 时，环境变量名称必须与字段名称匹配（可选地带有前缀），
因此在此示例中，`redis_host` 只能通过 `export redis_host` 进行修改。如果你想将环境变量命名为全大写，
你也应该将属性命名为全大写。你仍然可以通过 `Field(validation_alias=...)` 将环境变量命名为任何你喜欢的名称。

大小写敏感性也可以通过实例化时的 `_case_sensitive` 关键字参数设置。

对于嵌套模型，`case_sensitive` 设置将应用于所有嵌套模型。

```py
import os

from pydantic import BaseModel, ValidationError

from pydantic_settings import BaseSettings


class RedisSettings(BaseModel):
    host: str
    port: int


class Settings(BaseSettings, case_sensitive=True):
    redis: RedisSettings


os.environ['redis'] = '{"host": "localhost", "port": 6379}'
print(Settings().model_dump())
#> {'redis': {'host': 'localhost', 'port': 6379}}
os.environ['redis'] = '{"HOST": "localhost", "port": 6379}'  # (1)!
try:
    Settings()
except ValidationError as e:
    print(e)
    """
    1 validation error for Settings
    redis.host
      Field required [type=missing, input_value={'HOST': 'localhost', 'port': 6379}, input_type=dict]
        有关更多信息，请访问 https://errors.pydantic.dev/2/v/missing
    """
```

1. 注意 `host` 字段未找到，因为环境变量名称是 `HOST`（全大写）。

!!! note
    在 Windows 上，Python 的 `os` 模块始终将环境变量视为大小写不敏感，因此
    `case_sensitive` 配置设置将无效 - 设置将始终忽略大小写进行更新。

## 解析环境变量值

默认情况下，环境变量按字面解析，包括值为空的情况。你可以通过将 `env_ignore_empty` 配置设置设置为 `True` 来选择忽略空环境变量。
如果你更愿意使用字段的默认值而不是来自环境的空值，这会很有用。

对于大多数简单字段类型（如 `int`、`float`、`str` 等），环境变量值的解析方式与直接传递给初始化器（作为字符串）相同。

复杂类型如 `list`、`set`、`dict` 和子模型通过将环境变量的值视为 JSON 编码的字符串来从环境中填充。

填充嵌套复杂变量的另一种方法是配置模型的 `env_nested_delimiter` 配置设置，然后使用指向嵌套模块字段名称的环境变量。
它的作用只是将你的变量分解为嵌套模型或字典。
因此，如果你定义一个变量 `FOO__BAR__BAZ=123`，它将转换为 `FOO={'BAR': {'BAZ': 123}}`
如果你有多个具有相同结构的变量，它们将被合并。

!!! note
    子模型必须继承自 `pydantic.BaseModel`，否则 `pydantic-settings` 将初始化子模型，
    单独收集子模型字段的值，你可能会得到意外的结果。

例如，给定以下环境变量：
```bash
# your environment
export V0=0
export SUB_MODEL='{"v1": "json-1", "v2": "json-2"}'
export SUB_MODEL__V2=nested-2
export SUB_MODEL__V3=3
export SUB_MODEL__DEEP__V4=v4
```

你可以将它们加载到以下设置模型中：

```py
from pydantic import BaseModel

from pydantic_settings import BaseSettings, SettingsConfigDict


class DeepSubModel(BaseModel):  # (1)!
    v4: str


class SubModel(BaseModel):  # (2)!
    v1: str
    v2: bytes
    v3: int
    deep: DeepSubModel


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_nested_delimiter='__')

    v0: str
    sub_model: SubModel


print(Settings().model_dump())
"""
{
    'v0': '0',
    'sub_model': {'v1': 'json-1', 'v2': b'nested-2', 'v3': 3, 'deep': {'v4': 'v4'}},
}
"""
```

1. 子模型必须继承自 `pydantic.BaseModel`。

2. 子模型必须继承自 `pydantic.BaseModel`。

`env_nested_delimiter` 可以通过 `model_config` 配置，如上所示，也可以通过实例化时的 `_env_nested_delimiter` 关键字参数配置。

默认情况下，环境变量按 `env_nested_delimiter` 分割为任意深度的嵌套字段。你可以使用 `env_nested_max_split` 配置设置限制嵌套字段的深度。这在两级深度设置中特别有用，其中 `env_nested_delimiter`（通常是单个 `_`）可能是模型字段名称的子字符串。例如：

```bash
# your environment
export GENERATION_LLM_PROVIDER='anthropic'
export GENERATION_LLM_API_KEY='your-api-key'
export GENERATION_LLM_API_VERSION='2024-03-15'
```

你可以将它们加载到以下设置模型中：

```py
from pydantic import BaseModel

from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMConfig(BaseModel):
    provider: str = 'openai'
    api_key: str
    api_type: str = 'azure'
    api_version: str = '2023-03-15-preview'


class GenerationConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter='_', env_nested_max_split=1, env_prefix='GENERATION_'
    )

    llm: LLMConfig
    ...


print(GenerationConfig().model_dump())
"""
{
    'llm': {
        'provider': 'anthropic',
        'api_key': 'your-api-key',
        'api_type': 'azure',
        'api_version': '2024-03-15',
    }
}
"""
```

如果没有设置 `env_nested_max_split=1`，`GENERATION_LLM_API_KEY` 将被解析为 `llm.api.key` 而不是 `llm.api_key`，并且会引发 `ValidationError`。

嵌套环境变量优先于顶级环境变量 JSON（例如，在上面的示例中，`SUB_MODEL__V2` 优先于 `SUB_MODEL`）。

你也可以通过提供自己的源类来填充复杂类型。

```py
import json
import os
from typing import Any

from pydantic.fields import FieldInfo

from pydantic_settings import (
    BaseSettings,
    EnvSettingsSource,
    PydanticBaseSettingsSource,
)


class MyCustomSource(EnvSettingsSource):
    def prepare_field_value(
        self, field_name: str, field: FieldInfo, value: Any, value_is_complex: bool
    ) -> Any:
        if field_name == 'numbers':
            return [int(x) for x in value.split(',')]
        return json.loads(value)


class Settings(BaseSettings):
    numbers: list[int]

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (MyCustomSource(settings_cls),)


os.environ['numbers'] = '1,2,3'
print(Settings().model_dump())
#> {'numbers': [1, 2, 3]}
```

### 禁用 JSON 解析

pydantic-settings 默认将环境变量中的复杂类型解析为 JSON 字符串。如果你想禁用
此行为并在自己的验证器中解析值，可以使用 [`NoDecode`](../api/pydantic_settings.md#pydantic_settings.NoDecode) 注解字段：

```py
import os
from typing import Annotated

from pydantic import field_validator

from pydantic_settings import BaseSettings, NoDecode


class Settings(BaseSettings):
    numbers: Annotated[list[int], NoDecode]  # (1)!

    @field_validator('numbers', mode='before')
    @classmethod
    def decode_numbers(cls, v: str) -> list[int]:
        return [int(x) for x in v.split(',')]


os.environ['numbers'] = '1,2,3'
print(Settings().model_dump())
#> {'numbers': [1, 2, 3]}
```

1. `NoDecode` 注解禁用 `numbers` 字段的 JSON 解析。`decode_numbers` 字段验证器将被调用来解析值。

你也可以通过将 `enable_decoding` 配置设置设置为 `False` 来禁用所有字段的 JSON 解析：

```py
import os

from pydantic import field_validator

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(enable_decoding=False)

    numbers: list[int]

    @field_validator('numbers', mode='before')
    @classmethod
    def decode_numbers(cls, v: str) -> list[int]:
        return [int(x) for x in v.split(',')]


os.environ['numbers'] = '1,2,3'
print(Settings().model_dump())
#> {'numbers': [1, 2, 3]}
```

你可以通过使用 [`ForceDecode`](../api/pydantic_settings.md#pydantic_settings.ForceDecode) 注解字段来强制进行 JSON 解析。
这将绕过 `enable_decoding` 配置设置：

```py
import os
from typing import Annotated

from pydantic import field_validator

from pydantic_settings import BaseSettings, ForceDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(enable_decoding=False)

    numbers: Annotated[list[int], ForceDecode]
    numbers1: list[int]  # (1)!

    @field_validator('numbers1', mode='before')
    @classmethod
    def decode_numbers1(cls, v: str) -> list[int]:
        return [int(x) for x in v.split(',')]


os.environ['numbers'] = '["1","2","3"]'
os.environ['numbers1'] = '1,2,3'
print(Settings().model_dump())
#> {'numbers': [1, 2, 3], 'numbers1': [1, 2, 3]}
```

1. `numbers1` 字段没有用 `ForceDecode` 注解，因此不会被解析为 JSON，我们需要提供一个自定义验证器来解析值。

## 嵌套模型默认部分更新

默认情况下，Pydantic settings 不允许对嵌套模型默认对象进行部分更新。可以通过将 `nested_model_default_partial_update` 标志设置为 `True` 来覆盖此行为，这将允许对嵌套模型默认对象字段进行部分更新。

```py
import os

from pydantic import BaseModel

from pydantic_settings import BaseSettings, SettingsConfigDict


class SubModel(BaseModel):
    val: int = 0
    flag: bool = False


class SettingsPartialUpdate(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter='__', nested_model_default_partial_update=True
    )

    nested_model: SubModel = SubModel(val=1)


class SettingsNoPartialUpdate(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter='__', nested_model_default_partial_update=False
    )

    nested_model: SubModel = SubModel(val=1)


# Apply a partial update to the default object using environment variables
os.environ['NESTED_MODEL__FLAG'] = 'True'

# When partial update is enabled, the existing SubModel instance is updated
# with nested_model.flag=True change
assert SettingsPartialUpdate().model_dump() == {
    'nested_model': {'val': 1, 'flag': True}
}

# When partial update is disabled, a new SubModel instance is instantiated
# with nested_model.flag=True change
assert SettingsNoPartialUpdate().model_dump() == {
    'nested_model': {'val': 0, 'flag': True}
}
```

## Dotenv (.env) 支持

Dotenv 文件（通常命名为 `.env`）是一种常见模式，可以轻松地以平台无关的方式使用环境变量。

Dotenv 文件遵循所有环境变量的相同一般原则，它看起来像这样：

```bash title=".env"
# 忽略注释
ENVIRONMENT="production"
REDIS_ADDRESS=localhost:6379
MEANING_OF_LIFE=42
MY_VAR='Hello world'
```

一旦你填充了 `.env` 文件，*pydantic* 支持以两种方式加载它：

1. 在 `BaseSettings` 类的 `model_config` 上设置 `env_file`（如果不想使用操作系统的默认编码，还可以设置 `env_file_encoding`）：
   ````py hl_lines="4 5"
   from pydantic_settings import BaseSettings, SettingsConfigDict


   class Settings(BaseSettings):
       model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')
   ````
2. 使用 `_env_file` 关键字参数（如果需要，还可以使用 `_env_file_encoding`）实例化 `BaseSettings` 派生类：
   ````py hl_lines="8"
   from pydantic_settings import BaseSettings, SettingsConfigDict


   class Settings(BaseSettings):
       model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')


   settings = Settings(_env_file='prod.env', _env_file_encoding='utf-8')
   ````
无论哪种情况，传递的参数值可以是任何有效的路径或文件名，可以是绝对路径，也可以是相对于当前工作目录的路径。
从那里，*pydantic* 将通过加载你的变量并验证它们来处理所有事情。

!!! note
    如果为 `env_file` 指定了文件名，Pydantic 将仅检查当前工作目录，
    不会检查任何父目录中的 `.env` 文件。

即使使用 dotenv 文件，*pydantic* 仍会读取环境变量以及 dotenv 文件，
**环境变量始终优先于从 dotenv 文件加载的值**。

通过实例化时的 `_env_file` 关键字参数传递文件路径（方法 2）将覆盖
`model_config` 类上设置的任何值。如果上述代码片段一起使用，将加载 `prod.env`
而忽略 `.env`。

如果需要加载多个 dotenv 文件，可以将多个文件路径作为元组或列表传递。文件将
按顺序加载，每个文件覆盖前一个文件。

```py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # `.env.prod` 优先于 `.env`
        env_file=('.env', '.env.prod')
    )
```

你也可以使用关键字参数覆盖来告诉 Pydantic 根本不加载任何文件（即使在
`model_config` 类中设置了文件），通过传递 `None` 作为实例化关键字参数，例如 `settings = Settings(_env_file=None)`。

由于使用 python-dotenv 来解析文件，可以使用类似 bash 的语义，如 `export`，
（取决于你的操作系统和环境）可能允许你的 dotenv 文件也与 `source` 一起使用，
有关更多详细信息，请参阅 [python-dotenv 的文档](https://saurabh-kumar.com/python-dotenv/#usages)。

Pydantic settings 在 dotenv 文件的情况下会考虑 `extra` 配置。这意味着如果你在 `model_config` 上设置 `extra=forbid`（*默认*）
并且你的 dotenv 文件包含未在设置模型中定义的字段的条目，
它将在设置构造时引发 `ValidationError`。

为了与 pydantic 1.x BaseSettings 兼容，你应该使用 `extra=ignore`：
```py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
```


!!! note
    Pydantic settings 从 dotenv 文件加载所有值并将其传递给模型，无论模型的 `env_prefix` 如何。
    因此，如果你在 dotenv 文件中提供额外值，无论它们是否以 `env_prefix` 开头，
    都会引发 `ValidationError`。

## 命令行支持

Pydantic settings 提供集成的 CLI 支持，使得使用 Pydantic 模型快速定义 CLI 应用程序变得容易。
Pydantic settings CLI 有两个主要用例：

1. 使用 CLI 覆盖 Pydantic 模型中的字段。
2. 使用 Pydantic 模型定义 CLI。

默认情况下，体验是针对用例 #1 量身定制的，并建立在 [解析环境变量](#parsing-environment-variable-values) 中建立的基础上。
如果你的用例主要属于 #2，你可能希望启用 [创建 CLI 应用程序](#creating-cli-applications) 末尾概述的大多数默认设置。

### 基础

开始之前，让我们重新审视 [解析环境变量](#parsing-environment-variable-values) 中提供的示例，但使用 Pydantic settings CLI：

```py
import sys

from pydantic import BaseModel

from pydantic_settings import BaseSettings, SettingsConfigDict


class DeepSubModel(BaseModel):
    v4: str


class SubModel(BaseModel):
    v1: str
    v2: bytes
    v3: int
    deep: DeepSubModel


class Settings(BaseSettings):
    model_config = SettingsConfigDict(cli_parse_args=True)

    v0: str
    sub_model: SubModel


sys.argv = [
    'example.py',
    '--v0=0',
    '--sub_model={"v1": "json-1", "v2": "json-2"}',
    '--sub_model.v2=nested-2',
    '--sub_model.v3=3',
    '--sub_model.deep.v4=v4',
]

print(Settings().model_dump())
"""
{
    'v0': '0',
    'sub_model': {'v1': 'json-1', 'v2': b'nested-2', 'v3': 3, 'deep': {'v4': 'v4'}},
}
"""
```

要启用 CLI 解析，我们只需将 `cli_parse_args` 标志设置为有效值，这保留了与
`argparse` 中定义的兼容性。

请注意，CLI 设置源默认是 [**最高优先级的源**](#field-value-priority)，除非其 [优先级值被自定义](#customise-settings-sources)：

```py
import os
import sys

from pydantic_settings import (
    BaseSettings,
    CliSettingsSource,
    PydanticBaseSettingsSource,
)


class Settings(BaseSettings):
    my_foo: str

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return env_settings, CliSettingsSource(settings_cls, cli_parse_args=True)


os.environ['MY_FOO'] = 'from environment'

sys.argv = ['example.py', '--my_foo=from cli']

print(Settings().model_dump())
#> {'my_foo': 'from environment'}
```

#### 列表

CLI 参数解析列表支持混合使用以下三种样式中的任何一种：

  * JSON 样式 `--field='[1,2]'`
  * Argparse 样式 `--field 1 --field 2`
  * 懒人样式 `--field=1,2`

```py
import sys

from pydantic_settings import BaseSettings


class Settings(BaseSettings, cli_parse_args=True):
    my_list: list[int]


sys.argv = ['example.py', '--my_list', '[1,2]']
print(Settings().model_dump())
#> {'my_list': [1, 2]}

sys.argv = ['example.py', '--my_list', '1', '--my_list', '2']
print(Settings().model_dump())
#> {'my_list': [1, 2]}

sys.argv = ['example.py', '--my_list', '1,2']
print(Settings().model_dump())
#> {'my_list': [1, 2]}
```

#### 字典

CLI 参数解析字典支持混合使用以下两种样式中的任何一种：

  * JSON 样式 `--field='{"k1": 1, "k2": 2}'`
  * 环境变量样式 `--field k1=1 --field k2=2`

这些也可以与列表形式结合使用，例如：

  * `--field k1=1,k2=2 --field k3=3 --field '{"k4": 4}'` 等

```py
import sys

from pydantic_settings import BaseSettings


class Settings(BaseSettings, cli_parse_args=True):
    my_dict: dict[str, int]


sys.argv = ['example.py', '--my_dict', '{"k1":1,"k2":2}']
print(Settings().model_dump())
#> {'my_dict': {'k1': 1, 'k2': 2}}

sys.argv = ['example.py', '--my_dict', 'k1=1', '--my_dict', 'k2=2']
print(Settings().model_dump())
#> {'my_dict': {'k1': 1, 'k2': 2}}
```

#### 字面量和枚举

CLI 参数解析字面量和枚举会被转换为 CLI 选项。

```py
import sys
from enum import IntEnum
from typing import Literal

from pydantic_settings import BaseSettings


class Fruit(IntEnum):
    pear = 0
    kiwi = 1
    lime = 2


class Settings(BaseSettings, cli_parse_args=True):
    fruit: Fruit
    pet: Literal['dog', 'cat', 'bird']


sys.argv = ['example.py', '--fruit', 'lime', '--pet', 'cat']
print(Settings().model_dump())
#> {'fruit': <Fruit.lime: 2>, 'pet': 'cat'}
```

#### 别名

Pydantic 字段别名会作为 CLI 参数别名添加。长度为1的别名会被转换为短选项。

```py
import sys

from pydantic import AliasChoices, AliasPath, Field

from pydantic_settings import BaseSettings


class User(BaseSettings, cli_parse_args=True):
    first_name: str = Field(
        validation_alias=AliasChoices('f', 'fname', AliasPath('name', 0))
    )
    last_name: str = Field(
        validation_alias=AliasChoices('l', 'lname', AliasPath('name', 1))
    )


sys.argv = ['example.py', '--fname', 'John', '--lname', 'Doe']
print(User().model_dump())
#> {'first_name': 'John', 'last_name': 'Doe'}

sys.argv = ['example.py', '-f', 'John', '-l', 'Doe']
print(User().model_dump())
#> {'first_name': 'John', 'last_name': 'Doe'}

sys.argv = ['example.py', '--name', 'John,Doe']
print(User().model_dump())
#> {'first_name': 'John', 'last_name': 'Doe'}

sys.argv = ['example.py', '--name', 'John', '--lname', 'Doe']
print(User().model_dump())
#> {'first_name': 'John', 'last_name': 'Doe'}
```

### 子命令和位置参数

子命令和位置参数使用 `CliSubCommand` 和 `CliPositionalArg` 注解来表示。
子命令注解只能应用于必需字段（即没有默认值的字段）。
此外，子命令必须是派生自 pydantic `BaseModel` 或 pydantic.dataclasses `dataclass` 的有效类型。

解析后的子命令可以使用 `get_subcommand` 实用函数从模型实例中检索。如果子命令不是必需的，将 `is_required` 标志设置为 `False` 以在未找到子命令时禁用错误抛出。

!!! note
    CLI 设置子命令每个模型仅限于单个子解析器。换句话说，模型的所有子命令都分组在单个子解析器下；它不允许每个子解析器拥有自己的子命令集的多个子解析器。有关子解析器的更多信息，请参阅 [argparse 子命令](https://docs.python.org/3/library/argparse.html#sub-commands)。

!!! note
    `CliSubCommand` 和 `CliPositionalArg` 始终区分大小写。

```py
import sys

from pydantic import BaseModel

from pydantic_settings import (
    BaseSettings,
    CliPositionalArg,
    CliSubCommand,
    SettingsError,
    get_subcommand,
)


class Init(BaseModel):
    directory: CliPositionalArg[str]


class Clone(BaseModel):
    repository: CliPositionalArg[str]
    directory: CliPositionalArg[str]


class Git(BaseSettings, cli_parse_args=True, cli_exit_on_error=False):
    clone: CliSubCommand[Clone]
    init: CliSubCommand[Init]


# Run without subcommands
sys.argv = ['example.py']
cmd = Git()
assert cmd.model_dump() == {'clone': None, 'init': None}

try:
    # Will raise an error since no subcommand was provided
    get_subcommand(cmd).model_dump()
except SettingsError as err:
    assert str(err) == 'Error: CLI subcommand is required {clone, init}'

# Will not raise an error since subcommand is not required
assert get_subcommand(cmd, is_required=False) is None


# Run the clone subcommand
sys.argv = ['example.py', 'clone', 'repo', 'dest']
cmd = Git()
assert cmd.model_dump() == {
    'clone': {'repository': 'repo', 'directory': 'dest'},
    'init': None,
}

# Returns the subcommand model instance (in this case, 'clone')
assert get_subcommand(cmd).model_dump() == {
    'directory': 'dest',
    'repository': 'repo',
}
```

`CliSubCommand` 和 `CliPositionalArg` 注解也支持联合操作和别名。对于 Pydantic 模型的联合，重要的是要记住验证过程中可能出现的 [细微差别](https://docs.pydantic.dev/latest/concepts/unions/)。具体来说，对于内容相同的子命令联合，建议将它们分解为单独的 `CliSubCommand` 字段以避免任何复杂性。最后，从联合派生的子命令名称将是 Pydantic 模型类本身的名称。

当为 `CliSubCommand` 或 `CliPositionalArg` 字段分配别名时，只能分配单个别名。对于非联合子命令，别名将更改显示的帮助文本和子命令名称。相反，对于联合子命令，从 CLI 设置源的角度来看，别名不会有实际效果。最后，对于位置参数，别名将更改字段显示的 CLI 帮助文本。

```py
import sys
from typing import Union

from pydantic import BaseModel, Field

from pydantic_settings import (
    BaseSettings,
    CliPositionalArg,
    CliSubCommand,
    get_subcommand,
)


class Alpha(BaseModel):
    """Apha Help"""

    cmd_alpha: CliPositionalArg[str] = Field(alias='alpha-cmd')


class Beta(BaseModel):
    """Beta Help"""

    opt_beta: str = Field(alias='opt-beta')


class Gamma(BaseModel):
    """Gamma Help"""

    opt_gamma: str = Field(alias='opt-gamma')


class Root(BaseSettings, cli_parse_args=True, cli_exit_on_error=False):
    alpha_or_beta: CliSubCommand[Union[Alpha, Beta]] = Field(alias='alpha-or-beta-cmd')
    gamma: CliSubCommand[Gamma] = Field(alias='gamma-cmd')


sys.argv = ['example.py', 'Alpha', 'hello']
assert get_subcommand(Root()).model_dump() == {'cmd_alpha': 'hello'}

sys.argv = ['example.py', 'Beta', '--opt-beta=hey']
assert get_subcommand(Root()).model_dump() == {'opt_beta': 'hey'}

sys.argv = ['example.py', 'gamma-cmd', '--opt-gamma=hi']
assert get_subcommand(Root()).model_dump() == {'opt_gamma': 'hi'}
```

### 创建 CLI 应用程序

`CliApp` 类提供了两个实用方法，`CliApp.run` 和 `CliApp.run_subcommand`，可用于将 Pydantic `BaseSettings`、`BaseModel` 或 `pydantic.dataclasses.dataclass` 作为 CLI 应用程序运行。这些方法主要为运行与模型关联的 `cli_cmd` 方法提供结构。

`CliApp.run` 可用于直接提供要解析的 `cli_args`，并在实例化后运行模型的 `cli_cmd` 方法（如果已定义）：

```py
from pydantic_settings import BaseSettings, CliApp


class Settings(BaseSettings):
    this_foo: str

    def cli_cmd(self) -> None:
        # Print the parsed data
        print(self.model_dump())
        #> {'this_foo': 'is such a foo'}

        # Update the parsed data showing cli_cmd ran
        self.this_foo = 'ran the foo cli cmd'


s = CliApp.run(Settings, cli_args=['--this_foo', 'is such a foo'])
print(s.model_dump())
#> {'this_foo': 'ran the foo cli cmd'}
```

类似地，`CliApp.run_subcommand` 可以以递归方式用于运行子命令的 `cli_cmd` 方法：

```py
from pydantic import BaseModel

from pydantic_settings import CliApp, CliPositionalArg, CliSubCommand


class Init(BaseModel):
    directory: CliPositionalArg[str]

    def cli_cmd(self) -> None:
        print(f'git init "{self.directory}"')
        #> git init "dir"
        self.directory = 'ran the git init cli cmd'


class Clone(BaseModel):
    repository: CliPositionalArg[str]
    directory: CliPositionalArg[str]

    def cli_cmd(self) -> None:
        print(f'git clone from "{self.repository}" into "{self.directory}"')
        self.directory = 'ran the clone cli cmd'


class Git(BaseModel):
    clone: CliSubCommand[Clone]
    init: CliSubCommand[Init]

    def cli_cmd(self) -> None:
        CliApp.run_subcommand(self)


cmd = CliApp.run(Git, cli_args=['init', 'dir'])
assert cmd.model_dump() == {
    'clone': None,
    'init': {'directory': 'ran the git init cli cmd'},
}
```

!!! note
    与 `CliApp.run` 不同，`CliApp.run_subcommand` 要求子命令模型具有已定义的 `cli_cmd` 方法。

对于 `BaseModel` 和 `pydantic.dataclasses.dataclass` 类型，`CliApp.run` 将在内部使用以下
`BaseSettings` 配置默认值：

* `nested_model_default_partial_update=True`
* `case_sensitive=True`
* `cli_hide_none_type=True`
* `cli_avoid_json=True`
* `cli_enforce_required=True`
* `cli_implicit_flags=True`
* `cli_kebab_case=True`

### 异步 CLI 命令

Pydantic settings 支持通过 `CliApp.run` 和 `CliApp.run_subcommand` 运行异步 CLI 命令。通过此功能，你可以在 Pydantic 模型（包括子命令）中定义 async def 方法，并让它们像同步对应项一样执行。具体来说：

1. 支持异步方法：你现在可以将 cli_cmd 或类似的 CLI 入口点方法标记为 async def，并让 CliApp 执行它们。
2. 子命令也可以是异步的：如果你有嵌套的 CLI 子命令，最终（最低级别）的子命令方法同样可以是异步的。
3. 将异步方法限制在最终子命令：不建议将父命令定义为异步，因为这可能导致创建额外的线程和事件循环。为了获得最佳性能并避免不必要的资源使用，只实现最深层的（子）子命令为 async def。

下面是一个演示异步顶级命令的简单示例：

```py
from pydantic_settings import BaseSettings, CliApp


class AsyncSettings(BaseSettings):
    async def cli_cmd(self) -> None:
        print('Hello from an async CLI method!')
        #> Hello from an async CLI method!


# If an event loop is already running, a new thread will be used;
# otherwise, asyncio.run() is used to execute this async method.
assert CliApp.run(AsyncSettings, cli_args=[]).model_dump() == {}
```

#### 异步子命令

如上所述，你也可以将子命令定义为异步。但是，仅在叶子（最低级别）子命令中这样做，以避免在父命令中不必要地生成新线程和事件循环：

```py
from pydantic import BaseModel

from pydantic_settings import (
    BaseSettings,
    CliApp,
    CliPositionalArg,
    CliSubCommand,
)


class Clone(BaseModel):
    repository: CliPositionalArg[str]
    directory: CliPositionalArg[str]

    async def cli_cmd(self) -> None:
        # Perform async tasks here, e.g. network or I/O operations
        print(f'Cloning async from "{self.repository}" into "{self.directory}"')
        #> Cloning async from "repo" into "dir"


class Git(BaseSettings):
    clone: CliSubCommand[Clone]

    def cli_cmd(self) -> None:
        # Run the final subcommand (clone/init). It is recommended to define async methods only at the deepest level.
        CliApp.run_subcommand(self)


CliApp.run(Git, cli_args=['clone', 'repo', 'dir']).model_dump() == {
    'repository': 'repo',
    'directory': 'dir',
}
```

当执行具有异步 cli_cmd 的子命令时，Pydantic settings 会自动检测当前线程是否已有活动的事件循环。如果有，异步命令将在新线程中运行以避免冲突。否则，它将在当前线程中使用 asyncio.run()。这种处理确保你的异步子命令"正常工作"，无需额外的手动设置。

### 序列化 CLI 参数

可以使用 `CliApp.serialize` 方法将实例化的 Pydantic 模型序列化为其 CLI 参数。

```py
from pydantic import BaseModel

from pydantic_settings import CliApp


class Nested(BaseModel):
    that: int


class Settings(BaseModel):
    this: str
    nested: Nested


print(CliApp.serialize(Settings(this='hello', nested=Nested(that=123))))
#> ['--this', 'hello', '--nested.that', '123']
```

### 互斥组

可以通过继承 `CliMutuallyExclusiveGroup` 类来创建 CLI 互斥组。

!!! note
    `CliMutuallyExclusiveGroup` 不能在联合中使用，也不能包含嵌套模型。

```py
from typing import Optional

from pydantic import BaseModel

from pydantic_settings import CliApp, CliMutuallyExclusiveGroup, SettingsError


class Circle(CliMutuallyExclusiveGroup):
    radius: Optional[float] = None
    diameter: Optional[float] = None
    perimeter: Optional[float] = None


class Settings(BaseModel):
    circle: Circle


try:
    CliApp.run(
        Settings,
        cli_args=['--circle.radius=1', '--circle.diameter=2'],
        cli_exit_on_error=False,
    )
except SettingsError as e:
    print(e)
    """
    error parsing CLI: argument --circle.diameter: not allowed with argument --circle.radius
    """
```

### 自定义 CLI 体验

以下标志可用于根据你的需求自定义 CLI 体验。

#### 更改显示的程序名称

通过设置 `cli_prog_name` 来更改帮助文本使用中显示的默认程序名称。默认情况下，它将从 `sys.argv[0]` 派生当前正在执行的程序的名称，就像 argparse 一样。

```py
import sys

from pydantic_settings import BaseSettings


class Settings(BaseSettings, cli_parse_args=True, cli_prog_name='appdantic'):
    pass


try:
    sys.argv = ['example.py', '--help']
    Settings()
except SystemExit as e:
    print(e)
    #> 0
"""
usage: appdantic [-h]

options:
  -h, --help  显示此帮助信息并退出
"""
```

#### CLI 布尔标志

使用 `cli_implicit_flags` 设置来更改布尔字段默认应该是显式还是隐式。默认情况下，布尔字段是"显式"的，意味着必须在 CLI 上显式提供布尔值，例如 `--flag=True`。相反，"隐式"的布尔字段从标志本身派生值，例如 `--flag,--no-flag`，这消除了传递显式值的需要。

此外，提供的 `CliImplicitFlag` 和 `CliExplicitFlag` 注解可以在需要时用于更细粒度的控制。

```py
from pydantic_settings import BaseSettings, CliExplicitFlag, CliImplicitFlag


class ExplicitSettings(BaseSettings, cli_parse_args=True):
    """Boolean fields are explicit by default."""

    explicit_req: bool
    """
    --explicit_req bool   (required)
    """

    explicit_opt: bool = False
    """
    --explicit_opt bool   (default: False)
    """

    # Booleans are explicit by default, so must override implicit flags with annotation
    implicit_req: CliImplicitFlag[bool]
    """
    --implicit_req, --no-implicit_req (required)
    """

    implicit_opt: CliImplicitFlag[bool] = False
    """
    --implicit_opt, --no-implicit_opt (default: False)
    """


class ImplicitSettings(BaseSettings, cli_parse_args=True, cli_implicit_flags=True):
    """With cli_implicit_flags=True, boolean fields are implicit by default."""

    # Booleans are implicit by default, so must override explicit flags with annotation
    explicit_req: CliExplicitFlag[bool]
    """
    --explicit_req bool   (required)
    """

    explicit_opt: CliExplicitFlag[bool] = False
    """
    --explicit_opt bool   (default: False)
    """

    implicit_req: bool
    """
    --implicit_req, --no-implicit_req (required)
    """

    implicit_opt: bool = False
    """
    --implicit_opt, --no-implicit_opt (default: False)
    """
```

#### 忽略和检索未知参数

使用 `cli_ignore_unknown_args` 来更改是否忽略未知的 CLI 参数并仅解析已知的参数。默认情况下，CLI 不会忽略任何参数。然后可以使用 `CliUnknownArgs` 注解检索被忽略的参数。

```py
import sys

from pydantic_settings import BaseSettings, CliUnknownArgs


class Settings(BaseSettings, cli_parse_args=True, cli_ignore_unknown_args=True):
    good_arg: str
    ignored_args: CliUnknownArgs


sys.argv = ['example.py', '--bad-arg=bad', 'ANOTHER_BAD_ARG', '--good_arg=hello world']
print(Settings().model_dump())
#> {'good_arg': 'hello world', 'ignored_args': ['--bad-arg=bad', 'ANOTHER_BAD_ARG']}
```

#### CLI 参数的 Kebab Case

通过启用 `cli_kebab_case` 来更改 CLI 参数是否应使用 kebab case。默认情况下，`cli_kebab_case=True` 将忽略枚举字段，相当于 `cli_kebab_case='no_enums'`。要将 kebab case 应用于所有内容，包括枚举，请使用 `cli_kebab_case='all'`。

```py
import sys

from pydantic import Field

from pydantic_settings import BaseSettings


class Settings(BaseSettings, cli_parse_args=True, cli_kebab_case=True):
    my_option: str = Field(description='will show as kebab case on CLI')


try:
    sys.argv = ['example.py', '--help']
    Settings()
except SystemExit as e:
    print(e)
    #> 0
"""
usage: example.py [-h] [--my-option str]

options:
  -h, --help       显示此帮助信息并退出
  --my-option str  will show as kebab case on CLI (required)
"""
```

#### 更改 CLI 是否应在出错时退出

使用 `cli_exit_on_error` 来更改 CLI 内部解析器是在出错时退出还是引发 `SettingsError` 异常。默认情况下，CLI 内部解析器会在出错时退出。

```py
import sys

from pydantic_settings import BaseSettings, SettingsError


class Settings(BaseSettings, cli_parse_args=True, cli_exit_on_error=False): ...


try:
    sys.argv = ['example.py', '--bad-arg']
    Settings()
except SettingsError as e:
    print(e)
    #> error parsing CLI: unrecognized arguments: --bad-arg
```

#### 在 CLI 中强制执行必需参数

Pydantic settings 设计用于在实例化模型时从各种来源拉取值。这意味着必需的字段并不严格要求来自任何单个来源（例如 CLI）。相反，重要的是其中一个来源提供所需的值。

但是，如果你的用例[更符合 #2](#command-line-support)，即使用 Pydantic 模型定义 CLI，你可能希望必需字段在 CLI 中严格必需。我们可以通过使用 `cli_enforce_required` 来启用此行为。

!!! note
    必需的 `CliPositionalArg` 字段在 CLI 中始终是严格必需的（强制执行的）。

```py
import os
import sys

from pydantic import Field

from pydantic_settings import BaseSettings, SettingsError


class Settings(
    BaseSettings,
    cli_parse_args=True,
    cli_enforce_required=True,
    cli_exit_on_error=False,
):
    my_required_field: str = Field(description='a top level required field')


os.environ['MY_REQUIRED_FIELD'] = 'hello from environment'

try:
    sys.argv = ['example.py']
    Settings()
except SettingsError as e:
    print(e)
    #> error parsing CLI: the following arguments are required: --my_required_field
```

#### 更改 None 类型解析字符串

通过设置 `cli_parse_none_str` 来更改将被解析为 `None` 的 CLI 字符串值（例如 "null"、"void"、"None" 等）。默认情况下，如果设置了 `env_parse_none_str` 值，它将使用该值。否则，如果 `cli_avoid_json` 为 `False`，则默认为 "null"，如果 `cli_avoid_json` 为 `True`，则默认为 "None"。

```py
import sys
from typing import Optional

from pydantic import Field

from pydantic_settings import BaseSettings


class Settings(BaseSettings, cli_parse_args=True, cli_parse_none_str='void'):
    v1: Optional[int] = Field(description='the top level v0 option')


sys.argv = ['example.py', '--v1', 'void']
print(Settings().model_dump())
#> {'v1': None}
```

#### 隐藏 None 类型值

通过启用 `cli_hide_none_type` 从 CLI 帮助文本中隐藏 `None` 值。

```py
import sys
from typing import Optional

from pydantic import Field

from pydantic_settings import BaseSettings


class Settings(BaseSettings, cli_parse_args=True, cli_hide_none_type=True):
    v0: Optional[str] = Field(description='the top level v0 option')


try:
    sys.argv = ['example.py', '--help']
    Settings()
except SystemExit as e:
    print(e)
    #> 0
"""
usage: example.py [-h] [--v0 str]

options:
  -h, --help  show this help message and exit
  --v0 str    the top level v0 option (required)
"""
```

#### 避免添加 JSON CLI 选项

通过启用 `cli_avoid_json` 来避免在 CLI 中添加导致 JSON 字符串的复杂字段。

```py
import sys

from pydantic import BaseModel, Field

from pydantic_settings import BaseSettings


class SubModel(BaseModel):
    v1: int = Field(description='the sub model v1 option')


class Settings(BaseSettings, cli_parse_args=True, cli_avoid_json=True):
    sub_model: SubModel = Field(
        description='The help summary for SubModel related options'
    )


try:
    sys.argv = ['example.py', '--help']
    Settings()
except SystemExit as e:
    print(e)
    #> 0
"""
usage: example.py [-h] [--sub_model.v1 int]

options:
  -h, --help          show this help message and exit

sub_model options:
  The help summary for SubModel related options

  --sub_model.v1 int  the sub model v1 option (required)
"""
```

#### 使用类文档字符串作为组帮助文本

默认情况下，在填充嵌套模型的组帮助文本时，它将从字段描述中提取。或者，我们也可以配置 CLI 设置以从类文档字符串中提取。

!!! note
    如果字段是嵌套模型的联合，组帮助文本将始终从字段描述中提取；即使 `cli_use_class_docs_for_groups` 设置为 `True`。

```py
import sys

from pydantic import BaseModel, Field

from pydantic_settings import BaseSettings


class SubModel(BaseModel):
    """The help text from the class docstring."""

    v1: int = Field(description='the sub model v1 option')


class Settings(BaseSettings, cli_parse_args=True, cli_use_class_docs_for_groups=True):
    """My application help text."""

    sub_model: SubModel = Field(description='The help text from the field description')


try:
    sys.argv = ['example.py', '--help']
    Settings()
except SystemExit as e:
    print(e)
    #> 0
"""
usage: example.py [-h] [--sub_model JSON] [--sub_model.v1 int]

我的应用程序帮助文本。

options:
  -h, --help          显示此帮助信息并退出

sub_model options:
  The help text from the class docstring.

  --sub_model JSON    set sub_model from JSON string
  --sub_model.v1 int  the sub model v1 option (required)
"""
```

#### 更改 CLI 标志前缀字符

通过设置 `cli_flag_prefix_char` 来更改 CLI 可选参数中使用的 CLI 标志前缀字符。

```py
import sys

from pydantic import AliasChoices, Field

from pydantic_settings import BaseSettings


class Settings(BaseSettings, cli_parse_args=True, cli_flag_prefix_char='+'):
    my_arg: str = Field(validation_alias=AliasChoices('m', 'my-arg'))


sys.argv = ['example.py', '++my-arg', 'hi']
print(Settings().model_dump())
#> {'my_arg': 'hi'}

sys.argv = ['example.py', '+m', 'hi']
print(Settings().model_dump())
#> {'my_arg': 'hi'}
```

#### 从 CLI 帮助文本中抑制字段

要从 CLI 帮助文本中抑制字段，可以使用 `CliSuppress` 注解用于字段类型，或者使用 `CLI_SUPPRESS` 字符串常量用于字段描述。

```py
import sys

from pydantic import Field

from pydantic_settings import CLI_SUPPRESS, BaseSettings, CliSuppress


class Settings(BaseSettings, cli_parse_args=True):
    """从 CLI 帮助文本中抑制字段。"""

    field_a: CliSuppress[int] = 0
    field_b: str = Field(default=1, description=CLI_SUPPRESS)


try:
    sys.argv = ['example.py', '--help']
    Settings()
except SystemExit as e:
    print(e)
    #> 0
"""
usage: example.py [-h]

从 CLI 帮助文本中抑制字段。

options:
  -h, --help          显示此帮助信息并退出
"""
```

#### CLI 参数快捷方式

使用 `SettingsConfigDict` 中的 `cli_shortcuts` 选项为字段添加替代的 CLI 参数名称（快捷方式）。这允许你为 CLI 参数定义额外的名称，这对于为深度嵌套或冗长的字段名称提供更用户友好或更短的别名特别有用。

`cli_shortcuts` 选项接受一个字典，将目标字段名称（对嵌套字段使用点表示法）映射到一个或多个快捷方式名称。如果多个字段共享相同的快捷方式，第一个匹配的字段将优先。

**Flat Example:**

```py
from pydantic import Field

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    option: str = Field(default='foo')
    list_option: str = Field(default='fizz')

    model_config = SettingsConfigDict(
        cli_shortcuts={'option': 'option2', 'list_option': ['list_option2']}
    )


# Now you can use the shortcuts on the CLI:
# --option2 sets 'option', --list_option2 sets 'list_option'
```

**Nested Example:**

```py
from pydantic import BaseModel, Field

from pydantic_settings import BaseSettings, SettingsConfigDict


class TwiceNested(BaseModel):
    option: str = Field(default='foo')


class Nested(BaseModel):
    twice_nested_option: TwiceNested = TwiceNested()
    option: str = Field(default='foo')


class Settings(BaseSettings):
    nested: Nested = Nested()
    model_config = SettingsConfigDict(
        cli_shortcuts={
            'nested.option': 'option2',
            'nested.twice_nested_option.option': 'twice_nested_option',
        }
    )


# Now you can use --option2 to set nested.option and --twice_nested_option to set nested.twice_nested_option.option
```

如果快捷方式发生冲突（映射到多个字段），它将应用于模型中第一个匹配的字段。

### 与现有解析器集成

可以通过用用户定义的指定 `root_parser` 对象的 CLI 设置源覆盖默认的 CLI 设置源来与现有解析器集成。

```py
import sys
from argparse import ArgumentParser

from pydantic_settings import BaseSettings, CliApp, CliSettingsSource

parser = ArgumentParser()
parser.add_argument('--food', choices=['pear', 'kiwi', 'lime'])


class Settings(BaseSettings):
    name: str = 'Bob'


# Set existing `parser` as the `root_parser` object for the user defined settings source
cli_settings = CliSettingsSource(Settings, root_parser=parser)

# Parse and load CLI settings from the command line into the settings source.
sys.argv = ['example.py', '--food', 'kiwi', '--name', 'waldo']
s = CliApp.run(Settings, cli_settings_source=cli_settings)
print(s.model_dump())
#> {'name': 'waldo'}

# Load CLI settings from pre-parsed arguments. i.e., the parsing occurs elsewhere and we
# just need to load the pre-parsed args into the settings source.
parsed_args = parser.parse_args(['--food', 'kiwi', '--name', 'ralph'])
s = CliApp.run(Settings, cli_args=parsed_args, cli_settings_source=cli_settings)
print(s.model_dump())
#> {'name': 'ralph'}
```

`CliSettingsSource` 通过使用解析器方法将 `settings_cls` 字段添加为命令行参数来与 `root_parser` 对象连接。`CliSettingsSource` 内部解析器表示基于 `argparse` 库，因此需要支持与其 `argparse` 对应项相同属性的解析器方法。可以自定义的可用解析器方法及其 argparse 对应项（默认值）如下：

* `parse_args_method` - (`argparse.ArgumentParser.parse_args`)
* `add_argument_method` - (`argparse.ArgumentParser.add_argument`)
* `add_argument_group_method` - (`argparse.ArgumentParser.add_argument_group`)
* `add_parser_method` - (`argparse._SubParsersAction.add_parser`)
* `add_subparsers_method` - (`argparse.ArgumentParser.add_subparsers`)
* `formatter_class` - (`argparse.RawDescriptionHelpFormatter`)

对于非 argparse 解析器，如果不支持，解析器方法可以设置为 `None`。只有当解析器方法必要但设置为 `None` 时，CLI 设置才会在连接到根解析器时引发错误。

!!! note
    `formatter_class` 仅应用于子命令。`CliSettingsSource` 从不接触或修改任何外部解析器设置以避免破坏性更改。由于子命令驻留在它们自己的内部解析器树上，我们可以安全地应用 `formatter_class` 设置而不会破坏外部解析器逻辑。

## Secrets

将密钥值放在文件中是为应用程序提供敏感配置的常见模式。

密钥文件遵循与 dotenv 文件相同的原则，只是它只包含单个值，并且文件名用作键。密钥文件将如下所示：

``` title="/var/run/database_password"
super_secret_database_password
```

一旦您有了密钥文件，*pydantic* 支持通过两种方式加载它：

1. 在 `BaseSettings` 类的 `model_config` 上设置 `secrets_dir` 到存储密钥文件的目录。
   ````py hl_lines="4 5 6 7"
   from pydantic_settings import BaseSettings, SettingsConfigDict


   class Settings(BaseSettings):
       model_config = SettingsConfigDict(secrets_dir='/var/run')

       database_password: str
   ````
2. 使用 `_secrets_dir` 关键字参数实例化 `BaseSettings` 派生类：
   ````
   settings = Settings(_secrets_dir='/var/run')
   ````

无论哪种情况，传递的参数值可以是任何有效目录，绝对路径或相对于当前工作目录。**请注意，不存在的目录只会生成警告**。
从那里，*pydantic* 将通过加载变量并验证它们来处理所有事情。

即使使用密钥目录，*pydantic* 仍将从 dotenv 文件或环境中读取环境变量，**dotenv 文件和环境变量始终优先于从密钥目录加载的值**。

在实例化时通过 `_secrets_dir` 关键字参数传递文件路径（方法 2）将覆盖在 `model_config` 类上设置的任何值。

如果需要从多个密钥目录加载设置，可以将多个路径作为元组或列表传递。就像 `env_file` 一样，后续路径的值会覆盖先前的值。

````python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # '/run/secrets' 中的文件优先于 '/var/run'
    model_config = SettingsConfigDict(secrets_dir=('/var/run', '/run/secrets'))

    database_password: str
````

如果任何 `secrets_dir` 缺失，它将被忽略，并显示警告。如果任何 `secrets_dir` 是文件，将引发错误。


### 用例：Docker Secrets

Docker Secrets 可用于为在 Docker 容器中运行的应用程序提供敏感配置。
要在 *pydantic* 应用程序中使用这些密钥，过程很简单。有关在 Docker 中创建、管理和使用密钥的更多信息，请参阅官方
[Docker 文档](https://docs.docker.com/engine/reference/commandline/secret/)。

首先，使用指定密钥目录的 `SettingsConfigDict` 定义您的 `Settings` 类。

```py hl_lines="4 5 6 7"
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(secrets_dir='/run/secrets')

    my_secret_data: str
```

!!! note
    默认情况下 [Docker 使用 `/run/secrets`](https://docs.docker.com/engine/swarm/secrets/#how-docker-manages-secrets)
    作为目标挂载点。如果您想使用不同的位置，请相应地更改 `Config.secrets_dir`。

然后，通过 Docker CLI 创建您的密钥
```bash
printf "This is a secret" | docker secret create my_secret_data -
```

最后，在 Docker 容器内运行您的应用程序并提供新创建的密钥
```bash
docker service create --name pydantic-with-secrets --secret my_secret_data pydantic-app:latest
```

## 嵌套密钥

默认的密钥实现 `SecretsSettingsSource` 的行为并不总是理想或足够的。
例如，默认实现不支持嵌套子模型中的密钥字段。

`NestedSecretsSettingsSource` 可以用作 `SecretsSettingsSource` 的直接替代品来调整默认行为。
所有差异总结在下表中。

| `SecretsSettingsSource`                                                                                                                                         | `NestedSecretsSettingsSourcee`                                                                                                    |
|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------|
| 密钥字段必须属于顶级模型。                                                                                                                 | 密钥可以是嵌套模型的字段。                                                                                           |
| 密钥文件只能放在 `secrets_dir` 中。                                                                                                              | 密钥文件可以放在嵌套模型的子目录中。                                                                   |
| 密钥文件发现基于与 `EnvSettingsSource` 相同的配置选项：`case_sensitive`、`env_nested_delimiter`、`env_prefix`。 | 默认选项被尊重，但可以用 `secrets_case_sensitive`、`secrets_nested_delimiter`、`secrets_prefix` 覆盖。 |
| 当 `secrets_dir` 在文件系统中缺失时，会生成警告。                                                                                       | 使用 `secrets_dir_missing` 选项选择是发出警告、引发错误还是静默忽略。                            |

### 用例：普通目录布局

```text
📂 secrets
├── 📄 app_key
└── 📄 db_passwd
```

在下面的示例中，密钥嵌套分隔符 `'_'` 与环境嵌套分隔符 `'__'` 不同。
`Settings.db.user` 的值可以通过环境变量 `MY_DB__USER` 传递。

```py
from pydantic import BaseModel, SecretStr

from pydantic_settings import (
    BaseSettings,
    NestedSecretsSettingsSource,
    SettingsConfigDict,
)


class AppSettings(BaseModel):
    key: SecretStr


class DbSettings(BaseModel):
    user: str
    passwd: SecretStr


class Settings(BaseSettings):
    app: AppSettings
    db: DbSettings

    model_config = SettingsConfigDict(
        env_prefix='MY_',
        env_nested_delimiter='__',
        secrets_dir='secrets',
        secrets_nested_delimiter='_',
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            NestedSecretsSettingsSource(file_secret_settings),
        )
```

### 用例：嵌套目录布局

```text
📂 secrets
├── 📂 app
│   └── 📄 key
└── 📂 db
    └── 📄 passwd
```
```py
from pydantic import BaseModel, SecretStr

from pydantic_settings import (
    BaseSettings,
    NestedSecretsSettingsSource,
    SettingsConfigDict,
)


class AppSettings(BaseModel):
    key: SecretStr


class DbSettings(BaseModel):
    user: str
    passwd: SecretStr


class Settings(BaseSettings):
    app: AppSettings
    db: DbSettings

    model_config = SettingsConfigDict(
        env_prefix='MY_',
        env_nested_delimiter='__',
        secrets_dir='secrets',
        secrets_nested_subdir=True,
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            NestedSecretsSettingsSource(file_secret_settings),
        )
```

### 用例：多个嵌套目录

```text
📂 secrets
├── 📂 default
│   ├── 📂 app
│   │   └── 📄 key
│   └── 📂 db
│       └── 📄 passwd
└── 📂 override
    ├── 📂 app
    │   └── 📄 key
    └── 📂 db
        └── 📄 passwd
```
```py
from pydantic import BaseModel, SecretStr

from pydantic_settings import (
    BaseSettings,
    NestedSecretsSettingsSource,
    SettingsConfigDict,
)


class AppSettings(BaseModel):
    key: SecretStr


class DbSettings(BaseModel):
    user: str
    passwd: SecretStr


class Settings(BaseSettings):
    app: AppSettings
    db: DbSettings

    model_config = SettingsConfigDict(
        env_prefix='MY_',
        env_nested_delimiter='__',
        secrets_dir=['secrets/default', 'secrets/override'],
        secrets_nested_subdir=True,
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            NestedSecretsSettingsSource(file_secret_settings),
        )
```

### 配置选项

#### secrets_dir

密钥目录的路径，与 `SecretsSettingsSource.secrets_dir` 相同。如果是 `list`，最后一个匹配项获胜。
如果同时在源构造函数和模型配置中传递 `secrets_dir`，值不会合并（构造函数获胜）。

#### secrets_dir_missing

如果 `secrets_dir` 不存在，原始的 `SecretsSettingsSource` 会发出警告。
然而，这可能是不希望的，例如，如果我们在开发环境中没有挂载 Docker Secrets。
使用 `secrets_dir_missing` 来选择：

* `'ok'` — 如果 `secrets_dir` 不存在，什么也不做
* `'warn'`（默认）— 打印警告，与 `SecretsSettingsSource` 相同
* `'error'` — 引发 `SettingsError`

如果传递了多个 `secrets_dir`，相同的 `secrets_dir_missing` 操作适用于每个目录。

#### secrets_dir_max_size

出于安全原因限制 `secrets_dir` 的大小，默认为 `SECRETS_DIR_MAX_SIZE` 等于 16 MiB。

`NestedSecretsSettingsSource` 是围绕 `EnvSettingsSource` 的薄包装器，
它在初始化时加载所有潜在的密钥。如果我们在 `secrets_dir` 下挂载一个大文件，这可能导致 `MemoryError`。

如果传递了多个 `secrets_dir`，限制独立应用于每个目录。

#### secrets_case_sensitive

与 `case_sensitive` 相同，但仅适用于密钥。如果未指定，默认为 `case_sensitive`。

#### secrets_nested_delimiter

与 `env_nested_delimiter` 相同，但仅适用于密钥。如果未指定，默认为 `env_nested_delimiter`。
此选项用于实现_嵌套密钥目录_布局，并允许执行甚至像 `/run/secrets/model/delim/nested1/delim/nested2` 这样的复杂操作。

#### secrets_nested_subdir

布尔标志，用于打开_嵌套密钥目录_模式，默认为 `False`。如果为 `True`，将 `secrets_nested_delimiter`
设置为 `os.sep`。如果已经指定了 `secrets_nested_delimiter`，则引发 `SettingsError`。

#### secrets_prefix

密钥路径前缀，类似于 `env_prefix`，但仅适用于密钥。如果未指定，默认为 `env_prefix`。
在普通和嵌套目录模式下都有效，如 `'/run/secrets/prefix_model__nested'` 和 `'/run/secrets/prefix_model/nested'`。


## AWS Secrets Manager

您必须设置一个参数：

- `secret_id`：AWS 密钥 ID

您必须在密钥中的键值与字段名称中使用相同的命名约定。例如，如果密钥中的键名为 `SqlServerPassword`，字段名称必须相同。您也可以使用别名。

在 AWS Secrets Manager 中，嵌套模型支持在键名中使用 `--` 分隔符。例如，`SqlServer--Password`。

不支持数组（例如 `MySecret--0`、`MySecret--1`）。

```py
import os

from pydantic import BaseModel

from pydantic_settings import (
    AWSSecretsManagerSettingsSource,
    BaseSettings,
    PydanticBaseSettingsSource,
)


class SubModel(BaseModel):
    a: str


class AWSSecretsManagerSettings(BaseSettings):
    foo: str
    bar: int
    sub: SubModel

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        aws_secrets_manager_settings = AWSSecretsManagerSettingsSource(
            settings_cls,
            os.environ['AWS_SECRETS_MANAGER_SECRET_ID'],
        )
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
            aws_secrets_manager_settings,
        )
```

## Azure Key Vault

您必须设置两个参数：

- `url`：例如，`https://my-resource.vault.azure.net/`。
- `credential`：如果您使用 `DefaultAzureCredential`，在本地可以执行 `az login` 来获取您的身份凭据。身份必须具有角色分配（推荐的是 `Key Vault Secrets User`），以便您可以访问密钥。

您必须在字段名称与 Key Vault 密钥名称中使用相同的命名约定。例如，如果密钥名为 `SqlServerPassword`，字段名称必须相同。您也可以使用别名。

在 Key Vault 中，嵌套模型支持使用 `--` 分隔符。例如，`SqlServer--Password`。

不支持 Key Vault 数组（例如 `MySecret--0`、`MySecret--1`）。

```py
import os

from azure.identity import DefaultAzureCredential
from pydantic import BaseModel

from pydantic_settings import (
    AzureKeyVaultSettingsSource,
    BaseSettings,
    PydanticBaseSettingsSource,
)


class SubModel(BaseModel):
    a: str


class AzureKeyVaultSettings(BaseSettings):
    foo: str
    bar: int
    sub: SubModel

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        az_key_vault_settings = AzureKeyVaultSettingsSource(
            settings_cls,
            os.environ['AZURE_KEY_VAULT_URL'],
            DefaultAzureCredential(),
        )
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
            az_key_vault_settings,
        )
```

### Snake case 转换

Azure Key Vault 源接受一个 `snake_case_convertion` 选项，默认禁用，用于通过将 Key Vault 密钥名称映射到 Python 的 snake_case 字段名称来转换它们，无需使用别名。

```py
import os

from azure.identity import DefaultAzureCredential

from pydantic_settings import (
    AzureKeyVaultSettingsSource,
    BaseSettings,
    PydanticBaseSettingsSource,
)


class AzureKeyVaultSettings(BaseSettings):
    my_setting: str

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        az_key_vault_settings = AzureKeyVaultSettingsSource(
            settings_cls,
            os.environ['AZURE_KEY_VAULT_URL'],
            DefaultAzureCredential(),
            snake_case_conversion=True,
        )
        return (az_key_vault_settings,)
```

此设置将加载 Azure Key Vault 密钥（例如，`MySetting`、`mySetting`、`my-secret` 或 `MY-SECRET`），将它们映射到 snake case 版本（本例中为 `my_setting`）。

### 破折号到下划线映射

Azure Key Vault 源接受一个 `dash_to_underscore` 选项，默认禁用，用于通过将 Key Vault kebab-case 密钥名称映射到 Python 的 snake_case 字段名称来支持它们。启用后，在验证期间，密钥名称中的破折号（`-`）将映射到字段名称中的下划线（`_`）。

此映射仅适用于*字段名称*，不适用于别名。

```py
import os

from azure.identity import DefaultAzureCredential
from pydantic import Field

from pydantic_settings import (
    AzureKeyVaultSettingsSource,
    BaseSettings,
    PydanticBaseSettingsSource,
)


class AzureKeyVaultSettings(BaseSettings):
    field_with_underscore: str
    field_with_alias: str = Field(..., alias='Alias-With-Dashes')

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        az_key_vault_settings = AzureKeyVaultSettingsSource(
            settings_cls,
            os.environ['AZURE_KEY_VAULT_URL'],
            DefaultAzureCredential(),
            dash_to_underscore=True,
        )
        return (az_key_vault_settings,)
```

此设置将加载名为 `field-with-underscore` 和 `Alias-With-Dashes` 的 Azure Key Vault 密钥，分别将它们映射到 `field_with_underscore` 和 `field_with_alias` 字段。

!!! tip
    或者，您可以配置 [alias_generator](alias.md#using-alias-generators) 来映射 PascalCase 密钥。

## Google Cloud Secret Manager

Google Cloud Secret Manager 允许您在 Google Cloud Platform 中存储、管理和访问敏感信息作为密钥。此集成使您可以直接从 GCP Secret Manager 检索密钥以用于您的 Pydantic 设置。

### 安装

Google Cloud Secret Manager 集成需要额外的依赖项：

```bash
pip install "pydantic-settings[gcp-secret-manager]"
```

### 基本用法

要使用 Google Cloud Secret Manager，您需要：

1. 创建一个 `GoogleSecretManagerSettingsSource`。（有关身份验证选项，请参阅 [GCP Authentication](#gcp-authentication)。）
2. 将此源添加到您的设置自定义管道中

   ```py
   from pydantic import BaseModel

   from pydantic_settings import (
       BaseSettings,
       GoogleSecretManagerSettingsSource,
       PydanticBaseSettingsSource,
       SettingsConfigDict,
   )


   class Database(BaseModel):
       password: str
       user: str


   class Settings(BaseSettings):
       database: Database

       model_config = SettingsConfigDict(env_nested_delimiter='__')

       @classmethod
       def settings_customise_sources(
           cls,
           settings_cls: type[BaseSettings],
           init_settings: PydanticBaseSettingsSource,
           env_settings: PydanticBaseSettingsSource,
           dotenv_settings: PydanticBaseSettingsSource,
           file_secret_settings: PydanticBaseSettingsSource,
       ) -> tuple[PydanticBaseSettingsSource, ...]:
           # Create the GCP Secret Manager settings source
           gcp_settings = GoogleSecretManagerSettingsSource(
               settings_cls,
               # If not provided, will use google.auth.default()
               # to get credentials from the environemnt
               # credentials=your_credentials,
               # If not provided, will use google.auth.default()
               # to get project_id from the environemnt
               project_id='your-gcp-project-id',
           )

           return (
               init_settings,
               env_settings,
               dotenv_settings,
               file_secret_settings,
               gcp_settings,
           )
   ```

### GCP Authentication

`GoogleSecretManagerSettingsSource` 支持多种身份验证方法：

1. **默认凭据** - 如果您不提供凭据或项目 ID，它将使用 [`google.auth.default()`](https://google-auth.readthedocs.io/en/master/reference/google.auth.html#google.auth.default) 来获取它们。这适用于：

   - 来自 `GOOGLE_APPLICATION_CREDENTIALS` 环境变量的服务账户凭据
   - 来自 `gcloud auth application-default login` 的用户凭据
   - Compute Engine、GKE、Cloud Run 或 Cloud Functions 的默认服务账户

2. **显式凭据** - 您也可以直接提供 `credentials`。例如 `sa_credentials = google.oauth2.service_account.Credentials.from_service_account_file('path/to/service-account.json')`，然后使用 `GoogleSecretManagerSettingsSource(credentials=sa_credentials)`

### 嵌套模型

对于嵌套模型，只要符合[命名规则](https://cloud.google.com/secret-manager/docs/creating-and-accessing-secrets#create-a-secret)，Secret Manager 支持 `env_nested_delimiter` 设置。在上面的示例中，您需要在 Secret Manager 中创建名为 `database__password` 和 `database__user` 的密钥。

### 重要注意事项

1. **大小写敏感性**：默认情况下，密钥名称是区分大小写的。
2. **密钥命名**：在 Google Secret Manager 中创建密钥时，名称应与您的字段名称匹配（包括任何前缀）。根据 [Secret Manager 文档](https://cloud.google.com/secret-manager/docs/creating-and-accessing-secrets#create-a-secret)，密钥名称可以包含大写和小写字母、数字、连字符和下划线。名称的最大允许长度为 255 个字符。
3. **密钥版本**：`GoogleSecretManagerSettingsSource` 使用密钥的"最新"版本。

有关在 Google Cloud Secret Manager 中创建和管理密钥的更多详细信息，请参阅[官方 Google Cloud 文档](https://cloud.google.com/secret-manager/docs)。

## 其他设置源

其他设置源可用于常见的配置文件：

- `JsonConfigSettingsSource` 使用 `json_file` 和 `json_file_encoding` 参数
- `PyprojectTomlConfigSettingsSource` 使用 *(可选)* `pyproject_toml_depth` 和 *(可选)* `pyproject_toml_table_header` 参数
- `TomlConfigSettingsSource` 使用 `toml_file` 参数
- `YamlConfigSettingsSource` 使用 `yaml_file` 和 yaml_file_encoding 参数

您还可以通过提供路径列表来提供多个文件：
```py
toml_file = ['config.default.toml', 'config.custom.toml']
```
要使用它们，您可以使用[此处](#customise-settings-sources)描述的相同机制


```py
from pydantic import BaseModel

from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)


class Nested(BaseModel):
    nested_field: str


class Settings(BaseSettings):
    foobar: str
    nested: Nested
    model_config = SettingsConfigDict(toml_file='config.toml')

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (TomlConfigSettingsSource(settings_cls),)
```

这将能够读取位于工作目录中的以下 "config.toml" 文件：

```toml
foobar = "Hello"
[nested]
nested_field = "world!"
```

### pyproject.toml

"pyproject.toml" 是一个标准化的文件，用于在 Python 项目中提供配置值。
[PEP 518](https://peps.python.org/pep-0518/#tool-table) 定义了一个 `[tool]` 表，可用于提供任意工具配置。
虽然鼓励使用 `[tool]` 表，但 `PyprojectTomlConfigSettingsSource` 可用于从 "pyproject.toml" 文件中的任何位置加载变量。

这通过提供 `SettingsConfigDict(pyproject_toml_table_header=tuple[str, ...])` 来控制，其中值是一个头部部分的元组。
默认情况下，`pyproject_toml_table_header=('tool', 'pydantic-settings')`，这将从 `[tool.pydantic-settings]` 表加载变量。

```python
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    PyprojectTomlConfigSettingsSource,
    SettingsConfigDict,
)


class Settings(BaseSettings):
    """Example loading values from the table used by default."""

    field: str

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (PyprojectTomlConfigSettingsSource(settings_cls),)


class SomeTableSettings(Settings):
    """Example loading values from a user defined table."""

    model_config = SettingsConfigDict(
        pyproject_toml_table_header=('tool', 'some-table')
    )


class RootSettings(Settings):
    """Example loading values from the root of a pyproject.toml file."""

    model_config = SettingsConfigDict(extra='ignore', pyproject_toml_table_header=())
```

这将能够读取位于工作目录中的以下 "pyproject.toml" 文件，结果为 `Settings(field='default-table')`、`SomeTableSettings(field='some-table')` 和 `RootSettings(field='root')`：

```toml
field = "root"

[tool.pydantic-settings]
field = "default-table"

[tool.some-table]
field = "some-table"
```

默认情况下，`PyprojectTomlConfigSettingsSource` 只会在当前工作目录中查找 "pyproject.toml"。
但是，有两个选项可以改变这种行为。

* 可以提供 `SettingsConfigDict(pyproject_toml_depth=<int>)` 来检查目录树中 **向上** `<int>` 个目录以查找 "pyproject.toml"，如果在当前工作目录中未找到。
  默认情况下，不检查父目录。
* 可以在实例化源时提供显式文件路径（例如 `PyprojectTomlConfigSettingsSource(settings_cls, Path('~/.config').resolve() / 'pyproject.toml')`）。
  如果以这种方式提供文件路径，它将被视为绝对路径（不检查其他位置）。

```python
from pathlib import Path

from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    PyprojectTomlConfigSettingsSource,
    SettingsConfigDict,
)


class DiscoverSettings(BaseSettings):
    """Example of discovering a pyproject.toml in parent directories in not in `Path.cwd()`."""

    model_config = SettingsConfigDict(pyproject_toml_depth=2)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (PyprojectTomlConfigSettingsSource(settings_cls),)


class ExplicitFilePathSettings(BaseSettings):
    """Example of explicitly providing the path to the file to load."""

    field: str

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            PyprojectTomlConfigSettingsSource(
                settings_cls, Path('~/.config').resolve() / 'pyproject.toml'
            ),
        )
```

## 字段值优先级

当以多种方式为同一个 `Settings` 字段指定值时，所选值按以下优先级确定（按优先级降序排列）：

1. 如果启用了 `cli_parse_args`，则在 CLI 传递的参数。
2. 传递给 `Settings` 类初始化器的参数。
3. 环境变量，例如上面描述的 `my_prefix_special_function`。
4. 从 dotenv (`.env`) 文件加载的变量。
5. 从 secrets 目录加载的变量。
6. `Settings` 模型的默认字段值。

## 自定义设置源

如果默认的优先级顺序不符合你的需求，可以通过重写 `Settings` 的 `settings_customise_sources` 方法来更改它。

`settings_customise_sources` 接受四个可调用对象作为参数，并返回任意数量的可调用对象作为元组。
这些可调用对象依次被调用来构建设置类字段的输入。

每个可调用对象应将设置类的实例作为其唯一参数并返回一个 `dict`。

### 更改优先级

返回的可调用对象的顺序决定了输入的优先级；第一项具有最高优先级。

```py
from pydantic import PostgresDsn

from pydantic_settings import BaseSettings, PydanticBaseSettingsSource


class Settings(BaseSettings):
    database_dsn: PostgresDsn

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return env_settings, init_settings, file_secret_settings


print(Settings(database_dsn='postgres://postgres@localhost:5432/kwargs_db'))
#> database_dsn=PostgresDsn('postgres://postgres@localhost:5432/kwargs_db')
```

通过交换 `env_settings` 和 `init_settings`，环境变量现在优先于 `__init__` 关键字参数。

### 添加源

如前所述，*pydantic* 附带多个内置设置源。但是，你可能偶尔需要添加自己的自定义源，`settings_customise_sources` 使这变得非常容易：

```py
import json
from pathlib import Path
from typing import Any

from pydantic.fields import FieldInfo

from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)


class JsonConfigSettingsSource(PydanticBaseSettingsSource):
    """
    A simple settings source class that loads variables from a JSON file
    at the project's root.

    Here we happen to choose to use the `env_file_encoding` from Config
    when reading `config.json`
    """

    def get_field_value(
        self, field: FieldInfo, field_name: str
    ) -> tuple[Any, str, bool]:
        encoding = self.config.get('env_file_encoding')
        file_content_json = json.loads(
            Path('tests/example_test_config.json').read_text(encoding)
        )
        field_value = file_content_json.get(field_name)
        return field_value, field_name, False

    def prepare_field_value(
        self, field_name: str, field: FieldInfo, value: Any, value_is_complex: bool
    ) -> Any:
        return value

    def __call__(self) -> dict[str, Any]:
        d: dict[str, Any] = {}

        for field_name, field in self.settings_cls.model_fields.items():
            field_value, field_key, value_is_complex = self.get_field_value(
                field, field_name
            )
            field_value = self.prepare_field_value(
                field_name, field, field_value, value_is_complex
            )
            if field_value is not None:
                d[field_key] = field_value

        return d


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file_encoding='utf-8')

    foobar: str

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            JsonConfigSettingsSource(settings_cls),
            env_settings,
            file_secret_settings,
        )


print(Settings())
#> foobar='test'
```

#### 访问先前源的结果

每个设置源都可以访问先前源的结果。

```python
from typing import Any

from pydantic.fields import FieldInfo

from pydantic_settings import PydanticBaseSettingsSource


class MyCustomSource(PydanticBaseSettingsSource):
    def get_field_value(
        self, field: FieldInfo, field_name: str
    ) -> tuple[Any, str, bool]: ...

    def __call__(self) -> dict[str, Any]:
        # Retrieve the aggregated settings from previous sources
        current_state = self.current_state
        current_state.get('some_setting')

        # Retrive settings from all sources individually
        # self.settings_sources_data["SettingsSourceName"]: dict[str, Any]
        settings_sources_data = self.settings_sources_data
        settings_sources_data['SomeSettingsSource'].get('some_setting')

        # Your code here...
```

### 移除源

你可能也想禁用某个源：

```py
from pydantic import ValidationError

from pydantic_settings import BaseSettings, PydanticBaseSettingsSource


class Settings(BaseSettings):
    my_api_key: str

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        # here we choose to ignore arguments from init_settings
        return env_settings, file_secret_settings


try:
    Settings(my_api_key='this is ignored')
except ValidationError as exc_info:
    print(exc_info)
    """
    1 validation error for Settings
    my_api_key
      Field required [type=missing, input_value={}, input_type=dict]
        For further information visit https://errors.pydantic.dev/2/v/missing
    """
```


## 就地重载

如果你想就地重载现有设置，可以使用其 `__init__` 方法：

```py
import os

from pydantic import Field

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    foo: str = Field('foo')


mutable_settings = Settings()

print(mutable_settings.foo)
#> foo

os.environ['foo'] = 'bar'
print(mutable_settings.foo)
#> foo

mutable_settings.__init__()
print(mutable_settings.foo)
#> bar

os.environ.pop('foo')
mutable_settings.__init__()
print(mutable_settings.foo)
#> foo
```