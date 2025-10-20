`pydantic` 与 AWS Lambda 函数集成良好。在本指南中，我们将讨论如何为 AWS Lambda 函数设置 `pydantic`。

## 为 AWS Lambda 函数安装 Python 库

在 AWS Lambda 函数中使用 Python 库有多种方式。如 [AWS Lambda 文档](https://docs.aws.amazon.com/lambda/latest/dg/lambda-python.html) 所述，最常见的方法包括：

* 使用 [`.zip` 文件归档](https://docs.aws.amazon.com/lambda/latest/dg/python-package.html) 打包代码和依赖项
* 使用 [AWS Lambda 层](https://docs.aws.amazon.com/lambda/latest/dg/python-layers.html) 在多个函数之间共享库
* 使用 [容器镜像](https://docs.aws.amazon.com/lambda/latest/dg/python-image.html) 打包代码和依赖项

所有这些方法都可以与 `pydantic` 一起使用。最适合您的方法将取决于您的具体需求和约束。我们将在这里更深入地介绍前两种情况，因为使用容器镜像的依赖项管理更为直接。如果您使用容器镜像，您可能会发现 [此评论](https://github.com/pydantic/pydantic/issues/6557#issuecomment-1699456562) 对安装 `pydantic` 有帮助。

!!! tip
    如果您在多个函数中使用 `pydantic`，您可能需要考虑 AWS Lambda 层，它支持在多个函数之间无缝共享库。

无论您选择哪种依赖项管理方法，遵循这些指南都有助于确保依赖项管理过程顺利进行。

## 为 AWS Lambda 函数安装 `pydantic`

当您使用代码和依赖项构建 `.zip` 文件归档或为 Lambda 层组织 `.zip` 文件时，您可能会使用本地虚拟环境来安装和管理依赖项。如果您使用 `pip`，这可能会有点棘手，因为 `pip` 会安装为本地平台编译的 wheel 包，这可能与 Lambda 环境不兼容。

因此，我们建议您使用类似于以下命令：

```bash
pip install \
    --platform manylinux2014_x86_64 \  # (1)!
    --target=<your_package_dir> \  # (2)!
    --implementation cp \  # (3)!
    --python-version 3.10 \  # (4)!
    --only-binary=:all: \  # (5)!
    --upgrade pydantic  # (6)!
```

1. 使用与您的 Lambda 运行时对应的平台。
2. 指定要安装包的目录（对于 Lambda 层通常是 `python`）。
3. 使用 CPython 实现。
4. Python 版本必须与 Lambda 运行时兼容。
5. 此标志确保安装预构建的二进制 wheel 包。
6. 将安装最新版本的 `pydantic`。

## 故障排除

### 缺少 `pydantic_core` 模块

```output
no module named `pydantic_core._pydantic_core`
```

错误是一个常见问题，表明您安装 `pydantic` 的方式不正确。要调试此问题，您可以尝试以下步骤（在失败的导入之前）：

1. 检查已安装的 `pydantic-core` 包的内容。编译的库及其类型存根是否都存在？

    ```python {test="skip" lint="skip"}
    from importlib.metadata import files
    print([file for file in files('pydantic-core') if file.name.startswith('_pydantic_core')])
    """
    [PackagePath('pydantic_core/_pydantic_core.pyi'), PackagePath('pydantic_core/_pydantic_core.cpython-312-x86_64-linux-gnu.so')]
    """
    ```

    您应该期望看到如上打印的两个文件。编译的库文件应具有 `.so` 或 `.pyd` 扩展名，其名称根据操作系统和 Python 版本而变化。

2. 检查您的 lambda 的 Python 版本是否与上面找到的编译库版本兼容。

    ```python {test="skip" lint="skip"}
    import sysconfig
    print(sysconfig.get_config_var("EXT_SUFFIX"))
    #> '.cpython-312-x86_64-linux-gnu.so'
    ```

您应该期望在这里看到与编译库相同的后缀，例如这里我们看到后缀 `.cpython-312-x86_64-linux-gnu.so` 确实与 `_pydantic_core.cpython-312-x86_64-linux-gnu.so` 匹配。

如果这两个检查不匹配，您的构建步骤没有为您的 lambda 目标平台安装正确的本地代码。您应该调整构建步骤以更改安装的库版本。

最可能的错误：

* 您的操作系统或 CPU 架构不匹配（例如 darwin 与 x86_64-linux-gnu）。在安装 lambda 依赖项时尝试传递正确的 `--platform` 参数，或在正确的平台内的 linux docker 容器中构建。目前可能的平台包括 `--platform manylinux2014_x86_64` 或 `--platform manylinux2014_aarch64`，但这些可能会随着未来的 Pydantic 主要版本而改变。

* 您的 Python 版本不匹配（例如 `cpython-310` 与 `cpython-312`）。尝试传递正确的 `--python-version` 参数给 `pip install`，或者更改构建中使用的 Python 版本。

### 未找到 `email-validator` 的包元数据

Pydantic 使用 `importlib.metadata` 中的 `version` 来 [检查安装了哪个版本](https://github.com/pydantic/pydantic/pull/6033) 的 `email-validator`。
这种包版本控制机制与 AWS Lambda 有些不兼容，尽管它是 Python 中版本控制包的行业标准。有几种方法可以解决此问题：

如果您使用 serverless 框架部署 lambda，很可能 `email-validator` 包的适当元数据未包含在您的部署包中。像 [`serverless-python-requirements`](https://github.com/serverless/serverless-python-requirements/tree/master) 这样的工具会删除元数据以减少包大小。您可以通过在 `serverless.yml` 文件中将 `slim` 设置设置为 false 来解决此问题：

```yaml
pythonRequirements:
    dockerizePip: non-linux
    slim: false
    fileName: requirements.txt
```

您可以在此 [博客文章](https://biercoff.com/how-to-fix-package-not-found-error-importlib-metadata/) 中阅读有关此修复以及其他可能相关的 `slim` 设置的更多信息。

如果您使用 `.zip` 归档文件来存储代码和/或依赖项，请确保您的包包含所需的版本元数据。为此，请确保在您的 `.zip` 归档文件中包含 `email-validator` 包的 `dist-info` 目录。

此问题已在其他流行的 Python 库（如 [`jsonschema`](https://github.com/python-jsonschema/jsonschema/issues/584)）中报告，因此您也可以在那里阅读有关此问题和潜在修复的更多信息。

## 额外资源

### 更多调试技巧

如果您仍在为 AWS Lambda 安装 `pydantic` 而苦苦挣扎，您可以查阅 [此问题](https://github.com/pydantic/pydantic/issues/6557)，其中涵盖了其他开发人员遇到的各种问题和解决方案。

### 验证 `event` 和 `context` 数据

查看我们的 [博客文章](https://pydantic.dev/articles/lambda-intro)，了解有关如何使用 `pydantic` 验证 AWS Lambda 函数中的 `event` 和 `context` 数据的更多信息。