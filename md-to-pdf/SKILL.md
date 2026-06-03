---
name: md-to-pdf
description: >-
  Convert Markdown with LaTeX math, images, and tables into a polished PDF.
  Pure Python pipeline — no Pandoc or LaTeX needed. Supports Chinese/Japanese
  fonts, formula rendering, local & Base64 images. Can chain after
  ocr-md-polish for a complete OCR→clean→PDF workflow.
---

# Markdown → PDF Converter

Converts a Markdown file with `$...$` / `$$...$$` LaTeX into a typeset PDF.
Pure Python — no Pandoc, no LaTeX engine, no browser required.

## Pipeline

```
[PDF] → ocr-md-polish → [clean .md] → md-to-pdf → [polished PDF]
```

## When To Use

- Convert course notes, lecture slides, technical docs to PDF
- Documents with CJK text (Chinese, Japanese, Korean)
- Math-heavy content: formulas, integrals, limits, matrices
- Files with local images or Base64-embedded graphics
- After `ocr-md-polish` to get a polished PDF from OCR'd content

## Usage Flow

### 1. Dependencies (one-time)

The converter needs these Python packages in your project's venv:

```bash
uv add weasyprint marko latex2mathml
```

### 2. Font preference

The converter supports these CJK fonts (system-installed):

| Name | CSS family | Style |
|------|-----------|-------|
| 霞鹜文楷 | `LXGW WenKai` | 楷体/手写 |
| 思源宋体 | `Noto Serif CJK SC` | 衬线/书籍 |
| 思源黑体 | `Noto Sans SC` | 无衬线/现代 |
| 系统默认 | `serif` / `sans-serif` | 由系统决定 |

The skill will ask you which font to use before generating.

### 3. Convert

**单个文件:**
```bash
uv run python3 /home/fuurin/.claude/skills/md-to-pdf/convert.py input.md [output.pdf] [--font "Font Name"]
```

**批量（多个文件）:**
```bash
uv run python3 /home/fuurin/.claude/skills/md-to-pdf/convert.py note1.md note2.md note3.md --font "LXGW WenKai"
```

**批量（整个目录）:**
```bash
uv run python3 /home/fuurin/.claude/skills/md-to-pdf/convert.py ./lectures/ --font "Noto Serif CJK SC"
```

**Shell 通配符:**
```bash
uv run python3 /home/fuurin/.claude/skills/md-to-pdf/convert.py chapter*.md --font "LXGW WenKai"
```

批量转换会逐个显示进度：`[1/5]`, `[2/5]` … 最后输出汇总 `N 成功, M 失败`。

## What It Handles

| Feature | Status |
|---------|--------|
| `$...$` inline math | ✅ MathML rendering |
| `$$...$$` display math | ✅ Centered block |
| `\frac{a}{b}` fractions | ✅ |
| `x_0`, `x^2` sub/superscripts | ✅ CSS vertical-align fix |
| `\lim_{x\to0}` limits | ✅ |
| `\arctan`, `\sin` function names | ✅ Upright + spacing |
| `\int`, `\sum` integrals/summations | ✅ |
| Local images | ✅ Embedded in PDF |
| Base64 images | ✅ Embedded in PDF |
| Tables | ✅ HTML tables |
| CJK text | ✅ User's chosen system font |
| Code blocks | ✅ Styled via CSS |

## Integration with ocr-md-polish

This skill is designed to be the **final step** after OCR cleanup:

1. **ocr-md-polish** fixes formula broken subscripts (`x0` → `x_0`),
   nested dollar signs, OCR-duplicated image text, and numbering
2. **md-to-pdf** takes the polished Markdown and produces the final PDF

If input file is a `.pdf`, suggest using `pdf-math-convert` first
to get Markdown, then follow with `ocr-md-polish` → `md-to-pdf`.
