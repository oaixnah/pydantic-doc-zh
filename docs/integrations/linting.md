## Flake8 插件

如果在您的项目中使用 Flake8，可以使用一个[插件](https://pypi.org/project/flake8-pydantic/)，
可以通过以下方式安装：

```bash
pip install flake8-pydantic
```

此插件提供的 lint 错误使用 `PYDXXX` 代码进行命名空间划分。要忽略一些不需要的规则，
可以调整 Flake8 配置：

```ini
[flake8]
extend-ignore = PYD001,PYD002
```