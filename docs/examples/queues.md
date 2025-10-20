---
subtitle: 验证队列数据
description: 使用 Pydantic 验证队列数据：学习如何在 Redis、RabbitMQ 和 ARQ 队列系统中序列化和验证数据，包括完整的代码示例和实现方法。
---

Pydantic 对于验证进出队列的数据非常有帮助。下面，
我们将探讨如何使用各种队列系统来验证/序列化数据。

## Redis 队列

Redis 是一种流行的内存数据结构存储。

为了在本地运行此示例，您首先需要[安装 Redis](https://redis.io/docs/latest/operate/oss_and_stack/install/install-redis/)
并在本地启动服务器。

以下是一个简单的示例，展示如何使用 Pydantic 来：

1. 序列化数据以推送到队列
2. 从队列中弹出数据时进行反序列化和验证

```python {test="skip"}
import redis

from pydantic import BaseModel, EmailStr


class User(BaseModel):
    id: int
    name: str
    email: EmailStr


r = redis.Redis(host='localhost', port=6379, db=0)
QUEUE_NAME = 'user_queue'


def push_to_queue(user_data: User) -> None:
    serialized_data = user_data.model_dump_json()
    r.rpush(QUEUE_NAME, serialized_data)
    print(f'Added to queue: {serialized_data}')


user1 = User(id=1, name='John Doe', email='john@example.com')
user2 = User(id=2, name='Jane Doe', email='jane@example.com')

push_to_queue(user1)
#> 已添加到队列: {"id":1,"name":"John Doe","email":"john@example.com"}

push_to_queue(user2)
#> 已添加到队列: {"id":2,"name":"Jane Doe","email":"jane@example.com"}


def pop_from_queue() -> None:
    data = r.lpop(QUEUE_NAME)

    if data:
        user = User.model_validate_json(data)
        print(f'Validated user: {repr(user)}')
    else:
        print('Queue is empty')


pop_from_queue()
#> 已验证用户: User(id=1, name='John Doe', email='john@example.com')

pop_from_queue()
#> 已验证用户: User(id=2, name='Jane Doe', email='jane@example.com')

pop_from_queue()
#> 队列为空
```

## RabbitMQ

RabbitMQ 是一种流行的消息代理，实现了 AMQP 协议。

为了在本地运行此示例，您首先需要[安装 RabbitMQ](https://www.rabbitmq.com/download.html) 并启动服务器。

以下是一个简单的示例，展示如何使用 Pydantic 来：

1. 序列化数据以推送到队列
2. 从队列中弹出数据时进行反序列化和验证

首先，让我们创建一个发送者脚本。

```python {test="skip"}
import pika

from pydantic import BaseModel, EmailStr


class User(BaseModel):
    id: int
    name: str
    email: EmailStr


connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
QUEUE_NAME = 'user_queue'
channel.queue_declare(queue=QUEUE_NAME)


def push_to_queue(user_data: User) -> None:
    serialized_data = user_data.model_dump_json()
    channel.basic_publish(
        exchange='',
        routing_key=QUEUE_NAME,
        body=serialized_data,
    )
    print(f'Added to queue: {serialized_data}')


user1 = User(id=1, name='John Doe', email='john@example.com')
user2 = User(id=2, name='Jane Doe', email='jane@example.com')

push_to_queue(user1)
#> 已添加到队列: {"id":1,"name":"John Doe","email":"john@example.com"}

push_to_queue(user2)
#> 已添加到队列: {"id":2,"name":"Jane Doe","email":"jane@example.com"}

connection.close()
```

这是接收者脚本。

```python {test="skip"}
import pika

from pydantic import BaseModel, EmailStr


class User(BaseModel):
    id: int
    name: str
    email: EmailStr


def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    QUEUE_NAME = 'user_queue'
    channel.queue_declare(queue=QUEUE_NAME)

    def process_message(
        ch: pika.channel.Channel,
        method: pika.spec.Basic.Deliver,
        properties: pika.spec.BasicProperties,
        body: bytes,
    ):
        user = User.model_validate_json(body)
        print(f'Validated user: {repr(user)}')
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=process_message)
    channel.start_consuming()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
```

要测试此示例：

1. 在一个终端中运行接收者脚本以启动消费者。
2. 在另一个终端中运行发送者脚本以发送消息。

## ARQ

ARQ 是一个快速的基于 Redis 的 Python 作业队列。
它构建在 Redis 之上，提供了一种简单的方式来处理后台任务。

为了在本地运行此示例，您需要[安装 Redis](https://redis.io/docs/latest/operate/oss_and_stack/install/install-redis/) 并启动服务器。

以下是一个简单的示例，展示如何使用 Pydantic 与 ARQ 来：

1. 为作业数据定义模型
2. 在入队作业时序列化数据
3. 在处理作业时验证和反序列化数据

```python {test="skip"}
import asyncio
from typing import Any

from arq import create_pool
from arq.connections import RedisSettings

from pydantic import BaseModel, EmailStr


class User(BaseModel):
    id: int
    name: str
    email: EmailStr


REDIS_SETTINGS = RedisSettings()


async def process_user(ctx: dict[str, Any], user_data: dict[str, Any]) -> None:
    user = User.model_validate(user_data)
    print(f'Processing user: {repr(user)}')


async def enqueue_jobs(redis):
    user1 = User(id=1, name='John Doe', email='john@example.com')
    user2 = User(id=2, name='Jane Doe', email='jane@example.com')

    await redis.enqueue_job('process_user', user1.model_dump())
    print(f'Enqueued user: {repr(user1)}')

    await redis.enqueue_job('process_user', user2.model_dump())
    print(f'Enqueued user: {repr(user2)}')


class WorkerSettings:
    functions = [process_user]
    redis_settings = REDIS_SETTINGS


async def main():
    redis = await create_pool(REDIS_SETTINGS)
    await enqueue_jobs(redis)


if __name__ == '__main__':
    asyncio.run(main())
```

此脚本是完整的。
它应该可以"按原样"运行，既可以入队作业，也可以处理它们。
<!-- TODO: kafka, celery, etc - better for SEO, great for new contributors! -->