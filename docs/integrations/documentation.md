Pydantic 使用 [MkDocs](https://www.mkdocs.org/) 进行文档编写，同时结合使用
[mkdocstrings](https://mkdocstrings.github.io/)。因此，您可以利用 Pydantic 的
Sphinx 对象清单来交叉引用 Pydantic API 文档。

=== "Sphinx"

    在您的 [Sphinx 配置](https://www.sphinx-doc.org/en/master/usage/configuration.html)中，
    将以下内容添加到 [`intersphinx` 扩展配置](https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html#configuration)中：

    ```python {test="skip"}
    intersphinx_mapping = {
        'pydantic': ('https://docs.pydantic.dev/latest', None),  # (1)!
    }
    ```

    1. 您也可以使用 `dev` 代替 `latest` 来定位最新的文档构建，与 [`main`](https://github.com/pydantic/pydantic/tree/main) 分支保持同步。

=== "mkdocstrings"

    在您的 [MkDocs 配置](https://www.mkdocs.org/user-guide/configuration/)中，将以下
    导入添加到您的 [mkdocstrings 插件配置](https://mkdocstrings.github.io/usage/#cross-references-to-other-projects-inventories)中：

    ```yaml
    plugins:
    - mkdocstrings:
        handlers:
          python:
            import:
            - https://docs.pydantic.dev/latest/objects.inv  # (1)!
    ```

    1. 您也可以使用 `dev` 代替 `latest` 来定位最新的文档构建，与 [`main`](https://github.com/pydantic/pydantic/tree/main) 分支保持同步。