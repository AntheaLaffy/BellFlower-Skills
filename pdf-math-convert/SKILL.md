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
and `$$...$$` display LaTeX math, preserving images.

Images can be handled in two modes:
- **Embedded** (default): images kept as base64 data URIs — single file, no external deps
- **Referenced**: images extracted to an `images/` folder, md uses relative links — smaller md, easier to browse

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

### Step 3a: Image mode

**Ask the user:** *"Keep images embedded (single file, self-contained) or extract to an `images/` folder (smaller md, easier to browse)?"*

Default to **embedded** (no extraction). If the user chooses referenced mode:

1. Create an `images/` directory next to the markdown file
2. Scan the markdown for `![](data:image/png;base64,...)` data URIs
3. For each image, decode the base64, write to `images/img_001.png` (or descriptive name), replace the data URI with a relative path `![](images/img_001.png)`
4. Record the filename stem for the report (e.g., `Ses1` → `images/Ses1_*.png`)

### Step 3b: Survey the damage

Count and locate all issues:
```bash
grep -n 'formula-not-decoded\|f �\|f �' *_clean.md
```

### Step 3c: Fix `<!-- formula-not-decoded -->` placeholders

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

### Step 3d: Fix remaining OCR/Unicode issues

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

### Step 3e: Clean up partial math-mode

docling sometimes produces output like `( $x_0$ , f ( $x_0$ ))` where
adjacent math-mode spans should be a single span. Merge them:
- `( $x_0$ , f ( $x_0$ ))` → `$(x_0, f(x_0))$`
- `P = ( $x_0$ , $y_0$ )` → `$P = (x_0, y_0)$`

### Step 3f: Verify

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
- Image mode used (embedded or referenced)
- How many images were processed (and extracted, if referenced mode)
- How many `<!-- formula-not-decoded -->` were replaced
- How many display formulas (`$$...$$`) were added
- How many inline formulas (`$...$`) were normalized
- Any remaining issues or uncertainties

### Step 4: Clean Up Intermediate Files

After the report, **ask the user:** *"Delete intermediate files (`*_raw.md` and `*_clean.md`)?"*

Default to **keep** (no deletion). If the user says yes, remove them:

```bash
rm <input>_raw.md <input>_clean.md
```

## Batch Processing (Multiple PDFs)

When the user asks to convert **more than one** PDF, follow this orchestrated
workflow. The main agent handles the deterministic phases (extraction +
cleanup), then spawns sub-agents for the LLM repair to avoid context explosion.

### Batch Phase 1: Extract All PDFs

Loop over all input PDFs **sequentially** (docling is CPU-heavy):

```bash
for pdf in *.pdf; do
    echo "=== $pdf ==="
    uv run docling "$pdf" --from pdf --to md --output .
    mv "${pdf%.pdf}.md" "${pdf%.pdf}_raw.md"
done
```

Track successes and failures in a list.

### Batch Phase 2: Cleanup All Raw Files

Loop over all `*_raw.md` files:

```bash
for f in *_raw.md; do
    uv run python3 ~/.claude/skills/pdf-math-convert/cleanup.py "$f"
done
```

### Batch Phase 3: Ask Image Mode Once

**Ask the user once:** *"Keep images embedded for all files, or extract to `images/` folders?"*

Default to **embedded**. If referenced mode is chosen, note it — sub-agents will
handle the extraction per file (each sub-agent extracts images for its own files).

### Batch Phase 4: Survey and Plan Sub-Agent Allocation

**Do NOT read any `*_clean.md` files yourself.** Your job is to survey complexity
and allocate work to sub-agents.

Collect metrics **without reading the content** (single awk command, no multi-prompt):

```bash
awk 'FNR==1{printf "%s: ", FILENAME} ENDFILE{printf "%d lines, ", NR} /formula-not-decoded/{p++} ENDFILE{printf "%d placeholders\n", p; p=0}' *_clean.md
```

Use these metrics to partition work. The constraint is **per-agent capacity**,
not agent count — spawn as many agents as needed:

**Per-agent limit: ≤ 500 lines total or ≤ 15 placeholders total**, whichever hits
first. A single sub-agent's context window must hold all its files plus the repair
instructions — exceeding ~500 lines risks context explosion and degraded output.

- Partition files greedily: add files to agent-N until adding the next file would
  exceed either limit, then start agent-N+1
- Group files by similar topic when possible (e.g., same lecture series)
- There is **no cap** on the number of sub-agents; spawn as many as the data demands

### Batch Phase 5: Spawn Sub-Agents for LLM Repair

Use the `Agent` tool with `subagent_type: "general-purpose"` for each sub-agent.
Spawn them **in parallel** (all in one message) so they run concurrently.
If there are more than ~10 agents, batch them in groups of 8-10 per message to
stay under tool-call limits.

Each sub-agent's prompt must be **fully self-contained** — the sub-agent does NOT
have access to this SKILL.md. Include:

1. **The exact file list** assigned to this agent (by name)
2. **The image mode** chosen by the user (embedded or referenced)
3. **The full LLM repair instructions** — copy Steps 3a–3f from Phase 3 above
   verbatim into the prompt (formula inference rules with examples, OCR fix
   table, partial math-mode merging, verification steps)
4. **The expected output**: each file → `<stem>_enhanced.md`
5. **A requirement to report back** with per-file stats (placeholders
   replaced, display/inline formulas added, any uncertainties)

Example prompt for a sub-agent:

```
You are repairing docling-generated markdown files from math PDFs
(MIT 18.01SC calculus lecture notes). Your task is to apply LLM semantic
repair to the following files:

  - /home/fuurin/study/calculus/Ses1_clean.md → output as Ses1_enhanced.md
  - /home/fuurin/study/calculus/Ses2_clean.md → output as Ses2_enhanced.md
  - /home/fuurin/study/calculus/Ses3_clean.md → output as Ses3_enhanced.md

Image mode: embedded (leave base64 data URIs as-is).

## Instructions

For each _clean.md file:

### Step 1: If image mode is "referenced"
... [copy Step 3a here] ...

### Step 2: Survey the damage
... [copy Step 3b here] ...

### Step 3: Fix formula placeholders
... [copy Step 3c here, including all 3 examples] ...

### Step 4: Fix OCR/Unicode issues
... [copy Step 3d here, including the full table] ...

### Step 5: Clean up partial math-mode
... [copy Step 3e here] ...

### Step 6: Verify
... [copy Step 3f here] ...

## Report

When done, write a summary for each file:
- File: <name>
- Formula placeholders replaced: N
- Display formulas ($$...$$) added: N
- Inline formulas ($...$) normalized: N
- Uncertainties: <list or "none">
```

### Batch Phase 6: Collect Results and Summarize

After all sub-agents complete, verify with a quick audit:

```bash
for f in *_enhanced.md; do
    remaining=$(grep -c 'formula-not-decoded' "$f" 2>/dev/null || echo 0)
    echo "$f: $remaining placeholders remaining"
done
```

Then present the summary table to the user:

| File | Placeholders | Display Formulas | Inline Formulas | Image Mode | Status |
|------|-------------|-----------------|-----------------|------------|--------|
| Ses1_enhanced.md | 0 | 10 | 135 | embedded | ✓ |
| Ses2_enhanced.md | 0 | 8 | 92 | embedded | ✓ |
| ... | ... | ... | ... | ... | ... |

If any file still has `formula-not-decoded` placeholders, flag it and ask the
user whether to re-repair or inspect manually.

### Batch Phase 7: Clean Up Intermediate Files

After the summary, **ask the user once:** *"Delete all intermediate files (`*_raw.md` and `*_clean.md`)?"*

Default to **keep**. If yes:

```bash
rm *_raw.md *_clean.md
```

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
