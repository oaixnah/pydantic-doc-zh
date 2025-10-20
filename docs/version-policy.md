---
subtitle: 版本策略
---

# 版本策略

首先，我们认识到从 Pydantic V1 到 V2 的过渡对某些用户来说已经并将继续是痛苦的。
我们对这种痛苦表示歉意 :pray:，这是纠正 V1 设计错误的不幸但必要的步骤。

**不会再出现这种规模的中断性变更！**

## Pydantic V1

V1 的积极开发已经停止，但关键的错误修复和安全漏洞将在 V1 中修复，直到 Pydantic V3 发布。

## Pydantic V2

我们不会在 V2 的次要版本中故意进行中断性变更。

标记为已弃用的功能将不会在下一个主要版本 V3 发布之前被移除。

当然，一些看似安全的更改和错误修复不可避免地会破坏某些用户的代码 &mdash; 必须链接到 [xkcd](https://xkcd.com/1172/)。

以下更改将**不会**被视为中断性变更，并且可能在次要版本中发生：

* 可能导致现有代码破坏的错误修复，前提是该代码依赖于未记录的功能/构造。
* 更改 JSON Schema [引用](https://json-schema.org/understanding-json-schema/structuring#dollarref)的格式。
* 更改 [`ValidationError`][pydantic_core.ValidationError] 异常的 `msg`、`ctx` 和 `loc` 字段。`type` 不会更改 &mdash; 如果您以编程方式解析错误消息，应该使用 `type`。
* 向 [`ValidationError`][pydantic_core.ValidationError] 异常添加新键 &mdash; 例如，一旦我们迁移到新的 JSON 解析器，我们打算在验证 JSON 时向错误添加 `line_number` 和 `column_number`。
* 添加新的 [`ValidationError`][pydantic_core.ValidationError] 错误。
* 更改 `__repr__` 的行为，即使是公共类也是如此。
* [核心模式](./internals/architecture.md#communicating-between-pydantic-and-pydantic-core-the-core-schema)的内容（通常可在 Pydantic 模型的 [`__pydantic_core_schema__`][pydantic.BaseModel.__pydantic_core_schema__] 属性和[类型适配器](./concepts/type_adapter.md)的 `core_schema` 下获得）可能在版本之间更改（这是 Pydantic 用于规划如何执行验证和序列化的低级格式）。

在所有情况下，我们将旨在最小化变动，并且仅在提高 Pydantic 对用户的质量有充分理由时才这样做。

## Pydantic V3 及以后

我们预计未来大约每年发布一次新的主要版本，尽管如上所述，任何相关的中断性变更与 V1 到 V2 的过渡相比应该很容易修复。

## 实验性功能 {#experimental-features}

在 Pydantic，我们喜欢快速行动和创新！为此，我们可能在次要版本中引入实验性功能。

!!! abstract "使用文档"
    要了解我们当前的实验性功能，请参阅[实验性功能文档](./concepts/experimental.md)。

请记住，实验性功能是正在进行中的工作。如果这些功能成功，它们最终将成为 Pydantic 的一部分。如果不成功，这些功能将在很少通知的情况下被移除。在实验阶段，功能的 API 和行为可能不稳定，并且对该功能所做的更改很可能不会向后兼容。

### 命名约定

我们使用以下命名约定之一来指示某个功能是实验性的：

1. 该功能位于 [`experimental`](api/experimental.md) 模块中。在这种情况下，您可以这样访问该功能：

    ```python {test="skip" lint="skip"}
    from pydantic.experimental import feature_name
    ```

2. 该功能位于主模块中，但前缀为 `experimental_`。这种情况发生在我们向主 `pydantic` 模块中已有的现有数据结构添加新字段、参数或方法时。

具有这些命名约定的新功能可能会更改或移除，我们正在寻求反馈和建议，然后再将它们作为 Pydantic 的永久部分。有关更多信息，请参阅[反馈部分](./concepts/experimental.md#feedback)。

### 实验性功能的生命周期

1. 添加一个新功能，要么在 [`experimental`](api/experimental.md) 模块中，要么带有 `experimental_` 前缀。
2. 在补丁/次要版本期间通常会修改行为，可能会有 API/行为更改。
3. 如果该功能成功，我们通过以下步骤将其提升到 Pydantic：

    a. 如果它在 [`experimental`](api/experimental.md) 模块中，该功能将被克隆到 Pydantic 的主模块。原始实验性功能仍然保留在 [`experimental`](api/experimental.md) 模块中，但在使用时将显示警告。如果该功能已经在主 Pydantic 模块中，我们创建该功能的副本而不带 `experimental_` 前缀，因此该功能同时存在官方名称和实验性名称。弃用警告附加到实验版本。

    b. 在某个时候，实验性功能的代码被移除，但该功能的存根仍然存在，提供带有适当说明的错误消息。

    c. 作为最后一步，实验版本的功能完全从代码库中移除。

如果该功能不成功或不受欢迎，它将在很少通知的情况下被移除。弃用功能的位置将保留一个存根，其中包含错误消息。

感谢 [streamlit](https://docs.streamlit.io/develop/quick-reference/prerelease) 为我们新的实验性功能模式的生命周期和命名约定提供了灵感。

## 对 Python 版本的支持

当满足以下条件时，Pydantic 将停止对 Python 版本的支持：

* Python 版本已达到其[预期生命周期结束](https://devguide.python.org/versions/)。
* 最近次要版本的下载量中，使用该版本的下载量少于 5%。