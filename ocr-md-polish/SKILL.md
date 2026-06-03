---
name: ocr-md-polish
description: >-
  Polish an OCR-generated Markdown file that already has LaTeX math.
  Fix formula rendering issues (subscripts, grouping, nested delimiters),
  remove OCR-duplicated text near images, clean up broken tables.
---

# OCR Markdown Polish

Fix formula rendering issues and clean OCR artifacts in a Markdown file
that was produced by OCR (e.g., via docling + LLM repair).  The file
already has `$...$` / `$$...$$` LaTeX — this skill fixes what still
looks wrong.

## When To Use

- `$e^x arctan(x)$` renders as `eˣ · arctan(x)` instead of `e^{x·arctan(x)}`
- `x 0` appears instead of `x_0` (missing subscript underscore)
- Nested `$...$` like `$f(x 0 +$\Delta x$)$` where the second `$\Delta x$` is outside math mode
- Broken OCR tables near images (the image IS the table)
- `$\Delta x$` or similar axis labels from images bleeding into text

## Pipeline

```
en_zh_enhanced.md
  │
  ├──[Phase 1] Fix LaTeX rendering issues
  │    • Missing subscripts: x 0 → x_0, y0 → y_0
  │    • Exponent grouping:  e^x arctan(x) → e^{x \arctan(x)}
  │    • Nested math mode:   $f(x 0 +$\Delta x$)$ → $f(x_0 + \Delta x)$
  │
  ├──[Phase 2] Clean OCR-duplicated text near images
  │    • OCR-check suspicious text against image content
  │    • Remove text that belongs to the image (axis labels, in-image tables)
  │    • Keep legitimate figure captions ("Figure 1: ...")
  │
  └──[Phase 3] Verify
       • No nested $...$ patterns
       • No variable+number without underscore in math mode
       • No broken OCR tables
       • Balanced $ delimiters
```

## Phase 1: Fix LaTeX Rendering Issues

### 1a: Missing subscripts

docling often outputs `x0`, `x 0`, `y0` instead of `x_0`, `y_0` —
in math mode these render as multiplication `x·0` rather than subscript `x₀`.

```bash
# Find candidates (in math mode: inside $...$ or $$...$$)
grep -nP '\$[^$]*[a-zA-Z] ?0[^_$]'  *.md
```

Fix: `x 0` → `x_0`, `y0` → `y_0`, `f(x0)` → `f(x_0)` etc.
If `x 0` is in plain text (not math mode), wrap it: `x 0` → `$x_0$`.

### 1b: Exponent grouping

`^` in LaTeX only takes the next **single** character unless followed
by `{braces}`. Common OCR output that looks like `$e^x arctan(x)$`
(or `$e^x·arctan(x)$`, `$e^x·atan(x)$`) should be `$e^{x \arctan(x)}$`.

Scan for bare `^` operators that may need braces:

```bash
grep -nP '\^[a-zA-Z]' *.md | grep -vP '\^\{|\^2'
```

### 1c: Nested math mode delimiters

Some OCR pipelines produce nested `$...$` like:

```
$f(x 0 +$\Delta x$)$
```

In standard Markdown, `$...$` does **not** nest — the second `$` closes
the outer mode.  Only the text up to that `$` is rendered as math;
everything after it is plain text.

**Fix:** Merge into a single math expression:

| Before | After |
|--------|-------|
| `$f(x 0 +$\Delta x$)$` | `$f(x_0 + \Delta x)$` |
| `$\Delta f$ = $f(x 0 +$\Delta x$)$ -$f(x 0)$` | `$\Delta f = f(x_0 + \Delta x) - f(x_0)$` |
| `( x 0 +$\Delta x$, $f(x 0 +$\Delta x$)$)` | `$(x_0 + \Delta x, f(x_0 + \Delta x))$` |

Also check for partial math-mode spans that should be a single span:

| Before | After |
|--------|-------|
| `( x 0 , $y_0$ )` | `$(x_0, y_0)$` |
| `P = ( x 0 , $f(x 0)$` | `$P = (x_0, f(x_0))$` |

## Phase 2: Clean OCR-Duplicated Text Near Images

Text that appears **immediately before or after** an `![Image](...)` line
may have been OCR'd **from the image itself** rather than being legitimate
document text.

### 2a: OCR-check — distinguish image content from figure captions

Run OCR on the image to see what text it contains:

```bash
# Install tesseract if not already available
which tesseract || sudo pacman -S tesseract

# Run OCR on the image
tesseract "<image_path>" stdout 2>/dev/null
```

Compare the OCR output with the text adjacent to the image in the file.
If the text matches, it's likely OCR-duplicated from the image and should
be removed.

### 2b: What to keep vs. remove

| Text | Likely | Action |
|------|--------|--------|
| `$\Delta x$` near a graph image | Axis label from the image | Remove |
| `图 1：导数的几何定义` | Figure caption (translates "Figure 1: ...") | **Keep** |
| A full markdown table with broken cell data near an image | OCR of an in-image table | Remove |
| `Step 1: ...`, `Solution:` | Part of the lecture text | Keep (verify) |

**Rule of thumb:** If the text appears *in the image* (verified via OCR),
it's duplicated. If the text describes the image without being in it
(e.g., "Figure 1: ..."), it's a legitimate caption.

### 2c: Clean up

After identifying OCR garbage:

- **Single lines:** remove the line entirely
- **Tables:** remove the entire table block (header + separator + rows)
- **Captions to keep:** leave them adjacent to the image as `图 N` or the
  appropriate translation of "Figure N"

## Phase 3: Verify

Run these checks after editing:

### Balanced math delimiters

```bash
# Count $ signs — should be even (each pair is one open + one close)
grep -c '\$' *.md          # inline $ count — rows, not ideal
python3 -c "
import re
with open('<file>') as f:
    t = f.read()
    # Count $$ pairs (display math)
    dd = len(re.findall(r'\$\$', t))
    # Count $ (inline), excluding those inside $$
    singles = len(re.findall(r'(?<!\$)\$(?!\$)', t))
    print(f'display ($$): {dd//2} pairs, inline (\$): {singles//2} pairs')
"
```

### No remaining nested `$` or broken subscripts

```bash
# No variable+number without underscore in math mode
grep -nP '\$[^$]*[a-z] ?0[^_$]' *.md

# No nested $...$ (two $ in close proximity inside one $...$ span)
grep -nP '\$[^$]*\$[^$]*\$' *.md | grep -v '^\$\$'

# No broken OCR tables (table rows with all values in one cell)
grep -nP '^\| *- ?0' *.md
```

### Unusual characters

```bash
# Replacement characters
grep -n '�' *.md
```

## Phase 4: Batch Mode (Multiple Files)

When there are **multiple** markdown files to polish (e.g., an entire lecture
series `Ses1_enhanced.md` … `SesN_enhanced.md`), use the batch workflow below.

### 4a: Survey all files (no reading)

Do **not** read every file.  Use grep/awk to collect metrics:

```bash
# Per-file stats: lines, subscript candidates, nested $, images, tables
for f in *.md; do
    subs=$(grep -cP '\$[^$]*[a-z] ?0[^_$]' "$f" 2>/dev/null || echo 0)
    nested=$(grep -cP '\$[^$]*\$[^$]*\$' "$f" 2>/dev/null || echo 0)
    imgs=$(grep -c '!\[Image\]' "$f" 2>/dev/null || echo 0)
    tabs=$(grep -cP '^\| *- ?0' "$f" 2>/dev/null || echo 0)
    printf "%-40s subs=%d nested=%d images=%d ocr-tables=%d\n" "$f" "$subs" "$nested" "$imgs" "$tabs"
done
```

This produces a table like:

```
Ses1_enhanced.md        subs=5  nested=3  images=7  ocr-tables=2
Ses2_enhanced.md        subs=2  nested=0  images=5  ocr-tables=0
Ses3_enhanced.md        subs=8  nested=1  images=6  ocr-tables=1
...
```

### 4b: Partition into work batches

**Per-agent limit: ≤ 500 lines or ≤ 10 images or ≤ 15 grep-hits combined** —
whichever hits first.  This prevents a sub-agent's context from overflowing
with the file contents.

- Greedy-partition files: add to agent-N until the next file would exceed
  any limit, then start agent-N+1.
- There is **no cap** on the number of agents; spawn as many as needed.
- For a single quick pass (≤3 files, small), just do it sequentially yourself.

### 4c: Spawn sub-agents (parallel)

Use `Agent` with `subagent_type: "general-purpose"` for each batch.
Spawn them all in one message so they run concurrently (max ~8 per message).

Each sub-agent prompt must be **self-contained**.  Include:

1. The exact file list assigned to that agent
2. The **phases 1–3 instructions** from this skill (copy verbatim) —
   the sub-agent has no access to this SKILL.md
3. The expected output naming: keep the same filename (edit in-place)
4. A requirement to report per-file stats

Example prompt:

```
You are polishing OCR-generated Markdown files.  Edit the files *in place*.

Files to process:
  - /path/to/Ses1_enhanced.md
  - /path/to/Ses3_enhanced.md

## Instructions

[copy Phases 1–3 verbatim from the skill]

## Report

After each file, write a summary line:
  <file>: subs=N, exponents=N, nested=N, ocr-lines=N, tables=N
Then a final line: DONE
```

### 4d: Collect results

After all agents complete, re-run the survey command from 4a to confirm
everything is clean:

```bash
for f in *.md; do
    subs=$(grep -cP '\$[^$]*[a-z] ?0[^_$]' "$f" 2>/dev/null || echo 0)
    nested=$(grep -cP '\$[^$]*\$[^$]*\$' "$f" 2>/dev/null || echo 0)
    tabs=$(grep -cP '^\| *- ?0' "$f" 2>/dev/null || echo 0)
    echo "$f: subs=$subs nested=$nested ocr-tables=$tabs"
done
```

If any file still has issues, flag it for a re-pass or manual inspection.

### 4e: Consolidated Report

| File | Subscript Fixes | Exponent Fixes | Nested Merged | OCR Lines Removed | Tables Removed | Status |
|------|----------------|----------------|---------------|-------------------|----------------|--------|
| Ses1_enhanced.md | 5 | 1 | 3 | 2 | 1 | ✓ |
| Ses2_enhanced.md | 2 | 0 | 0 | 0 | 0 | ✓ |
| Ses3_enhanced.md | 8 | 2 | 1 | 1 | 1 | ✓ |
| **Total** | **15** | **3** | **4** | **3** | **2** | |

Include any files that need manual follow-up.

## Single-File Report

When done with a single file, summarize:

1. **Subscript fixes:** N instances of `x 0` → `x_0` etc.
2. **Exponent grouping fixes:** N instances (e.g., `e^x arctan(x)` → `e^{x \arctan(x)}`)
3. **Nested math mode fixes:** N instances merged
4. **OCR-duplicated text removed:** N lines (with image names)
5. **Tables removed:** N OCR tables
6. **Figure captions kept:** N captions left in place
7. **Remaining issues:** any uncertainties or unfixable patterns
