---
name: md-to-pdf
description: >-
  Convert Markdown with LaTeX math, images, and tables into a polished PDF.
  Two rendering engines: (1) weasyprint — pure Python, no browser needed;
  (2) chromium — best for matrices/bmatrix/pmatrix/vmatrix and complex formulas.
  Supports Chinese/Japanese fonts. Can chain after ocr-md-polish for a
  complete OCR→clean→PDF workflow.
---

# Markdown → PDF Converter

Converts a Markdown file with `$...$` / `$$...$$` LaTeX into a typeset PDF.

**Two engines:**

| Engine | When to use | Notes |
|--------|-------------|-------|
| `weasyprint` (default) | Most documents, pure Python, no browser needed | MathML + CSS. May flatten matrices like `bmatrix` on some versions. |
| `chromium` | Complex formulas (`bmatrix`, `pmatrix`, `vmatrix`, `vmatrix`, `det`, nested fractions, …) | Requires system `chromium` / `google-chrome` to be installed. Uses native MathML rendering. |

## Quick Start

```bash
# 默认引擎 weasyprint
uv run python3 /home/fuurin/.claude/skills/md-to-pdf/convert.py input.md --font "LXGW WenKai"

# 矩阵/复杂公式 —— 用 chromium（需系统已装 chromium）
uv run python3 /home/fuurin/.claude/skills/md-to-pdf/convert.py input.md --font "LXGW WenKai" --engine chromium
```

## Pipeline

```
[PDF] → pdf-math-convert → [raw .md] → ocr-md-polish → [clean .md] → md-to-pdf → [polished PDF]
```

## Usage

### 1. Dependencies

```bash
# 默认引擎（最小方案）
uv add weasyprint marko latex2mathml

# chromium 引擎（需系统已安装 chromium/google-chrome）
uv add marko latex2mathml
```

### 2. Font preference

| Name | CSS family | Style |
|------|-----------|-------|
| 霞鹜文楷 | `LXGW WenKai` | 楷体/手写 |
| 思源宋体 | `Noto Serif CJK SC` | 衬线/书籍 |
| 思源黑体 | `Noto Sans SC` | 无衬线/现代 |

The converter auto-detects installed fonts; `LXGW WenKai` is preferred
when present, otherwise `Noto Serif CJK SC`.

### 3. Convert

**Single file:**
```bash
uv run python3 /home/fuurin/.claude/skills/md-to-pdf/convert.py input.md [output.pdf] [--font "LXGW WenKai"] [--engine weasyprint|chromium]
```

**Batch:**
```bash
uv run python3 /home/fuurin/.claude/skills/md-to-pdf/convert.py note1.md note2.md --font "LXGW WenKai" --engine chromium
```

**Directory / glob:**
```bash
uv run python3 /home/fuurin/.claude/skills/md-to-pdf/convert.py ./lectures/ --engine chromium
uv run python3 /home/fuurin/.claude/skills/md-to-pdf/convert.py chapter*.md --engine chromium
```

### 4. When to pick `--engine chromium`

Use `--engine chromium` when your Markdown contains any of these,
because weasyprint's MathML is limited for them:

- Matrix environments: `\begin{bmatrix}…\end{bmatrix}`, `\begin{pmatrix}…`,
  `\begin{vmatrix}…`, `\begin{matrix}…`
- Determinants `\det`, column vectors, multi-line equations
- Nested `\frac`, `\lim`, `\sum` with sub/super-scripts

The script auto-looks for `chromium` / `google-chrome` in
`/usr/sbin`, `/usr/bin`, and `PATH`. If none is found it exits with a
clear message.

## Features

| Feature | Status |
|---------|--------|
| `$...$` inline math | ✅ MathML rendering |
| `$$...$$` display math | ✅ Centered block |
| `\frac{a}{b}` fractions | ✅ |
| `x_0`, `x^2` sub/superscripts | ✅ |
| `\lim`, `\int`, `\sum` | ✅ |
| `\begin{bmatrix}…`, `\begin{pmatrix}…` | ✅ (best with `--engine chromium`) |
| Local images, base64 images | ✅ |
| Tables | ✅ |
| Chinese / CJK text | ✅ with `--font` |
| Code blocks | ✅ styled CSS |
| Header/footer-free PDF | ✅ chromium: `--no-pdf-header-footer` |

## Integration with ocr-md-polish

This skill is designed to be the final step after OCR cleanup:

1. **ocr-md-polish** fixes formula broken subscripts (`x0` → `x_0`),
   nested dollar signs, OCR-duplicated image text, and numbering
2. **md-to-pdf** takes the polished Markdown and produces the final PDF

If input file is a `.pdf`, suggest using `pdf-math-convert` first
to get Markdown, then follow with `ocr-md-polish` → `md-to-pdf`.
