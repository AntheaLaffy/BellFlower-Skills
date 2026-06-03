#!/usr/bin/env python3
"""Markdown → PDF 转换器（纯Python）

用法:
  单个文件:  uv run python3 convert.py input.md [output.pdf] [--font "Font Name"]
  批量:      uv run python3 convert.py input1.md input2.md ... [--font "Font Name"]
  目录:      uv run python3 convert.py ./markdown_dir/ [--font "Font Name"]
  Shell 通配: uv run python3 convert.py lectures/*.md [--font "Font Name"]

依赖（需在项目 venv 中安装）:
  uv add weasyprint marko latex2mathml

功能:
  - 行内/行间 LaTeX 公式 ($...$ / $$...$$) → MathML 渲染
  - 本地图片 / Base64 图片嵌入
  - 中文字体可选用系统安装的任意字体
  - 表格、代码块、引用完整支持
  - 批量：多个文件或一个目录，自动转换所有 .md
"""

import sys, os, re, subprocess


def _importable(name: str) -> bool:
    import importlib.util
    return importlib.util.find_spec(name) is not None


# ── 依赖检查 ──────────────────────────────────────────────
_REQUIRED = {
    'weasyprint':  'weasyprint',
    'marko':       'marko',
    'latex2mathml':'latex2mathml',
}
_MISSING = [v for k, v in _REQUIRED.items() if not _importable(k)]


def _check_deps():
    if not _MISSING:
        return
    print("❌ 缺少依赖包:")
    for p in _MISSING:
        print(f"   • {p}")
    print()
    print("请运行以下命令安装:")
    print(f"   uv add {' '.join(_MISSING)}")
    print()
    sys.exit(1)


# ── 可用字体检测 ──────────────────────────────────────────
CJK_FONTS = [
    ('LXGW WenKai',        '霞鹜文楷（楷体/手写）'),
    ('Noto Serif CJK SC',  '思源宋体 / Noto Serif CJK SC（衬线/书籍）'),
    ('Noto Sans SC',       '思源黑体 / Noto Sans SC（无衬线/现代）'),
    ('serif',              '系统 serif 默认'),
    ('sans-serif',         '系统 sans-serif 默认'),
]


def _detect_available_fonts() -> list[tuple[str, str]]:
    """只返回系统上实际安装的字体"""
    available = []
    for family, label in CJK_FONTS:
        if family in ('serif', 'sans-serif'):
            available.append((family, label))  # fallback always available
            continue
        ret = subprocess.run(
            ['fc-list', f':lang=zh:family={family}'],
            capture_output=True, text=True, timeout=5
        )
        if ret.returncode == 0 and ret.stdout.strip():
            available.append((family, label))
    return available


def _css(font_family: str) -> str:
    """生成完整的 CSS 样式"""
    return f"""
@page {{ size: A4; margin: 1.5cm 1.8cm; }}
html {{ color: #1a1a1a; background: #fff; }}
body {{
  font-family: '{font_family}', 'Noto Serif CJK SC', 'Noto Serif SC', serif;
  line-height: 1.75;
  font-size: 10.5pt;
  orphans: 2; widows: 2;
}}
h1, h2, h3, h4 {{
  font-family: 'Noto Sans SC', 'Source Han Sans CN', sans-serif;
  color: #1a1a2e;
  margin-top: 1.6em; margin-bottom: 0.5em;
  page-break-after: avoid;
}}
h1 {{ font-size: 1.5em; border-bottom: 2px solid #eee; padding-bottom: 0.2em; }}
h2 {{ font-size: 1.25em; border-bottom: 1px solid #eee; padding-bottom: 0.15em; }}
h3 {{ font-size: 1.1em; }}
p {{ margin: 0.4em 0; }}
ul, ol {{ margin: 0.3em 0; padding-left: 1.8em; }}
li {{ margin: 0.15em 0; }}
img {{ max-width: 80%; height: auto; display: block; margin: 0.8em auto; border-radius: 3px; }}
table {{ border-collapse: collapse; width: 100%; margin: 0.8em 0; font-size: 0.95em; }}
td, th {{ border: 1px solid #ccc; padding: 4px 8px; }}
th {{ background: #f5f5f5; }}
code {{
  background: #f5f5f5; padding: 1px 5px; border-radius: 3px;
  font-family: 'JetBrains Maple Mono', 'Fira Code', monospace; font-size: 0.88em;
}}
pre {{
  background: #f5f5f5; padding: 0.8em; border-radius: 4px;
  overflow-x: auto; border: 1px solid #e0e0e0; font-size: 0.9em;
}}
blockquote {{
  border-left: 4px solid #ddd; margin: 0.5em 0; padding: 0.3em 1em;
  color: #555; background: #fafafa;
}}
math {{ font-size: 1.08em; }}
.math.display {{ text-align: center; margin: 1em 0; overflow-x: auto; }}
math[display="block"] {{ display: block; text-align: center; margin: 1em 0; overflow-x: auto; }}
msub > *:nth-child(2), msubsup > *:nth-child(2) {{ vertical-align: sub; font-size: 0.72em; line-height: 1; }}
msup > *:nth-child(2), msubsup > *:nth-child(3) {{ vertical-align: super; font-size: 0.72em; line-height: 1; }}
munder > *:nth-child(2) {{ display: block; font-size: 0.7em; text-align: center; }}
munder {{ display: inline-flex; flex-direction: column; align-items: center; vertical-align: middle; }}
mi[mathvariant="normal"] {{ font-style: normal; margin-left: 0.08em; }}
@media print {{
  body {{ font-size: 10pt; }}
  img {{ max-width: 100%; }}
  h2, h3 {{ page-break-after: avoid; }}
}}
"""


# ── MathML 修正 ───────────────────────────────────────────
_FUNC_NAMES = {
    'sin','cos','tan','cot','sec','csc',
    'arcsin','arccos','arctan','arccot','arcsec','arccsc',
    'sinh','cosh','tanh','coth','sech','csch',
    'exp','log','ln','lg',
    'lim','limsup','liminf',
    'max','min','sup','inf',
    'det','dim','ker','hom','Pr','gcd','deg','arg','Re','Im',
}

_FUNC_RE = '|'.join(sorted(_FUNC_NAMES, key=len, reverse=True))
_CLOSE_TAG_RE = r'(</(?:msup|mi|msub|msqrt|mfrac|mover|munder|mtd|mth)>(?:\s*<mrow>)?)'


def _fix_mathml_func_names(mm: str) -> str:
    """给已知函数名加上 mathvariant="normal" """
    def _tag(m):
        n = m.group(1)
        return f'<mi mathvariant="normal">{n}</mi>' if n in _FUNC_NAMES else m.group(0)
    return re.sub(r'<mi>([a-zA-Z.]+)</mi>', _tag, mm)


def _fix_mathml_spacing(mm: str) -> str:
    """函数名前插入薄空"""
    return re.sub(
        rf'{_CLOSE_TAG_RE}(\s*<mi(?:\s+mathvariant="normal")?>(?:{_FUNC_RE}))',
        r'\1<mspace width="0.1667em"/>\2', mm
    )


# ── 主流程 ────────────────────────────────────────────────
def convert(md_path: str, pdf_path: str | None = None, font: str | None = None) -> str:
    md_path = os.path.abspath(md_path)
    project_dir = os.path.dirname(md_path)
    if pdf_path is None:
        pdf_path = os.path.splitext(md_path)[0] + '.pdf'
    else:
        pdf_path = os.path.abspath(pdf_path)

    # 确定字体
    if font is None:
        available = _detect_available_fonts()
        font = 'LXGW WenKai' if any(f == 'LXGW WenKai' for f, _ in available) else 'Noto Serif CJK SC'

    os.chdir(project_dir)
    md_text = open(md_path, encoding='utf-8').read()

    # Step 1: 图片路径 → 绝对
    def _fix_img(m):
        alt, src = m.group(1), m.group(2)
        if src.startswith('data:'):
            return m.group(0)
        return f'![{alt}]({os.path.abspath(src)})'
    md_text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', _fix_img, md_text)

    # Step 2: $$...$$ 显示公式
    from latex2mathml.converter import convert as tex2mathml

    def _display(m):
        tex = m.group(1).strip()
        try:
            mm = _fix_mathml_spacing(_fix_mathml_func_names(tex2mathml(tex)))
            return f'<div class="math display">{mm}</div>'
        except Exception:
            return f'<div class="math display">\\({tex}\\)</div>'
    md_text = re.sub(r'\$\$(.+?)\$\$', _display, md_text, flags=re.DOTALL)

    # Step 3: $...$ 行内公式
    def _inline(m):
        tex = m.group(1).strip()
        try:
            mm = _fix_mathml_spacing(_fix_mathml_func_names(tex2mathml(tex)))
            return f'<span class="math inline">{mm}</span>'
        except Exception:
            return f'<span class="math inline">\\({tex}\\)</span>'
    md_text = re.sub(r'(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)', _inline, md_text)

    # Step 4: marko → HTML
    from marko import Markdown
    html_body = Markdown().convert(md_text)

    # Step 5: 组装
    html = f'''<!DOCTYPE html>
<html><head><meta charset="utf-8"/>
<title>{os.path.splitext(os.path.basename(md_path))[0]}</title>
<style>{_css(font)}</style></head><body>
{html_body}
</body></html>'''

    # Step 6: weasyprint → PDF
    from weasyprint import HTML
    HTML(string=html, base_url=project_dir).write_pdf(pdf_path)

    size_kb = os.path.getsize(pdf_path) // 1024
    print(f"✅ {pdf_path}  ({size_kb}K)  |  字体: {font}")
    return pdf_path


def _parse_args(argv: list[str]) -> tuple[list[str], str | None]:
    """解析 --font 参数，返回 (文件列表, 字体名)"""
    font = None
    if '--font' in argv:
        i = argv.index('--font')
        font = argv[i + 1] if i + 1 < len(argv) else None
        argv = argv[:i] + argv[i + 2:] if font else argv[:i] + argv[i + 1:]

    # 收集所有输入路径
    inputs: list[str] = []
    for a in argv:
        a = os.path.expanduser(a)
        if os.path.isdir(a):
            # 目录 → 扫所有 .md
            inputs.extend(os.path.join(a, f) for f in sorted(os.listdir(a)) if f.endswith('.md'))
        elif os.path.isfile(a):
            inputs.append(a)
        else:
            print(f"⚠️ 跳过（不存在）: {a}")
    return inputs, font


if __name__ == '__main__':
    _check_deps()

    inputs, font = _parse_args(sys.argv[1:])
    if not inputs:
        print(__doc__)
        sys.exit(1)

    results = []
    for i, md in enumerate(inputs, 1):
        print(f"[{i}/{len(inputs)}] {md}")
        try:
            pdf = convert(md, None, font)
            results.append((md, pdf, None))
        except Exception as e:
            results.append((md, None, str(e)))
            print(f"   ❌ {e}")

    ok = sum(1 for _, _, err in results if err is None)
    fail = sum(1 for _, _, err in results if err is not None)
    print(f"\n完成: {ok} 成功, {fail} 失败  (共 {len(results)} 个文件)")
