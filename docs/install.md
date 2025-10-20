---
subtitle: 安装
---

# 安装

非常简单：

=== "pip"

    ```bash
    pip install pydantic
    ```

=== "uv"

    ```bash
    uv add pydantic
    ```

Pydantic 有几个依赖项：

* [`pydantic-core`](https://pypi.org/project/pydantic-core/)：用 Rust 编写的 Pydantic 核心验证逻辑。
* [`typing-extensions`](https://pypi.org/project/typing-extensions/)：标准库 [typing][] 模块的后向移植。
* [`annotated-types`](https://pypi.org/project/annotated-types/)：与 [`typing.Annotated`][] 一起使用的可重用约束类型。

如果您已经安装了 Python 3.9+ 和 `pip`，那么您就可以开始使用了。

Pydantic 也可以在 [conda](https://www.anaconda.com) 的 [conda-forge](https://conda-forge.org) 频道上获取：

```bash
conda install pydantic -c conda-forge
```

## 可选依赖项

Pydantic 有以下可选依赖项：

* `email`：由 [email-validator](https://pypi.org/project/email-validator/) 包提供的电子邮件验证。
* `timezone`：由 [tzdata](https://pypi.org/project/tzdata/) 包提供的备用 IANA 时区数据库。

要安装 Pydantic 及其可选依赖项：

=== "pip"

    ```bash
    # 包含 `email` 额外依赖：
    pip install 'pydantic[email]'
    # 或包含 `email` 和 `timezone` 额外依赖：
    pip install 'pydantic[email,timezone]'
    ```

=== "uv"

    ```bash
    # 包含 `email` 额外依赖：
    uv add 'pydantic[email]'
    # 或包含 `email` 和 `timezone` 额外依赖：
    uv add 'pydantic[email,timezone]'
    ```

当然，您也可以使用 `pip install email-validator tzdata` 手动安装需求。

## 从仓库安装

如果您希望直接从仓库安装 Pydantic：

=== "pip"

    ```bash
    pip install 'git+https://github.com/pydantic/pydantic@main'
    # 或包含 `email` 和 `timezone` 额外依赖：
    pip install 'git+https://github.com/pydantic/pydantic@main#egg=pydantic[email,timezone]'
    ```

=== "uv"

    ```bash
    uv add 'git+https://github.com/pydantic/pydantic@main'
    # 或包含 `email` 和 `timezone` 额外依赖：
    uv add 'git+https://github.com/pydantic/pydantic@main#egg=pydantic[email,timezone]'
    ```