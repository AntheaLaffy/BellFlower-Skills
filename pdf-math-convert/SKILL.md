---
name: pdf-math-convert
description: >-
  Convert math-heavy PDFs (lecture notes, textbooks, papers, problem sets)
  into clean Markdown with proper LaTeX math. Use this skill whenever the
  user asks to convert a PDF containing mathematics to Markdown, extract
  formulas to LaTeX, make PDF course materials searchable/editable, or
  batch-process math PDFs for use in note-taking or LLM applications.
---

# PDF to LaTeX Markdown Converter

Converts a math-heavy PDF into clean Markdown with proper `$...$` inline
and `$$...$$` display LaTeX math, preserving images as base64 data URIs.

## Pipeline Overview

```
PDF ──[docling]──> raw.md   ──[cleanup.py]──> clean.md   ──[LLM repair]──> final.md
     extraction       (images +               (generic OCR      (formula inference,
                      formula-not-decoded)     + spacing fixes)   LaTeX wrapping)
```

## Phase 1: Extraction (docling)

### Setup (one-time per project)

Check whether the project directory already has a `pyproject.toml` with
`docling` as a dependency and a `.venv` from `uv sync`.

**If not:** add docling to the project's dependencies and sync.

```bash
# If project has no pyproject.toml at all, create one:
cat > pyproject.toml << 'EOF'
[project]
name = "my-project"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "docling>=2.0",
    "pypdfium2",
    "docling-parse",
    "lxml",
    "beautifulsoup4",
    "pylatexenc",
    "marko",
]
EOF

uv sync  # creates .venv, resolves all deps and optional backends
```

**If the project already has a `pyproject.toml`:** add `docling` and the
backend deps to `dependencies`, then re-run `uv sync`.

**If the project uses `requirements.txt` or another non-uv format:**
convert it to `pyproject.toml` + `uv sync` first.

### Run

```bash
uv run docling "<input.pdf>" --from pdf --to md --output .
```

This produces `<input>.md` (same stem as the PDF). Rename it to `<input>_raw.md`.

**First run note:** docling downloads OCR models (~40 MB) automatically.

**Edge cases:**
- If `uv run docling` fails with a missing module, re-run `uv sync` to
  ensure all optional backends are installed.
- For very large PDFs (>50 pages), docling may be slow. Consider splitting
  the PDF first with `pdfseparate`.

## Phase 2: Generic Cleanup (cleanup.py)

Run the bundled cleanup script to fix OCR artifacts that are independent
of the specific math content:

```bash
python3 ~/.claude/skills/pdf-math-convert/cleanup.py <input>_raw.md
```
If you prefer to use the project venv: `uv run python3 ~/.claude/skills/pdf-math-convert/cleanup.py <input>_raw.md`.

This produces `<input>_clean.md` and fixes:
- Ligature breaks: `fi rst` → `first`, `fi nd` → `find`
- Unicode replacement characters (�)
- Number spacing artifacts: `0 . 75` → `0.75`, `-0 . 5` → `-0.5`
- Greek letter wrapping: `∆`/`Δ` → `$\Delta$` in context
- Basic function notation: `f ( x )` → `$f(x)$` (context-aware)
- Broken docling tables (malformed multi-column rows)
- Double spaces and excess blank lines

The script is **domain-agnostic** — it knows no calculus, only typographic
patterns common to docling's OCR output.

## Phase 3: LLM Semantic Repair

**This is the critical phase.** Read `*_clean.md` and fix it in-place.

### Step 3a: Survey the damage

Count and locate all issues:
```bash
grep -n 'formula-not-decoded\|f �\|f �' *_clean.md
```

### Step 3b: Fix `<!-- formula-not-decoded -->` placeholders

For **each** placeholder, read the ~3 lines of English text **immediately
before** the placeholder. The text describes the formula in words. Use your
knowledge of mathematics to write the correct LaTeX.

**Example — the context tells you everything:**

> Context: *"the slope of the tangent line is the limit of the slopes of
> the secant lines. In other words,"*
>
> `<!-- formula-not-decoded -->`
>
> → Write: `$$m = \lim_{Q \to P} \frac{\Delta f}{\Delta x} = \lim_{\Delta x \to 0} \frac{\Delta f}{\Delta x}$$`

> Context: *"We can now write the following formula for the derivative:"*
>
> `<!-- formula-not-decoded -->`
>
> → Write: `$$f'(x_0) = \lim_{\Delta x \to 0} \frac{f(x_0 + \Delta x) - f(x_0)}{\Delta x}$$`

> Context: *"when x = -0.75 and Δx has each of the following values:"*
>
> `<!-- formula-not-decoded -->`
>
> → Write: `$$\Delta x = -0.5,\ -0.25,\ 0.25,\ 0.5$$`

If a context is **genuinely ambiguous** (rare — most math textbooks state
the formula in words before showing it), flag it with a comment:
`<!-- UNCERTAIN: could not infer formula -->` and move on.

### Step 3c: Fix remaining OCR/Unicode issues

After clearing all placeholders, scan for and fix:

| Pattern | Fix |
|---------|-----|
| `f � ( x₀ )` (Unicode replacement char) | `$f'(x_0)$` |
| `f ( x ) = ...` (math in plain text) | `$f(x) = ...$` |
| `y - y0 = m ( x - x0 )` | `$y - y_0 = m(x - x_0)$` |
| `P = ( x0 , f ( x0 ))` | `$P = (x_0, f(x_0))$` |
| `e x · arctan( x )` | `$e^x \arctan(x)$` |
| `0.5 x 3 - x` | `$0.5x^3 - x$` |
| `-0.08 ≤ Δx ≤ 0.10` | `$-0.08 \leq \Delta x \leq 0.10$` |
| `as Q → P` (in prose) | `as $Q \to P$` |

### Step 3d: Clean up partial math-mode

docling sometimes produces output like `( $x_0$ , f ( $x_0$ ))` where
adjacent math-mode spans should be a single span. Merge them:
- `( $x_0$ , f ( $x_0$ ))` → `$(x_0, f(x_0))$`
- `P = ( $x_0$ , $y_0$ )` → `$P = (x_0, y_0)$`

### Step 3e: Verify

After editing, run:
```bash
grep -c 'formula-not-decoded' <file>   # must be 0
```

Check that `$` signs are balanced:
- Count of `$$` should be even
- Each `$...$` should not span a paragraph boundary
- No unescaped `$` in prose (e.g., monetary amounts — rare in math texts)

## Phase 4: Rename and Report

Rename the final file to `<input>_enhanced.md` and report:
- How many `<!-- formula-not-decoded -->` were replaced
- How many display formulas (`$$...$$`) were added
- How many inline formulas (`$...$`) were normalized
- Any remaining issues or uncertainties

## Batch Processing

When the user asks to convert multiple PDFs:
1. Process them sequentially (docling is CPU-heavy and may OOM if parallelized)
2. Use the same cleanup.py + LLM repair for each
3. Keep a summary table of results per file

## Fallbacks

If docling fails entirely (rare), try `markitdown` as a lighter alternative:
```bash
uvx markitdown <input.pdf> > <input>_raw.md
```
markitdown preserves text but has no math awareness — the LLM repair phase
becomes more critical and more manual.

If images are not needed, use `pymupdf4llm`:
```bash
uvx --with pymupdf4llm python3 -c "
import pymupdf4llm
md = pymupdf4llm.to_markdown(doc='<input.pdf>')
with open('<output>.md', 'w') as f: f.write(md)
"
```
