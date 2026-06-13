#!/usr/bin/env python3
"""Markdown → PDF 转换器

默认引擎: weasyprint（纯 Python，MathML + CSS）
备用引擎: chromium（当检测到 `chromium` 可执行时，启用 Chromium
            headless 的原生 MathML 渲染，对 `bmatrix/pmatrix/vmatrix`
            等矩阵环境效果更好）

用法:
  单个文件:  uv run python3 convert.py input.md [output.pdf] [--font "Font Name"] [--engine weasyprint|chromium]
  批量:      uv run python3 convert.py input1.md input2.md ... [--font ...] [--engine ...]
  目录:      uv run python3 convert.py ./markdown_dir/ [--font ...] [--engine ...]
  Shell 通配: uv run python3 convert.py lectures/*.md [--font ...] [--engine ...]

依赖:
  默认 (weasyprint): uv add weasyprint marko latex2mathml
  备用 (chromium):   需要系统已安装 chromium (路径会自动探测)
                      Python 包: marko latex2mathml
"""

import sys, os, re, subprocess, shutil, tempfile
from pathlib import Path


# ── 可配置参数 ──────────────────────────────────────────
CHROMIUM_CANDIDATES = [
    "/usr/sbin/chromium",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
    "/usr/bin/google-chrome-stable",
    "/usr/bin/google-chrome",
]

# ── 基础工具 ────────────────────────────────────────────
def _importable(name: str) -> bool:
    import importlib.util
    return importlib.util.find_spec(name) is not None


def _find_chromium() -> str | None:
    """在常见位置查找 chromium 可执行文件，找不到返回 None"""
    for p in CHROMIUM_CANDIDATES:
        if os.path.isfile(p) and os.access(p, os.X_OK):
            return p
    # 再用 which 找一下
    w = shutil.which("chromium") or shutil.which("chromium-browser") or shutil.which("google-chrome")
    return w


# ── 依赖检查 ────────────────────────────────────────────
_REQUIRED = {
    'marko':       'marko',
    'latex2mathml':'latex2mathml',
}
_MISSING = [v for k, v in _REQUIRED.items() if not _importable(k)]
_HAS_WEASY = _importable('weasyprint')


def _check_deps(engine: str):
    if _MISSING:
        print("❌ 缺少依赖包:")
        for p in _MISSING:
            print(f"   • {p}")
        print()
        print("请运行以下命令安装:")
        print(f"   uv add {' '.join(_MISSING)}")
        if engine == "weasyprint" and "weasyprint" not in _MISSING and not _HAS_WEASY:
            print("   uv add weasyprint")
        print()
        sys.exit(1)
    if engine == "weasyprint" and not _HAS_WEASY:
        print("❌ weasyprint 未安装。请运行:  uv add weasyprint")
        print("   或者改用 --engine chromium（需要系统安装了 chromium）")
        sys.exit(1)
    if engine == "chromium" and _find_chromium() is None:
        print("❌ 未检测到 chromium。请先安装 chromium / google-chrome，")
        print("   或改用 --engine weasyprint。")
        sys.exit(1)


# ── 字体检测 ────────────────────────────────────────────
CJK_FONTS = [
    ('LXGW WenKai',        '霞鹜文楷（楷体/手写）'),
    ('Noto Serif CJK SC',  '思源宋体 / Noto Serif CJK SC（衬线/书籍）'),
    ('Noto Sans SC',       '思源黑体 / Noto Sans SC（无衬线/现代）'),
    ('serif',              '系统 serif 默认'),
    ('sans-serif',         '系统 sans-serif 默认'),
]


def _detect_available_fonts() -> list[tuple[str, str]]:
    available = []
    for family, label in CJK_FONTS:
        if family in ('serif', 'sans-serif'):
            available.append((family, label))
            continue
        try:
            ret = subprocess.run(
                ['fc-list', f':lang=zh:family={family}'],
                capture_output=True, text=True, timeout=5
            )
            if ret.returncode == 0 and ret.stdout.strip():
                available.append((family, label))
        except Exception:
            pass
    return available


# ── 共用 CSS ────────────────────────────────────────────
def _css(font_family: str, engine: str) -> str:
    """生成适配指定引擎的 CSS"""
    base = f"""
@page {{ size: A4; margin: 1.5cm 1.8cm; }}
html {{ color: #1a1a1a; background: #fff; }}
body {{
  font-family: '{font_family}', 'LXGW WenKai', '霞鹜文楷',
               'Noto Serif CJK SC', 'Noto Serif SC', 'Source Han Serif CN',
               'Source Han Sans CN', serif;
  line-height: 1.75;
  font-size: 10.5pt;
  orphans: 2; widows: 2;
  -webkit-font-smoothing: antialiased;
}}
h1, h2, h3, h4 {{
  font-family: '{font_family}', 'LXGW WenKai', '霞鹜文楷',
               'Noto Sans SC', 'Source Han Sans CN', sans-serif;
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
.math.display {{ display: block; text-align: center; margin: 1.2em 0; overflow-x: auto; }}
.math.inline {{ white-space: nowrap; }}
"""
    if engine == "weasyprint":
        # weasyprint 需要额外的 MathML 补丁 CSS
        base += """
math[display="block"] {{ display: block; text-align: center; margin: 1em 0; overflow-x: auto; }}
msub > *:nth-child(2), msubsup > *:nth-child(2) {{ vertical-align: sub; font-size: 0.72em; line-height: 1; }}
msup > *:nth-child(2), msubsup > *:nth-child(3) {{ vertical-align: super; font-size: 0.72em; line-height: 1; }}
munder > *:nth-child(2) {{ display: block; font-size: 0.7em; text-align: center; }}
munder {{ display: inline-flex; flex-direction: column; align-items: center; vertical-align: middle; }}
mi[mathvariant="normal"] {{ font-style: normal; margin-left: 0.08em; }}
"""
    base += """
@media print {{
  body {{ font-size: 10pt; }}
  img {{ max-width: 100%; }}
  h2, h3 {{ page-break-after: avoid; }}
}}
"""
    return base


# ── MathML 修正 ─────────────────────────────────────────
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
    def _tag(m):
        n = m.group(1)
        return f'<mi mathvariant="normal">{n}</mi>' if n in _FUNC_NAMES else m.group(0)
    return re.sub(r'<mi>([a-zA-Z.]+)</mi>', _tag, mm)


def _fix_mathml_spacing(mm: str) -> str:
    return re.sub(
        rf'{_CLOSE_TAG_RE}(\s*<mi(?:\s+mathvariant="normal")?>(?:{_FUNC_RE}))',
        r'\1<mspace width="0.1667em"/>\2', mm
    )


def _tex_to_mathml(tex: str) -> str:
    from latex2mathml.converter import convert as tex2mathml
    try:
        return _fix_mathml_spacing(_fix_mathml_func_names(tex2mathml(tex)))
    except Exception:
        return f"<span>({tex})</span>"


# ── Markdown → HTML（两引擎共用）────────────────────────
def md_to_html(md_path: str, font: str, engine: str) -> tuple[str, str]:
    """返回 (html, project_dir)"""
    project_dir = os.path.dirname(md_path)
    md_text = open(md_path, encoding='utf-8').read()

    # Step 1: 图片路径绝对化
    def _fix_img(m):
        alt, src = m.group(1), m.group(2)
        if src.startswith('data:'):
            return m.group(0)
        return f'![{alt}]({os.path.abspath(os.path.join(project_dir, src))})'
    md_text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', _fix_img, md_text)

    # Step 2: $$...$$ 显示公式
    def _display(m):
        tex = m.group(1).strip()
        mm = _tex_to_mathml(tex)
        return f'<div class="math display">{mm}</div>\n'
    md_text = re.sub(r'\$\$(.+?)\$\$', _display, md_text, flags=re.DOTALL)

    # Step 3: $...$ 行内公式
    def _inline(m):
        tex = m.group(1).strip()
        mm = _tex_to_mathml(tex)
        return f'<span class="math inline">{mm}</span>'
    md_text = re.sub(r'(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)', _inline, md_text)

    # Step 4: marko → HTML body
    from marko import Markdown
    html_body = Markdown().convert(md_text)

    title = os.path.splitext(os.path.basename(md_path))[0]
    html = (
        '<!DOCTYPE html><html><head><meta charset="utf-8"/>'
        f'<title>{title}</title>'
        f'<style>{_css(font, engine)}</style>'
        '</head><body>'
        + html_body
        + '</body></html>'
    )
    return html, project_dir


# ── 引擎 1: weasyprint ──────────────────────────────────
def render_weasyprint(html: str, project_dir: str, pdf_path: str):
    from weasyprint import HTML
    HTML(string=html, base_url=project_dir).write_pdf(pdf_path)


# ── 引擎 2: chromium headless ───────────────────────────
def render_chromium(html: str, pdf_path: str):
    chromium = _find_chromium()
    with tempfile.TemporaryDirectory() as tmp:
        html_file = os.path.join(tmp, "doc.html")
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html)
        pdf_tmp = os.path.join(tmp, "doc.pdf")
        cmd = [
            chromium,
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--hide-scrollbars",
            "--disable-background-networking",
            "--disable-extensions",
            "--disable-software-rasterizer",
            "--no-pdf-header-footer",
            "--print-to-pdf-no-header",
            f"--print-to-pdf={pdf_tmp}",
            f"file://{html_file}",
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if r.returncode != 0:
            print('   STDOUT:', r.stdout[:2000])
            print('   STDERR:', r.stderr[:2000])
            raise RuntimeError(f'chromium failed with code {r.returncode}')
        if not os.path.exists(pdf_tmp) or os.path.getsize(pdf_tmp) < 1000:
            raise RuntimeError('chromium produced no PDF')
        shutil.copyfile(pdf_tmp, pdf_path)


# ── 主流程 ──────────────────────────────────────────────
def convert(md_path: str, pdf_path: str | None = None,
            font: str | None = None, engine: str = "weasyprint") -> str:
    md_path = os.path.abspath(md_path)
    if pdf_path is None:
        pdf_path = os.path.splitext(md_path)[0] + '.pdf'
    else:
        pdf_path = os.path.abspath(pdf_path)

    # 确定字体
    if font is None:
        available = _detect_available_fonts()
        if any(f == 'LXGW WenKai' for f, _ in available):
            font = 'LXGW WenKai'
        else:
            font = 'Noto Serif CJK SC'

    html, project_dir = md_to_html(md_path, font, engine)

    if engine == "chromium":
        render_chromium(html, pdf_path)
    else:
        render_weasyprint(html, project_dir, pdf_path)

    size_kb = os.path.getsize(pdf_path) // 1024
    print(f"✅ {pdf_path}  ({size_kb}K)  |  字体: {font}  |  引擎: {engine}")
    return pdf_path


# ── 参数解析 ────────────────────────────────────────────
def _parse_args(argv: list[str]) -> tuple[list[str], str | None, str]:
    font = None
    engine = "weasyprint"

    def _pick(name: str, i: int, lst: list[str]) -> str | None:
        return lst[i + 1] if i + 1 < len(lst) else None

    # --font
    if '--font' in argv:
        i = argv.index('--font')
        font = _pick('--font', i, argv)
        argv = argv[:i] + (argv[i + 2:] if font else argv[i + 1:])

    # --engine
    if '--engine' in argv:
        i = argv.index('--engine')
        engine = _pick('--engine', i, argv) or "weasyprint"
        argv = argv[:i] + (argv[i + 2:] if engine else argv[i + 1:])

    if engine not in ("weasyprint", "chromium"):
        print(f"❌ 未知引擎: {engine}（可选: weasyprint / chromium）")
        sys.exit(1)

    inputs: list[str] = []
    for a in argv:
        a = os.path.expanduser(a)
        if os.path.isdir(a):
            inputs.extend(os.path.join(a, f) for f in sorted(os.listdir(a)) if f.endswith('.md'))
        elif os.path.isfile(a):
            inputs.append(a)
        else:
            print(f"⚠️ 跳过（不存在）: {a}")
    return inputs, font, engine


if __name__ == '__main__':
    inputs, font, engine = _parse_args(sys.argv[1:])
    if not inputs:
        print(__doc__)
        sys.exit(1)
    _check_deps(engine)

    results = []
    for i, md in enumerate(inputs, 1):
        print(f"[{i}/{len(inputs)}] {md}")
        try:
            pdf = convert(md, None, font, engine)
            results.append((md, pdf, None))
        except Exception as e:
            results.append((md, None, str(e)))
            print(f"   ❌ {e}")

    ok = sum(1 for _, _, err in results if err is None)
    fail = sum(1 for _, _, err in results if err is not None)
    print(f"\n完成: {ok} 成功, {fail} 失败  (共 {len(results)} 个文件)  |  引擎: {engine}")
