Pydantic 文档以 [llms.txt](https://llmstxt.org/) 格式提供。
该格式基于 Markdown 定义，适用于大型语言模型。

提供两种格式：

* [llms.txt](https://docs.pydantic.dev/latest/llms.txt)：包含项目简要描述的文件，
  以及指向文档不同部分的链接。该文件的结构在[格式文档](https://llmstxt.org/#format)中有详细描述。
* [llms-full.txt](https://docs.pydantic.dev/latest/llms-full.txt)：类似于 `llms.txt` 文件，
  但包含了每个链接的内容。请注意，此文件可能对某些 LLM 来说过大。

截至目前，这些文件*无法*被 LLM 框架或 IDE 原生利用。或者，
可以实现一个 [MCP 服务器](https://modelcontextprotocol.io/) 来正确解析 `llms.txt` 文件。