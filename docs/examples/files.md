---
subtitle: 验证文件数据
description: 使用 Pydantic 验证 JSON、CSV、TOML、YAML、XML 和 INI 文件数据的完整指南，包含实用代码示例和错误处理方法。
---

`pydantic` 是一个用于验证来自各种来源数据的强大工具。
在本节中，我们将了解如何验证来自不同类型文件的数据。

!!! note
    如果您使用以下任何文件格式来解析配置/设置，您可能想要
    考虑使用 [`pydantic-settings`][pydantic_settings] 库，它提供了内置的
    支持来解析此类数据。

## JSON 数据

`.json` 文件是一种以人类可读格式存储键/值数据的常见方式。
以下是一个 `.json` 文件的示例：

```json
{
    "name": "John Doe",
    "age": 30,
    "email": "john@example.com"
}
```

要验证这些数据，我们可以使用一个 `pydantic` 模型：

```python {test="skip"}
import pathlib

from pydantic import BaseModel, EmailStr, PositiveInt


class Person(BaseModel):
    name: str
    age: PositiveInt
    email: EmailStr


json_string = pathlib.Path('person.json').read_text()
person = Person.model_validate_json(json_string)
print(person)
#> name='John Doe' age=30 email='john@example.com'
```

如果文件中的数据无效，`pydantic` 将引发一个 [`ValidationError`][pydantic_core.ValidationError]。
假设我们有以下 `.json` 文件：

```json
{
    "age": -30,
    "email": "not-an-email-address"
}
```

这些数据存在三个问题：

1. 缺少 `name` 字段。
2. `age` 字段为负数。
3. `email` 字段不是有效的电子邮件地址。

当我们尝试验证这些数据时，`pydantic` 会引发一个 [`ValidationError`][pydantic_core.ValidationError]，其中包含所有
上述问题：

```python {test="skip"}
import pathlib

from pydantic import BaseModel, EmailStr, PositiveInt, ValidationError


class Person(BaseModel):
    name: str
    age: PositiveInt
    email: EmailStr


json_string = pathlib.Path('person.json').read_text()
try:
    person = Person.model_validate_json(json_string)
except ValidationError as err:
    print(err)
    """
    3 validation errors for Person
    name
    Field required [type=missing, input_value={'age': -30, 'email': 'not-an-email-address'}, input_type=dict]
        For further information visit https://errors.pydantic.dev/2.10/v/missing
    age
    Input should be greater than 0 [type=greater_than, input_value=-30, input_type=int]
        For further information visit https://errors.pydantic.dev/2.10/v/greater_than
    email
    value is not a valid email address: An email address must have an @-sign. [type=value_error, input_value='not-an-email-address', input_type=str]
    """
```

通常，您可能在 `.json` 文件中拥有大量某种类型的数据。
例如，您可能有一个人员列表：

```json
[
    {
        "name": "John Doe",
        "age": 30,
        "email": "john@example.com"
    },
    {
        "name": "Jane Doe",
        "age": 25,
        "email": "jane@example.com"
    }
]
```

在这种情况下，您可以针对 `list[Person]` 模型验证数据：

```python {test="skip"}
import pathlib

from pydantic import BaseModel, EmailStr, PositiveInt, TypeAdapter


class Person(BaseModel):
    name: str
    age: PositiveInt
    email: EmailStr


person_list_adapter = TypeAdapter(list[Person])  # (1)!

json_string = pathlib.Path('people.json').read_text()
people = person_list_adapter.validate_json(json_string)
print(people)
#> [Person(name='John Doe', age=30, email='john@example.com'), Person(name='Jane Doe', age=25, email='jane@example.com')]
```

1. 我们使用 [`TypeAdapter`][pydantic.type_adapter.TypeAdapter] 来验证 `Person` 对象列表。
[`TypeAdapter`][pydantic.type_adapter.TypeAdapter] 是一个 Pydantic 构造，用于针对单一类型验证数据。

## JSON lines 文件

与验证来自 `.json` 文件的对象列表类似，您可以验证来自 `.jsonl` 文件的对象列表。
`.jsonl` 文件是由换行符分隔的 JSON 对象序列。

考虑以下 `.jsonl` 文件：

```json
{"name": "John Doe", "age": 30, "email": "john@example.com"}
{"name": "Jane Doe", "age": 25, "email": "jane@example.com"}
```

我们可以使用与处理 `.json` 文件类似的方法来验证这些数据：

```python {test="skip"}
import pathlib

from pydantic import BaseModel, EmailStr, PositiveInt


class Person(BaseModel):
    name: str
    age: PositiveInt
    email: EmailStr


json_lines = pathlib.Path('people.jsonl').read_text().splitlines()
people = [Person.model_validate_json(line) for line in json_lines]
print(people)
#> [Person(name='John Doe', age=30, email='john@example.com'), Person(name='Jane Doe', age=25, email='jane@example.com')]
```

## CSV 文件

CSV 是存储表格数据最常见的文件格式之一。
要验证来自 CSV 文件的数据，您可以使用 Python 标准库中的 `csv` 模块来加载
数据，并使用 Pydantic 模型进行验证。

考虑以下 CSV 文件：

```csv
name,age,email
John Doe,30,john@example.com
Jane Doe,25,jane@example.com
```

以下是我们验证这些数据的方法：

```python {test="skip"}
import csv

from pydantic import BaseModel, EmailStr, PositiveInt


class Person(BaseModel):
    name: str
    age: PositiveInt
    email: EmailStr


with open('people.csv') as f:
    reader = csv.DictReader(f)
    people = [Person.model_validate(row) for row in reader]

print(people)
#> [Person(name='John Doe', age=30, email='john@example.com'), Person(name='Jane Doe', age=25, email='jane@example.com')]
```

## TOML 文件

TOML 文件因其简单性和可读性而常用于配置。

考虑以下 TOML 文件：

```toml
name = "John Doe"
age = 30
email = "john@example.com"
```

以下是我们验证这些数据的方法：

```python {test="skip"}
import tomllib

from pydantic import BaseModel, EmailStr, PositiveInt


class Person(BaseModel):
    name: str
    age: PositiveInt
    email: EmailStr


with open('person.toml', 'rb') as f:
    data = tomllib.load(f)

person = Person.model_validate(data)
print(person)
#> name='John Doe' age=30 email='john@example.com'
```

## YAML 文件

YAML（YAML Ain't Markup Language）是一种人类可读的数据序列化格式，常用于配置文件。

考虑以下 YAML 文件：

```yaml
name: John Doe
age: 30
email: john@example.com
```

以下是我们验证这些数据的方法：

```python {test="skip"}
import yaml

from pydantic import BaseModel, EmailStr, PositiveInt


class Person(BaseModel):
    name: str
    age: PositiveInt
    email: EmailStr


with open('person.yaml') as f:
    data = yaml.safe_load(f)

person = Person.model_validate(data)
print(person)
#> name='John Doe' age=30 email='john@example.com'
```

## XML 文件

XML（可扩展标记语言）是一种标记语言，定义了一组规则，用于以人类可读和机器可读的格式编码文档。

考虑以下 XML 文件：

```xml
<?xml version="1.0"?>
<person>
    <name>John Doe</name>
    <age>30</age>
    <email>john@example.com</email>
</person>
```

以下是我们验证这些数据的方法：

```python {test="skip"}
import xml.etree.ElementTree as ET

from pydantic import BaseModel, EmailStr, PositiveInt


class Person(BaseModel):
    name: str
    age: PositiveInt
    email: EmailStr


tree = ET.parse('person.xml').getroot()
data = {child.tag: child.text for child in tree}
person = Person.model_validate(data)
print(person)
#> name='John Doe' age=30 email='john@example.com'
```

## INI 文件

INI 文件是一种简单的配置文件格式，使用节和键值对。它们常用于 Windows 应用程序和较旧的软件。

考虑以下 INI 文件：

```ini
[PERSON]
name = John Doe
age = 30
email = john@example.com
```

以下是我们验证这些数据的方法：

```python {test="skip"}
import configparser

from pydantic import BaseModel, EmailStr, PositiveInt


class Person(BaseModel):
    name: str
    age: PositiveInt
    email: EmailStr


config = configparser.ConfigParser()
config.read('person.ini')
person = Person.model_validate(config['PERSON'])
print(person)
#> name='John Doe' age=30 email='john@example.com'
```