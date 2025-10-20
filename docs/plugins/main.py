from __future__ import annotations as _annotations

import json
import logging
import re
import textwrap
from pathlib import Path
from textwrap import indent

import autoflake
import pyupgrade._main as pyupgrade_main  # type: ignore
import tomli
from jinja2 import Template  # type: ignore
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.exceptions import PluginError
from mkdocs.structure.files import Files
from mkdocs.structure.pages import Page

# 日志记录器，用于记录插件运行时的信息
logger = logging.getLogger('mkdocs.plugin')
# 当前文件所在目录
THIS_DIR = Path(__file__).parent
logger.warning(THIS_DIR)
# 文档目录
DOCS_DIR = THIS_DIR.parent
# 项目根目录
PROJECT_ROOT = DOCS_DIR.parent


try:
    from .conversion_table import conversion_table
except ImportError:
    # Due to how MkDocs requires this file to be specified (as a path and not a
    # dot-separated module name), relative imports don't work:
    # MkDocs is adding the dir. of this file to `sys.path` and uses
    # `importlib.spec_from_file_location` and `module_from_spec`, which isn't ideal.
    from conversion_table import conversion_table

# Start definition of MkDocs hooks


def on_pre_build(config: MkDocsConfig) -> None:
    """
    MkDocs预构建钩子函数，在构建开始前执行
    
    Args:
        config: MkDocs配置对象
    """
    if not config.site_url:
        raise PluginError("'site_url' must be set")


def on_page_markdown(markdown: str, page: Page, config: MkDocsConfig, files: Files) -> str:
    """
    MkDocs页面markdown处理钩子函数，在每个文件读取后、转换为HTML前调用
    
    Args:
        markdown: 原始markdown内容
        page: 页面对象
        config: MkDocs配置对象
        files: 文件列表
        
    Returns:
        处理后的markdown内容
    """
    markdown = upgrade_python(markdown)
    markdown = insert_json_output(markdown)
    if md := render_index(markdown, page):
        return md
    if md := render_why(markdown, page):
        return md
    if md := render_pydantic_settings(markdown, page):
        return md
    elif md := build_schema_mappings(markdown, page):
        return md
    elif md := build_conversion_table(markdown, page):
        return md
    elif md := devtools_example(markdown, page):
        return md
    else:
        return markdown


# Python版本升级的最小和最大版本号
MIN_MINOR_VERSION = 9
MAX_MINOR_VERSION = 13


def upgrade_python(markdown: str) -> str:
    """
    对Python代码块应用pyupgrade，除非明确跳过，为每个版本创建标签页
    
    Args:
        markdown: 原始markdown内容
        
    Returns:
        处理后的markdown内容
    """

    def add_tabs(match: re.Match[str]) -> str:
        """内部函数：为代码块添加版本标签页"""
        prefix = match.group(1)
        # 如果标记为跳过升级，则返回原始内容
        if 'upgrade="skip"' in prefix:
            return match.group(0)

        # 检查是否有最低版本要求
        if m := re.search(r'requires="3.(\d+)"', prefix):
            min_minor_version = int(m.group(1))
        else:
            min_minor_version = MIN_MINOR_VERSION

        py_code = match.group(2)
        numbers = match.group(3)
        # import devtools
        # devtools.debug(numbers)
        output = []
        last_code = py_code
        # 为每个版本生成代码块
        for minor_version in range(min_minor_version, MAX_MINOR_VERSION + 1):
            if minor_version == min_minor_version:
                tab_code = py_code
            else:
                tab_code = _upgrade_code(py_code, minor_version)
                # 如果代码与上一个版本相同，则跳过
                if tab_code == last_code:
                    continue
                last_code = tab_code

            content = indent(f'{prefix}\n{tab_code}```{numbers}', ' ' * 4)
            output.append(f'=== "Python 3.{minor_version} and above"\n\n{content}')

        # 如果只有一个版本，返回原始内容
        if len(output) == 1:
            return match.group(0)
        else:
            return '\n\n'.join(output)

    # Note: we should move away from this regex approach. It does not handle edge cases (indented code blocks inside
    # other blocks, etc) and can lead to bugs in the rendering of annotations. Edit with care and make sure the rendered
    # documentation does not break:
    return re.sub(r'(``` *py.*?)\n(.+?)^```(\s+(?:^\d+\. (?:[^\n][\n]?)+\n?)*)', add_tabs, markdown, flags=re.M | re.S)


def _upgrade_code(code: str, min_version: int) -> str:
    """
    使用pyupgrade升级Python代码到指定版本
    
    Args:
        code: 原始Python代码
        min_version: 目标Python版本的小版本号
        
    Returns:
        升级后的Python代码
    """
    upgraded = pyupgrade_main._fix_plugins(
        code,
        settings=pyupgrade_main.Settings(
            min_version=(3, min_version),
            keep_percent_format=True,
            keep_mock=False,
            keep_runtime_typing=True,
        ),
    )
    # 使用autoflake移除未使用的导入
    return autoflake.fix_code(upgraded, remove_all_unused_imports=True)


def insert_json_output(markdown: str) -> str:
    """
    查找`output="json"`代码块标签并替换为单独的JSON部分
    
    Args:
        markdown: 原始markdown内容
        
    Returns:
        处理后的markdown内容
    """

    def replace_json(m: re.Match[str]) -> str:
        """内部函数：替换JSON输出"""
        start, attrs, code = m.groups()

        def replace_last_print(m2: re.Match[str]) -> str:
            """内部函数：替换最后一个print语句为JSON输出"""
            ind, json_text = m2.groups()
            json_text = indent(json.dumps(json.loads(json_text), indent=2), ind)
            # 没有尾部的代码块标记，因为那不是代码的一部分
            return f'\n{ind}```\n\n{ind}JSON output:\n\n{ind}```json\n{json_text}\n'

        code = re.sub(r'\n( *)"""(.*?)\1"""\n$', replace_last_print, code, flags=re.S)
        return f'{start}{attrs}{code}{start}\n'

    return re.sub(r'(^ *```)([^\n]*?output="json"[^\n]*?\n)(.+?)\1', replace_json, markdown, flags=re.M | re.S)


def get_orgs_data() -> list[dict[str, str]]:
    """
    从orgs.toml文件获取组织数据
    
    Returns:
        组织数据列表
    """
    with (THIS_DIR / 'orgs.toml').open('rb') as f:
        orgs_data = tomli.load(f)
    return orgs_data['orgs']


def render_index(markdown: str, page: Page) -> str | None:
    """
    渲染首页内容
    
    Args:
        markdown: 原始markdown内容
        page: 页面对象
        
    Returns:
        处理后的markdown内容，如果不是首页则返回None
    """
    if page.file.src_uri != 'index.md':
        return None

    # 组织logo的HTML模板
    tile_template = """
<div class="tile">
  <a href="why/#org-{key}" title="{name}">
    <img src="logos/{key}_logo.png" alt="{name}" />
  </a>
</div>"""

    # 生成组织logo网格
    elements = [tile_template.format(**org) for org in get_orgs_data()]

    orgs_grid = f'<div id="grid-container"><div id="company-grid" class="grid">{"".join(elements)}</div></div>'
    return re.sub(r'{{ *organisations *}}', orgs_grid, markdown)


def render_why(markdown: str, page: Page) -> str | None:
    """
    渲染why页面内容
    
    Args:
        markdown: 原始markdown内容
        page: 页面对象
        
    Returns:
        处理后的markdown内容，如果不是why页面则返回None
    """
    if page.file.src_uri != 'why.md':
        return None

    # 从using.toml文件获取库数据
    with (THIS_DIR / 'using.toml').open('rb') as f:
        using = tomli.load(f)['libs']

    # 生成库列表
    libraries = '\n'.join('* [`{repo}`](https://github.com/{repo}) {stars:,} stars'.format(**lib) for lib in using)
    markdown = re.sub(r'{{ *libraries *}}', libraries, markdown)
    default_description = '_(Based on the criteria described above)_'

    # 生成组织描述
    elements = [
        f'### {org["name"]} {{#org-{org["key"]}}}\n\n{org.get("description") or default_description}'
        for org in get_orgs_data()
    ]
    return re.sub(r'{{ *organisations *}}', '\n\n'.join(elements), markdown)


def render_pydantic_settings(markdown: str, page: Page) -> str | None:
    """
    渲染pydantic-settings页面内容
    
    Args:
        markdown: 原始markdown内容
        page: 页面对象
        
    Returns:
        处理后的markdown内容，如果不是pydantic-settings页面则返回None
    """
    if page.file.src_uri != 'concepts/pydantic_settings.md':
        return None

    docs_content = (PROJECT_ROOT / 'pydantic-settings/index.md').read_text()

    return re.sub(r'{{ *pydantic_settings *}}', docs_content, markdown)


def _generate_table_row(col_values: list[str]) -> str:
    """
    生成Markdown表格行
    
    Args:
        col_values: 列值列表
        
    Returns:
        Markdown表格行字符串
    """
    return f'| {" | ".join(col_values)} |\n'


def _generate_table_heading(col_names: list[str]) -> str:
    """
    生成Markdown表格标题行
    
    Args:
        col_names: 列名列表
        
    Returns:
        Markdown表格标题字符串
    """
    return _generate_table_row(col_names) + _generate_table_row(['-'] * len(col_names))


def build_schema_mappings(markdown: str, page: Page) -> str | None:
    """
    构建JSON Schema映射表
    
    Args:
        markdown: 原始markdown内容
        page: 页面对象
        
    Returns:
        处理后的markdown内容，如果不是JSON Schema页面则返回None
    """
    if page.file.src_uri != 'concepts/json_schema.md':
        return None

    # 表格列名
    col_names = [
        'Python type',
        'JSON Schema Type',
        'Additional JSON Schema',
        'Defined in',
        'Notes',
    ]
    table_text = _generate_table_heading(col_names)

    # 从schema_mappings.toml文件加载表格数据
    with (THIS_DIR / 'schema_mappings.toml').open('rb') as f:
        table = tomli.load(f)

    # 生成表格行
    for t in table.values():
        py_type = t.get('py_type', '')
        json_type = t.get('json_type', '')
        additional = t.get('additional', '')
        defined_in = t.get('defined_in', '')
        notes = t.get('notes', '')
        if additional and not isinstance(additional, str):
            additional = json.dumps(additional)
        cols = [f'`{py_type}`', f'`{json_type}`', f'`{additional}`' if additional else '', defined_in, notes]
        table_text += _generate_table_row(cols)

    return re.sub(r'{{ *schema_mappings_table *}}', table_text, markdown)


def build_conversion_table(markdown: str, page: Page) -> str | None:
    """
    构建转换表
    
    Args:
        markdown: 原始markdown内容
        page: 页面对象
        
    Returns:
        处理后的markdown内容，如果不是转换表页面则返回None
    """
    if page.file.src_uri != 'concepts/conversion_table.md':
        return None

    # 定义不同过滤条件的转换表
    filtered_table_predicates = {
        'all': lambda r: True,
        'json': lambda r: r.json_input,
        'json_strict': lambda r: r.json_input and r.strict,
        'python': lambda r: r.python_input,
        'python_strict': lambda r: r.python_input and r.strict,
    }

    # 为每种过滤条件生成对应的转换表
    for table_id, predicate in filtered_table_predicates.items():
        table_markdown = conversion_table.filtered(predicate).as_markdown()
        table_markdown = textwrap.indent(table_markdown, '    ')
        markdown = re.sub(rf'{{{{ *conversion_table_{table_id} *}}}}', table_markdown, markdown)

    return markdown


def devtools_example(markdown: str, page: Page) -> str | None:
    """
    渲染devtools示例
    
    Args:
        markdown: 原始markdown内容
        page: 页面对象
        
    Returns:
        处理后的markdown内容，如果不是devtools页面则返回None
    """
    if page.file.src_uri != 'integrations/devtools.md':
        return None

    # 从HTML文件读取devtools输出示例
    html = (THIS_DIR / 'devtools_output.html').read_text().strip('\n')
    full_html = f'<div class="highlight">\n<pre><code>{html}</code></pre>\n</div>'
    return re.sub(r'{{ *devtools_example *}}', full_html, markdown)