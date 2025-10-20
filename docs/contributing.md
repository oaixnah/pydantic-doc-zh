---
subtitle: 贡献
---

# 贡献

我们非常欢迎您为 Pydantic 做出贡献！

## 问题报告

问题、功能请求和错误报告都可以通过[讨论或问题](https://github.com/pydantic/pydantic/issues/new/choose)的方式提出。
**但是，要报告安全漏洞，请参阅我们的[安全策略](https://github.com/pydantic/pydantic/security/policy)。**

为了让我们尽可能简单地帮助您，请在您的问题中包含以下调用的输出：

```bash
python -c "import pydantic.version; print(pydantic.version.version_info())"
```

如果您使用的是 **v2.0** 之前的 Pydantic，请使用：

```bash
python -c "import pydantic.utils; print(pydantic.utils.version_info())"
```

除非您无法安装 Pydantic 或**知道**它与您的问题或功能请求无关，否则请始终包含上述信息。

## 拉取请求

开始创建拉取请求应该非常简单。
Pydantic 会定期发布，因此您应该能在几天或几周内看到您的改进发布 🚀。

除非您的更改是微不足道的（拼写错误、文档调整等），否则请在创建拉取请求之前创建一个问题来讨论更改。

!!! note "Pydantic V1 处于维护模式"
    Pydantic v1 处于维护模式，意味着只接受错误修复和安全修复。
    新功能应该针对 Pydantic v2。

    要向 Pydantic v1 提交修复，请使用 `1.10.X-fixes` 作为目标分支。

如果您正在寻找一些有挑战性的工作，请查看 GitHub 上的
["help wanted"](https://github.com/pydantic/pydantic/issues?q=is%3Aopen+is%3Aissue+label%3A%22help+wanted%22)
标签。

为了使贡献尽可能简单快捷，您需要在本地运行测试和代码检查。幸运的是，
Pydantic 依赖项很少，不需要编译，测试也不需要访问数据库等。
因此，设置和运行测试应该非常简单。

!!! tip
    **tl;dr**：使用 `make format` 修复格式，使用 `make` 运行测试和代码检查，使用 `make docs`
    构建文档。

### 先决条件

您需要以下先决条件：

* **Python 3.9 到 3.12** 之间的任何 Python 版本
* [**uv**](https://docs.astral.sh/uv/getting-started/installation/) 或其他虚拟环境工具
* **git**
* **make**

### 安装和设置

在 GitHub 上 fork 仓库并在本地克隆您的 fork。

```bash
# 克隆您的 fork 并进入仓库目录
git clone git@github.com:<your username>/pydantic.git
cd pydantic

# 安装 UV 和 pre-commit
# 我们在这里使用 pipx，有关其他选项请参阅：
# https://docs.astral.sh/uv/getting-started/installation/
# https://pre-commit.com/#install
# 要获取 pipx 本身：
# https://pypa.github.io/pipx/
pipx install uv
pipx install pre-commit

# 安装 pydantic、依赖项、测试依赖项和文档依赖项
make install
```

### 检出新分支并进行更改

为您的更改创建一个新分支。

```bash
# 检出新分支并进行更改
git checkout -b my-new-feature-branch
# 进行您的更改...
```

### 运行测试和代码检查

在本地运行测试和代码检查，确保一切按预期工作。

```bash
# 运行自动化代码格式化和代码检查
make format
# Pydantic 使用 ruff，一个用 rust 编写的优秀 Python 代码检查器
# https://github.com/astral-sh/ruff

# 运行测试和代码检查
make
# Makefile 中有一些子命令，如 `test`、`testcov` 和 `lint`
# 您可能想要使用这些命令，但通常只需 `make` 就足够了。
# 您可以运行 `make help` 查看更多选项。
```

### 构建文档

如果您对文档进行了任何更改（包括对函数签名、类定义或将在 API 文档中出现的文档字符串的更改），请确保文档构建成功。

我们使用 `mkdocs-material[imaging]` 来支持社交预览（请参阅[插件文档](https://squidfunk.github.io/mkdocs-material/plugins/requirements/image-processing/)）。

```bash
# 构建文档
make docs
# 如果您更改了文档，请确保它构建成功。
# 您也可以使用 `uv run mkdocs serve` 在 localhost:8000 上提供文档服务
```

如果由于图像插件的问题导致无法正常工作，请尝试注释掉 `mkdocs.yml` 中的 `social` 插件行，然后再次运行 `make docs`。

#### 更新文档

我们会在每个次要版本发布时推送新版本的文档，并在每次提交到 `main` 时推送到 `dev` 路径。

如果您在次要版本发布周期之外更新文档，并希望您的更改反映在 `latest` 上，
请执行以下操作：

1. 针对 `main` 分支打开一个包含文档更改的 PR
2. PR 合并后，检出 `docs-update` 分支。此分支应与最新的补丁版本保持同步。
例如，如果最新版本是 `v2.9.2`，您应确保 `docs-update` 与 `v2.9.2` 标签保持同步。
3. 从 `docs-update` 检出一个新分支，并将您的更改 cherry-pick 到此分支。
4. 推送您的更改并针对 `docs-update` 打开一个 PR。
5. PR 合并后，新文档将被构建和部署。

!!! note
    维护者快捷方式 - 作为维护者，您可以跳过第二个 PR，直接 cherry-pick 到 `docs-update` 分支。

### 提交并推送您的更改

提交您的更改，将分支推送到 GitHub，并创建一个拉取请求。

请遵循拉取请求模板并尽可能填写完整信息。链接到任何相关问题并包含对您更改的描述。

当您的拉取请求准备好进行审查时，添加一条包含 "please review" 消息的评论，我们会尽快查看。

## 文档风格

文档使用 Markdown 编写，并使用 [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) 构建。API 文档使用 [mkdocstrings](https://mkdocstrings.github.io/) 从文档字符串构建。

### 代码文档

在为 Pydantic 做贡献时，请确保所有代码都有良好的文档记录。以下内容应使用正确格式的文档字符串进行记录：

* 模块
* 类定义
* 函数定义
* 模块级变量

Pydantic 使用 [Google 风格的文档字符串](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)，按照 [PEP 257](https://www.python.org/dev/peps/pep-0257/) 指南格式化。（有关更多示例，请参阅[Google 风格 Python 文档字符串示例](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html)。）

[pydocstyle](https://www.pydocstyle.org/en/stable/index.html) 用于检查文档字符串。您可以运行 `make format` 来检查您的文档字符串。

当 Google 风格的文档字符串与 pydocstyle 检查存在冲突时，请遵循 pydocstyle 的检查提示。

类属性和函数参数应以 "名称: 描述。" 的格式进行记录。适用时，返回类型应仅包含描述。类型从签名中推断。

```python
class Foo:
    """一个类文档字符串。

    Attributes:
        bar: bar 的描述。默认为 "bar"。
    """

    bar: str = 'bar'
```

```python
def bar(self, baz: int) -> str:
    """一个函数文档字符串。

    Args:
        baz: `baz` 的描述。

    Returns:
        返回值的描述。
    """

    return 'bar'
```

您可以在文档字符串中包含示例代码。此代码应该是完整、自包含且可运行的。文档字符串示例会被测试，因此请确保它们正确且完整。有关示例，请参阅 [`FieldInfo.from_annotated_attribute`][pydantic.fields.FieldInfo.from_annotated_attribute]。

!!! note "类和实例属性"
    类属性应在类文档字符串中记录。

    实例属性应在 `__init__` 文档字符串中作为 "Args" 记录。

### 文档风格

一般来说，文档应该以友好、平易近人的风格编写。它应该易于阅读和理解，并且在保持完整的同时尽可能简洁。

鼓励使用代码示例，但应保持简短和简单。然而，每个代码示例都应该是完整、自包含且可运行的。（如果您不确定如何做到这一点，请寻求帮助！）我们更喜欢打印输出而不是裸断言，但如果您测试的内容没有有用的打印输出，断言也可以。

Pydantic 的单元测试将测试文档中的所有代码示例，因此确保它们正确且完整非常重要。添加新的代码示例时，请使用以下命令来测试示例并更新其格式和输出：

```bash
# 运行测试并更新代码示例
pytest tests/test_docs.py --update-examples
```

## 调试 Python 和 Rust

如果您正在使用 `pydantic` 和 `pydantic-core`，您可能会发现同时调试 Python 和 Rust 代码很有帮助。
这里是一个快速指南，介绍如何做到这一点。本教程是在 VSCode 中完成的，但您可以在其他 IDE 中使用类似的步骤。

<div style="position: relative; padding-bottom: 56.4035546262415%; height: 0;">
    <iframe src="https://www.loom.com/embed/71019f8b92b04839ae233eb70c23c5b5?sid=1ea39ca9-d0cc-494b-8214-159f7cc26190" frameborder="0" webkitallowfullscreen mozallowfullscreen allowfullscreen style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;">
    </iframe>
</div>

## 徽章

[![Pydantic v1](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/pydantic/pydantic/main/docs/badge/v1.json)](https://pydantic.dev)
[![Pydantic v2](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/pydantic/pydantic/main/docs/badge/v2.json)](https://pydantic.dev)

Pydantic 有一个徽章，您可以用它来显示您的项目使用了 Pydantic。您可以在 `README.md` 中使用此徽章：

### 使用 Markdown

```md
[![Pydantic v1](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/pydantic/pydantic/main/docs/badge/v1.json)](https://pydantic.dev)

[![Pydantic v2](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/pydantic/pydantic/main/docs/badge/v2.json)](https://pydantic.dev)
```

### 使用 reStructuredText

```rst
.. image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/pydantic/pydantic/main/docs/badge/v1.json
    :target: https://pydantic.dev
    :alt: Pydantic

.. image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/pydantic/pydantic/main/docs/badge/v2.json
    :target: https://pydantic.dev
    :alt: Pydantic
```

### 使用 HTML

```html
<a href="https://pydantic.dev"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/pydantic/pydantic/main/docs/badge/v1.json" alt="Pydantic Version 1" style="max-width:100%;"></a>

<a href="https://pydantic.dev"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/pydantic/pydantic/main/docs/badge/v2.json" alt="Pydantic Version 2" style="max-width:100%;"></a>
```

## 将您的库添加为 Pydantic 第三方测试套件的一部分

为了能够在开发过程中及早识别回归问题，Pydantic 会在各种使用 Pydantic 的第三方项目上运行测试。
如果您的项目符合以下一些标准，我们会考虑添加对测试新的开源项目（严重依赖 Pydantic）的支持：

* 项目正在积极维护。
* 项目使用了 Pydantic 的内部结构（例如，依赖于 [`BaseModel`][pydantic.BaseModel] 元类、类型工具）。
* 项目足够受欢迎（尽管根据 Pydantic 的使用方式，小型项目仍可能被包含）。
* 项目的 CI 足够简单，可以移植到 Pydantic 的测试工作流中。

如果您的项目符合其中一些标准，您可以[打开功能请求][open feature request]
来讨论将您的项目包含在内。

[open feature request]: https://github.com/pydantic/pydantic/issues/new?assignees=&labels=feature+request&projects=&template=feature_request.yml