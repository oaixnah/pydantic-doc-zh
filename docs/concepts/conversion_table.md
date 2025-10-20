---
description: Pydantic 转换表：详细说明 Pydantic 在严格模式和宽松模式下进行验证时如何转换数据。包含 JSON、Python 数据类型的转换规则，以及在严格模式下的额外转换。
---

以下表格详细说明了 Pydantic 在严格模式和宽松模式下进行验证时如何转换数据。

"Strict" 列包含在 [严格模式](strict_mode.md) 下验证时允许的类型转换的勾选标记。

=== "全部"
{{ conversion_table_all }}

=== "JSON"
{{ conversion_table_json }}

=== "JSON - 严格模式"
{{ conversion_table_json_strict }}

=== "Python"
{{ conversion_table_python }}

=== "Python - 严格模式"
{{ conversion_table_python_strict }}