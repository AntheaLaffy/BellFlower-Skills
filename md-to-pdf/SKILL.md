---
name: md-to-pdf
description: >-
  Convert Markdown with LaTeX math, images (local/Base64), and tables
  into a polished PDF. Handles Chinese/Japanese text, formula rendering
  (subscripts, fractions, integrals, limits), and embedded graphics.
  Pure Python — no Pandoc or LaTeX engine required.
---

# Markdown → PDF Converter

Converts a Markdown file with `$...$` / `$$...$$` LaTeX math into a
typeset PDF using a pure Python pipeline:

```
input.md
  │
  ├── marko (Markdown → HTML)
  ├── latex2mathml (LaTeX → MathML)
  ├── WeasyPrint (HTML+MathML → PDF)
  └── output.pdf
```

## When To Use

- Convert course notes, lecture slides, or technical docs to PDF
- Documents with Chinese/Japanese text (uses system CJK fonts)
- Math-heavy content: formulas, integrals, limits, matrices
- Files with local images or Base64-embedded graphics
- You want a self-contained PDF without installing Pandoc or LaTeX

## Usage

```bash
# From the project directory where convert.py lives
uv run python3 md-to-pdf.py input.md [output.pdf]

# Or with the skill's script directly
uv run python3 /home/fuurin/.claude/skills/md-to-pdf/convert.py input.md output.pdf
```

## Requirements

The following Python packages must be installed in the project's virtual
environment (add them with `uv add <pkg>`):

| Package | Purpose |
|---------|---------|
| `weasyprint` | HTML+CSS+MathML → PDF rendering engine |
| `marko` | Markdown parser (GitHub-flavored) |
| `latex2mathml` | LaTeX expression → MathML conversion |

## What It Handles

| Feature | Status |
|---------|--------|
| `$...$` inline math | ✅ Rendered as MathML |
| `$$...$$` display math | ✅ Centered block |
| `\frac{a}{b}` fractions | ✅ |
| `x_0`, `x^2` sub/superscripts | ✅ CSS vertical-align fix |
| `\lim_{x\to0}` limits | ✅ munder → flex column layout |
| `\arctan`, `\sin` function names | ✅ Upright font with spacing |
| `\int`, `\sum` integrals/summations | ✅ |
| Local images `![](path.png)` | ✅ Embedded in PDF |
| Base64 images `![](data:...)` | ✅ Embedded in PDF |
| Tables | ✅ Rendered as HTML tables |
| Chinese/Japanese text | ✅ System CJK fonts |
| Code blocks | ✅ Syntax-highlighted via CSS |

## Notes

- The script uses WeasyPrint which does **not** execute JavaScript —
  all math rendering is done server-side via MathML. No browser needed.
- For best font rendering, install `noto-fonts-cjk` or `lxgw-wenkai-fonts`
  on Arch Linux.
- The output PDF embeds subsetted fonts, so it's self-contained but
  larger than a font-linked PDF (~300-400K for a typical lecture).
