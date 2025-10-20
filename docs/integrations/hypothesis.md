[Hypothesis](https://hypothesis.readthedocs.io/) 是用于[基于属性的测试](https://increment.com/testing/in-praise-of-property-based-testing/)的 Python 库。
Hypothesis 可以推断如何构造类型注解的类，并默认支持内置类型、许多标准库类型，以及来自 [`typing`](https://docs.python.org/3/library/typing.html) 和 [`typing_extensions`](https://pypi.org/project/typing-extensions/) 模块的泛型类型。

Pydantic v2.0 放弃了对 Hypothesis 的内置支持，不再提供集成的 Hypothesis 插件。

!!! warning
    我们暂时移除 Hypothesis 插件，以便研究不同的机制。更多信息请参阅问题 [annotated-types/annotated-types#37](https://github.com/annotated-types/annotated-types/issues/37)。

    Hypothesis 插件可能会在未来的版本中回归。请订阅 [pydantic/pydantic#4682](https://github.com/pydantic/pydantic/issues/4682) 以获取更新。