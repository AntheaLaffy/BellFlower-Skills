---
name: ocr-md-polish
description: >-
  Polish an OCR-generated Markdown file that already has LaTeX math.
  Fix formula rendering issues (subscripts, grouping, nested delimiters),
  remove OCR-duplicated text near images, clean up broken tables,
  restore list numbering hierarchy, unify split inline math,
  validate formulas semantically against surrounding context.
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
- Sub-items `(a) (b) (c)` got wrong top-level numbers like `2. (a)`, `3. (b)`
- Inline math split: `$f(x)$ = 0.5 x 3 -x` instead of `$f(x) = 0.5x^3 - x$`
- Two separate `$...$` spans that should be one formula, e.g. `$f(x) = e$ 的 $e^{x·\arctan(x)}$ 导数`
- Formula content doesn't match surrounding text ("切线" but formula has no slope)

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
  ├──[Phase 3] Fix numbering hierarchy & inline math
  │    • Restore flattened sub-items: N. (a/b/c) → indented (a/b/c)
  │    • Unify split math: $f(x)$ = 0.5 x 3 -x → $f(x) = 0.5x^3 - x$
  │
  ├──[Phase 4] Semantic formula validation
  │    • Merge adjacent $...$ spans that are one formula
  │    • Check context-formula consistency
  │    • Verify variable names match prose
  │
  └──[Phase 5] Verify
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

## Phase 3: Fix Numbering Hierarchy & Inline Math

OCR flattens list hierarchies and splits inline math across `$...$` boundaries.
Two common consequences:

### 3a: Flattened sub-item numbering

Original structure:
```
1. 将红色滑块移到 x = -0.75
   (a) 使用黄色滑块求出...
   (b) 使用切线复选框...
   (c) 求出一个 Δx 的值...
2. 现在使用红色滑块设置 x = 0
   (a) 求出当 x = 0 ...
```

OCR output (wrong):
```
1. 将红色滑块移到 x = -0.75
2. (a) 使用黄色滑块求出...     ← orphaned "2.", should be indented (a)
3. (b) 使用切线复选框...       ← orphaned "3.", should be indented (b)
```

The OCR treats every `(a)` `(b)` `(c)` line as a new top-level numbered item,
giving it a wrong number like `2.` or `3.` that conflicts with the real
top-level items.  Markdown renderers display this as:

```
1.  将红色滑块移到 x = -0.75
2.  (a) 使用黄色滑块求出...     ← looks like a sibling, not a sub-item
```

**Detection:**

```bash
# Find "N. (a/b/c)" lines where N is not the expected parent number
grep -nP '^\d+\.\s*\((a|b|c)\)' *.md
```

**Fix:** For each such line:
1. Determine the **parent** numbered item (the closest preceding `N.` line
   without `(a/b/c)` suffix)
2. Remove the top-level number prefix
3. **Apply US textbook indentation:** 3 spaces, then `(a)`, `(b)`, or `(c)`
4. If the line uses a dash prefix (`- (a)`), remove it — the indent alone
   conveys the hierarchy

| Before | After | Style |
|--------|-------|-------|
| `2. (a) 使用黄色滑块求出...` | `   (a) 使用黄色滑块求出...` | 3-space indent |
| `3. (b) 对于某些 x 的值...` | `   (b) 对于某些 x 的值...` | 3-space indent |
| `- (a) 求出当 x = 0...` | `   (a) 求出当 x = 0...` | Remove dash, add indent |
| `- (b) 使用切线复选框...` | `   (b) 使用切线复选框...` | Remove dash, add indent |

**Note:** The 3-space indented `(a)(b)(c)` lines are plain text (not Markdown
list syntax), which is intentional — US textbooks render sub-items as a visual
continuation of the parent item, not as a separate nested list.

**Edge cases to watch:**
- Lines with `(c)` inside the text (e.g., `问题 (c) 部分`) — these are
  **not** sub-item markers, don't touch them.  Only match `(a)`, `(b)`, `(c)`
  at the **start** of the line (after the number prefix).
- A `(a) (b) (c)` block may be followed by another top-level number that
  continues correctly (`2.`, `3.` etc.) — leave the real top-level items alone.
- In a "解答" (solutions) section, the structure mirrors the exercises.
  Apply the same logic.

### 3b: Split inline math

Some OCR pipelines output what should be a single math expression as
separate `$...$` spans with text in between:

```
... $f(x)$ = 0.5 x 3 -x 是一个奇函数
... $f(x)$ = e 这样的函数
```

The `$...$` span ends too early; `= 0.5 x 3 -x` is left as plain text
instead of being part of the math expression.

**Detection:**

```bash
# Find math mode followed by = and plain text on the same line
grep -nP '\$[^$]*\$\s*=' *.md
```

**Fix:** Merge into a single math expression, and fix the plain-text notation
at the same time:

| Before | After | Notes |
|--------|-------|-------|
| `$f(x)$ = 0.5 x 3 -x` | `$f(x) = 0.5x^3 - x$` | Missing `^` for power, missing braces on subscript |
| `$f(x)$ = e 这样的` | `$f(x) = e$ 这样的` | End math after `e`; keep rest as text |
| `$f(x)$ = 0.5 x 3 -x 是奇函数` | `$f(x) = 0.5x^3 - x$ 是奇函数` | Full formula fixed |

Common plain-text repair table (also applies here):

| Plain text | LaTeX |
|------------|-------|
| `0.5 x 3` | `0.5x^3` |
| `x 3 - x` | `x^3 - x` |
| `x 2` | `x^2` |
| `x 3 + 2 x 2` | `x^3 + 2x^2` |

When in doubt about the intended formula, read the surrounding sentence
context to infer the correct LaTeX.

## Phase 4: Semantic Formula Validation

Some LaTeX formulas are **syntactically valid but semantically wrong**.
OCR can produce correct-looking `$...$` that doesn't match what the
surrounding text describes.  Read context to catch these.

### 4a: Split formula across adjacent math spans

Two adjacent `$...$` spans with a small piece of text between them may
actually be **one** formula that was split by OCR:

```
Wrong:  求像 $f(x) = e$ 这样的函数的 $e^{x \arctan(x)}$ 导数
        │───────────────│                   │─────────────────│
        separate spans, but the text describes ONE function

Correct (unified):  $f(x) = e^{x \arctan(x)}$ 这样的函数的导数
                    │─────────────────────────│
                    one formula: f(x) = e^(x·arctan(x))
```

**Detection:** Scan for two `$...$` expressions separated by ≤6 words
where the second span's content looks like a continuation of the first.

```bash
# Find adjacent $...$ spans with short text between them
# (awk match: close $, ≤6 words, open $, suggesting split formula)
grep -nP '\$[^$]*\$\s*\S+(\s+\S+){0,5}\s*\$[^$]*\$' *.md
```

**Fix:** For each candidate:
1. Read the sentence context — what single formula does it describe?
2. Merge into one `$...$` span with correct LaTeX
3. Keep text that isn't part of the formula outside the math mode

| Before | After | Reasoning |
|--------|-------|-----------|
| `求像 $f(x) = e$ 这样的函数的 $e^{x \arctan(x)}$ 导数` | `求 $f(x) = e^{x \arctan(x)}$ 这样的函数的导数` | "e^(x·arctan(x))" is the exponent, not a separate function |
| `计算 $f'(x)$ 也就是切线斜率的值` | `计算切线斜率 $f'(x)$ 的值` (depends on context) | Merge split text into coherent sentence |

### 4b: Context-formula mismatch

The surrounding text often signals what the formula *should* say.
Compare the formula's mathematical content with nearby keywords:

| Context keyword | Expected formula property | Red flag |
|----------------|---------------------------|----------|
| "导数" / "求导" (differentiate) | Contains derivative notation `f'`, `\frac{d}{dx}`, `\lim` | Plain expression like `$x^2$` with no derivative |
| "切线" / "切线斜率" (tangent) | Involves slope, `f'(x_0)`, `\lim` | Formula about area or integral |
| "奇函数" (odd function) | Satisfies `f(-x) = -f(x)` | Formula that doesn't satisfy the property |
| "极限" (limit) | Contains `\lim` | Missing `\lim` |
| "割线" (secant line) | Involves `\Delta f / \Delta x`, `(f(x+Δx)-f(x))/Δx` | Formula unrelated to secant |

```bash
# Scan for potential mismatches — "odd function" + formula (verify manually)
grep -n '奇函数\|偶函数' *.md
# Then read the formula near the match and verify f(-x) = -f(x)
```

This check requires **reading comprehension** — there is no regex that can
fully automate it.  Treat it as a human-in-the-loop sanity check.

### 4c: Obvious OCR corruption in formula text

English words that OCR misread as math or vice versa:

| Pattern | Likely fix |
|---------|-----------|
| `$f(x)$ = 0.5 x 3 -x` | `$f(x) = 0.5x^3 - x$` (also covered in Phase 3b) |
| `$f$ 是一个函数` where $f$ should be plain | Keep but double-check |
| `$f(x)$ 的图像` — fine | Leave alone |

### 4d: Variable consistency

Variables used in a formula should appear in the surrounding sentence:

- Text says "点 P" and "x₀" → formula should use `x_0`, not `t` or `a`
- Formula uses `\Delta x`, `\Delta f` → text nearby should mention "delta x"

This is a **manual review** step.  Read through the file and flag any
formula whose variables don't match the surrounding prose.

### 4e: One-pass reading strategy

Rather than inspecting every formula in isolation, **read the file
as a coherent document** from start to finish after the mechanical
fixes (Phases 1–3).  While reading:

1. When you hit a formula, pause and check: does it match what the
   preceding sentences are describing?
2. Does the prose flow naturally around the formula, or does it
   seem like the text and the math are describing different things?
3. Are there two `$...$` spans that should clearly be one (4a)?

This one-pass approach catches most semantic issues because the
OCR corruption that caused them is usually visible at reading speed.

## Phase 5: Verify

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

## Phase 6: Batch Mode (Multiple Files)

When there are **multiple** markdown files to polish (e.g., an entire lecture
series `Ses1_enhanced.md` … `SesN_enhanced.md`), use the batch workflow below.

### 6a: Survey all files (no reading)

Do **not** read every file.  Use grep/awk to collect metrics:

```bash
# Per-file stats: lines, subscript candidates, nested $, images,
# broken tables, orphaned sub-items, split math
for f in *.md; do
    subs=$(grep -cP '\$[^$]*[a-z] ?0[^_$]' "$f" 2>/dev/null || echo 0)
    nested=$(grep -cP '\$[^$]*\$[^$]*\$' "$f" 2>/dev/null || echo 0)
    imgs=$(grep -c '!\[Image\]' "$f" 2>/dev/null || echo 0)
    tabs=$(grep -cP '^\| *- ?0' "$f" 2>/dev/null || echo 0)
    orphans=$(grep -cP '^\d+\.\s*\((a|b|c)\)' "$f" 2>/dev/null || echo 0)
    split=$(grep -cP '\$[^$]*\$\s*=' "$f" 2>/dev/null || echo 0)
    printf "%-40s subs=%d nested=%d images=%d ocr-tables=%d orphans=%d split=%d\n" \
           "$f" "$subs" "$nested" "$imgs" "$tabs" "$orphans" "$split"
done
```

This produces a table like:

```
Ses1_enhanced.md        subs=5  nested=3  images=7  ocr-tables=2  orphans=3  split=1
Ses2_enhanced.md        subs=2  nested=0  images=5  ocr-tables=0  orphans=0  split=0
Ses3_enhanced.md        subs=8  nested=1  images=6  ocr-tables=1  orphans=2  split=0
...
```

### 6b: Partition into work batches

**Per-agent limit: ≤ 500 lines or ≤ 10 images or ≤ 15 grep-hits combined** —
whichever hits first.  This prevents a sub-agent's context from overflowing
with the file contents.

- Greedy-partition files: add to agent-N until the next file would exceed
  any limit, then start agent-N+1.
- There is **no cap** on the number of agents; spawn as many as needed.
- For a single quick pass (≤3 files, small), just do it sequentially yourself.

### 6c: Spawn sub-agents (parallel)

Same as in single-file mode, but each sub-agent processes its assigned batch.

Use `Agent` with `subagent_type: "general-purpose"` for each batch.
Spawn them all in one message so they run concurrently (max ~8 per message).

Each sub-agent prompt must be **self-contained**.  Include:

1. The exact file list assigned to that agent
2. The **Phases 1–5 instructions** from this skill (copy verbatim) —
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

[copy Phases 1–5 verbatim from the skill]

## Report

After each file, write a summary line:
  <file>: subs=N, exponents=N, nested=N, ocr-lines=N, tables=N, orphans=N, split=N
Then a final line: DONE
```

### 6d: Collect results

After all agents complete, re-run the survey command from 5a to confirm
everything is clean:

```bash
for f in *.md; do
    subs=$(grep -cP '\$[^$]*[a-z] ?0[^_$]' "$f" 2>/dev/null || echo 0)
    nested=$(grep -cP '\$[^$]*\$[^$]*\$' "$f" 2>/dev/null || echo 0)
    tabs=$(grep -cP '^\| *- ?0' "$f" 2>/dev/null || echo 0)
    orphans=$(grep -cP '^\d+\.\s*\((a|b|c)\)' "$f" 2>/dev/null || echo 0)
    split=$(grep -cP '\$[^$]*\$\s*=' "$f" 2>/dev/null || echo 0)
    echo "$f: subs=$subs nested=$nested ocr-tables=$tabs orphans=$orphans split=$split"
done
```

If any file still has issues, flag it for a re-pass or manual inspection.

### 6e: Consolidated Report

| File | Subscript | Exponent | Nested | OCR Lines | Tables | Orphaned Sub-items | Split Math | Status |
|------|-----------|----------|--------|-----------|--------|-------------------|------------|--------|
| Ses1 | 5 | 1 | 3 | 2 | 1 | 3 | 1 | ✓ |
| Ses2 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | ✓ |
| Ses3 | 8 | 2 | 1 | 1 | 1 | 2 | 0 | ✓ |
| **Total** | **15** | **3** | **4** | **3** | **2** | **5** | **1** | |

Include any files that need manual follow-up.

## Single-File Report

When done with a single file, summarize:

1. **Subscript fixes:** N instances of `x 0` → `x_0` etc.
2. **Exponent grouping fixes:** N instances (e.g., `e^x arctan(x)` → `e^{x \arctan(x)}`)
3. **Nested math mode fixes:** N instances merged
4. **OCR-duplicated text removed:** N lines (with image names)
5. **Tables removed:** N OCR tables
6. **Figure captions kept:** N captions left in place
7. **Orphaned sub-items fixed:** N lines where `N. (a/b/c)` → indented `(a/b/c)`
8. **Split inline math unified:** N instances of `$f(x)$ = ...` → `$f(x) = ...$`
9. **Semantic formula fixes:** N instances where formula didn't match context (split spans, wrong expression)
10. **Remaining issues:** any uncertainties or unfixable patterns
