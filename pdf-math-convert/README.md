# pdf-math-convert

Convert math-heavy PDFs into clean Markdown with proper LaTeX math.

## Quick Start

```bash
# In your project directory, add docling deps if not already present:
cat >> pyproject.toml << 'EOF'
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

uv sync                                    # create .venv, install everything
uv run docling my_lecture.pdf --from pdf --to md --output .
mv my_lecture.md my_lecture_raw.md
python3 ~/.claude/skills/pdf-math-convert/cleanup.py my_lecture_raw.md
# Then have Claude (or another LLM) fix the remaining formula-not-decoded slots
```

## Pipeline

```
lecture.pdf
  │
  ├──[uv run docling]───> lecture_raw.md     (images preserved, formulas as placeholders)
  │
  ├──[cleanup.py]─────────> lecture_clean.md  (OCR/spacing fixes)
  │
  └──[LLM repair]────────> lecture_final.md   (LaTeX formulas reconstructed)
```

## Dependency Management

Dependencies live in the **project's** `pyproject.toml` and are managed by `uv sync`.

- `uv sync` creates a project-local `.venv/` with all runtime backends pre-installed
- `uv run docling` runs docling from the project venv — no global tool install needed
- When the project moves to another machine, `uv sync` reproduces the exact same environment
- If the project already uses a different venv tool, convert to `uv` first

## Tools

| Tool | Phase | How to run |
|------|-------|------------|
| `docling` | Extraction | `uv run docling in.pdf --from pdf --to md --output .` |
| `cleanup.py` | Cleanup | `python3 ~/.claude/skills/pdf-math-convert/cleanup.py in_raw.md` |
| Claude / LLM | Repair | Semantic formula reconstruction (described in SKILL.md Phase 3) |

## What cleanup.py Does

The script applies domain-agnostic fixes:
- Ligature restoration (`fi rst` → `first`)
- Number spacing repair (`0 . 75` → `0.75`)
- Delta symbol wrapping (`∆` → `$\Delta$`)
- Basic function notation (`f ( x )` → `$f(x)$`)
- Broken docling table removal
- Whitespace normalization

## What the LLM Does

- Reads `<!-- formula-not-decoded -->` placeholders and infers LaTeX from English context
- Fixes OCR corruption: `f � (x₀)` → `$f'(x_0)$`, `e x · arctan( x )` → `$e^x \arctan(x)$`
- Merges partial math-mode spans: `( $x_0$ , f ( $x_0$ ))` → `$(x_0, f(x_0))$`
- Balances all `$` delimiters

## Limitations

- **Works best with:** LaTeX-generated PDFs (lecture notes, textbooks, papers)
- **Struggles with:** Scanned PDFs, handwritten formulas, unusual notation
- **Image size:** Docling embeds images as base64 PNG → output files can be large
- **OCR quality:** Varies with PDF quality; LLM repair compensates for typical errors
