#!/usr/bin/env python3
"""Markdown → PDF 转换工具 (纯Python，无需pandoc)
用法:  uv run python3 test/md2pdf_pure.py <input.md> [output.pdf]

依赖: weasyprint, marko, latex2mathml
特点: 纯 Python 实现，零外部二进制依赖
"""

import sys, os, re
from weasyprint import HTML
from marko import Markdown
from latex2mathml.converter import convert as tex2mathml

# LaTeX 中应渲染为直体（正体）的函数名
_FUNC_NAMES = {
    'sin', 'cos', 'tan', 'cot', 'sec', 'csc',
    'arcsin', 'arccos', 'arctan', 'arccot', 'arcsec', 'arccsc',
    'sinh', 'cosh', 'tanh', 'coth', 'sech', 'csch',
    'exp', 'log', 'ln', 'lg',
    'lim', 'limsup', 'liminf',
    'max', 'min', 'sup', 'inf',
    'det', 'dim', 'ker', 'hom', 'Pr', 'gcd', 'deg', 'arg',
    'Re', 'Im',
}


def _fix_mathml_func_names(mathml: str) -> str:
    """给 latex2mathml 输出的 MathML 中已知函数名加上 mathvariant="normal" """
    def _tag_func(m):
        name = m.group(1)
        if name in _FUNC_NAMES:
            return f'<mi mathvariant="normal">{name}</mi>'
        return m.group(0)
    mm = re.sub(r'<mi>([a-zA-Z.]+)</mi>', _tag_func, mathml)
    return mm


def _fix_mathml_spacing(mathml: str) -> str:
    """在函数名 mi 之前插入薄空，解决 exarctan 粘连"""
    names = '|'.join(sorted(_FUNC_NAMES, key=len, reverse=True))
    mm = re.sub(
        rf'(</(?:msup|mi|msub|msqrt|mfrac|mover|munder|mtd|mth)>'
        rf'(?:\s*<mrow>)?)(\s*<mi(?:\s+mathvariant="normal")?>(?:{names}))',
        r'\1<mspace width="0.1667em"/>\2',
        mathml,
    )
    return mm


def _make_css() -> str:
    return """
@page { size: A4; margin: 2cm 2.2cm; }
html { color: #1a1a1a; background: #fff; }
body {
  font-family: 'LXGW WenKai', 'Noto Serif CJK SC', 'Noto Serif SC', serif;
  line-height: 1.75;
  font-size: 10.5pt;
  orphans: 2; widows: 2;
}
h1, h2, h3, h4 {
  font-family: 'Noto Sans SC', 'Source Han Sans CN', sans-serif;
  color: #1a1a2e;
  margin-top: 1.6em; margin-bottom: 0.5em;
  page-break-after: avoid;
}
h1 { font-size: 1.5em; border-bottom: 2px solid #eee; padding-bottom: 0.2em; }
h2 { font-size: 1.25em; border-bottom: 1px solid #eee; padding-bottom: 0.15em; }
h3 { font-size: 1.1em; }
p { margin: 0.4em 0; }
ul, ol { margin: 0.3em 0; padding-left: 1.8em; }
li { margin: 0.15em 0; }
img { max-width: 80%; height: auto; display: block; margin: 0.8em auto; border-radius: 3px; }
table { border-collapse: collapse; width: 100%; margin: 0.8em 0; font-size: 0.95em; }
td, th { border: 1px solid #ccc; padding: 4px 8px; }
th { background: #f5f5f5; }
code {
  background: #f5f5f5; padding: 1px 5px; border-radius: 3px;
  font-family: 'JetBrains Maple Mono', 'Fira Code', monospace; font-size: 0.88em;
}
pre {
  background: #f5f5f5; padding: 0.8em; border-radius: 4px;
  overflow-x: auto; border: 1px solid #e0e0e0; font-size: 0.9em;
}
blockquote {
  border-left: 4px solid #ddd; margin: 0.5em 0; padding: 0.3em 1em;
  color: #555; background: #fafafa;
}
math { font-size: 1.08em; }
.math.display { text-align: center; margin: 1em 0; overflow-x: auto; }
math[display="block"] { display: block; text-align: center; margin: 1em 0; overflow-x: auto; }

/* WeasyPrint MathML 下标/上标修正 */
msub > *:nth-child(2),
msubsup > *:nth-child(2) { vertical-align: sub; font-size: 0.72em; line-height: 1; }
msup > *:nth-child(2),
msubsup > *:nth-child(3) { vertical-align: super; font-size: 0.72em; line-height: 1; }
/* lim 的下标（munder 布局） */
munder > *:nth-child(2) { display: block; font-size: 0.7em; text-align: center; }
munder { display: inline-flex; flex-direction: column; align-items: center; vertical-align: middle; }

/* 函数名直体 + 微间距 */
mi[mathvariant="normal"] { font-style: normal; margin-left: 0.08em; }
@media print {
  body { font-size: 10pt; }
  img { max-width: 100%; }
  h2, h3 { page-break-after: avoid; }
}
"""


def convert(md_path: str, pdf_path: str | None = None) -> str:
    md_path = os.path.abspath(md_path)
    project_dir = os.path.dirname(md_path)
    if pdf_path is None:
        pdf_path = os.path.splitext(md_path)[0] + '.pdf'
    else:
        pdf_path = os.path.abspath(pdf_path)

    os.chdir(project_dir)
    md_text = open(md_path, encoding='utf-8').read()

    # === Step 1: 图片路径（相对 → 绝对，base64 不动） ===
    def _fix_img(m):
        alt, src = m.group(1), m.group(2)
        if src.startswith('data:'):
            return m.group(0)
        return f'![{alt}]({os.path.abspath(src)})'

    md_text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', _fix_img, md_text)

    # === Step 2: 行间公式 $$...$$ → MathML ===
    def _display_math(m):
        tex = m.group(1).strip()
        try:
            mm = tex2mathml(tex)
            mm = _fix_mathml_func_names(mm)
            mm = _fix_mathml_spacing(mm)
            return f'<div class="math display">{mm}</div>'
        except Exception:
            return f'<div class="math display">\\({tex}\\)</div>'

    md_text = re.sub(r'\$\$(.+?)\$\$', _display_math, md_text, flags=re.DOTALL)

    # === Step 3: 行内公式 $...$ → MathML ===
    def _inline_math(m):
        tex = m.group(1).strip()
        try:
            mm = tex2mathml(tex)
            mm = _fix_mathml_func_names(mm)
            mm = _fix_mathml_spacing(mm)
            return f'<span class="math inline">{mm}</span>'
        except Exception:
            return f'<span class="math inline">\\({tex}\\)</span>'

    md_text = re.sub(r'(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)', _inline_math, md_text)

    # === Step 4: marko 渲染 HTML ===
    html_body = Markdown().convert(md_text)

    # === Step 5: 组装 ===
    css = _make_css()
    html_full = f'''<!DOCTYPE html>
<html><head><meta charset="utf-8"/>
<title>{os.path.splitext(os.path.basename(md_path))[0]}</title>
<style>{css}</style></head><body>
{html_body}
</body></html>'''

    # === Step 6: weasyprint → PDF ===
    HTML(string=html_full, base_url=project_dir).write_pdf(pdf_path)

    size_kb = os.path.getsize(pdf_path) // 1024
    print(f"✅ {pdf_path}  ({size_kb}K)")
    return pdf_path


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    convert(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
