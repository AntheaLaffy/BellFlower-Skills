---
name: markdown-translate
description: >-
  Translate Markdown text (lecture notes, documentation, articles) between
  languages while preserving Markdown formatting, LaTeX math, code blocks,
  images, HTML comments, and frontmatter. Use this skill whenever the user
  asks to translate a Markdown file, convert lecture notes to another
  language, or batch-translate Markdown documents.
---

# Markdown Translation

Translate Markdown files between languages using LLM, preserving all
formatting, LaTeX math, code blocks, images, and special markup.

## Core Principle

**Only translate linguistic content** — everything else is carried through
verbatim:

| Element | Action |
|---------|--------|
| `$...$` inline math | **Do not translate** — copy verbatim |
| `$$...$$` display math | **Do not translate** — copy verbatim |
| `\\( ... \\)` inline math | **Do not translate** — copy verbatim |
| `\\[ ... \\]` display math | **Do not translate** — copy verbatim |
| ` ``` ` code blocks | **Do not translate** — copy verbatim |
| `` `inline code` `` | **Do not translate** — copy verbatim |
| `![](path)` images | **Do not translate** — copy verbatim |
| `<img ...>` HTML images | **Do not translate** — copy verbatim |
| `<!-- comments -->` | **Do not translate** — copy verbatim |
| `[text](url)` links | Translate link **text**, keep URL |
| `![alt](url)` images | Translate **alt text**, keep URL |
| `---` frontmatter | Translate **values**, keep keys |
| Markdown tables | Translate **cell content**, keep structure |
| `# Headings` | Translate heading text, keep `#` markers |
| `> blockquotes` | Translate content, keep `>` markers |
| `- list items` | Translate content, keep `-` markers |

## Pipeline Overview

```
input.md ──[survey]──> plan ──[LLM translate]──> output_<lang>.md
                              (direct or chunked)
```

No external tools required — the LLM does all the work.

## Phase 1: Gather Requirements

Ask the user (if not specified):

1. **Source language** — default: auto-detect from content
2. **Target language** — required (e.g., `zh`, `ja`, `en`)
3. **Which files** — single file, glob pattern, or list

For language codes, use ISO 639-1: `zh` (Chinese), `ja` (Japanese),
`en` (English), `ko` (Korean), `fr` (French), `de` (German), etc.

### Output Naming

Default pattern: `<original_stem>_<target_lang>.md`

| Source | Target | Output |
|--------|--------|--------|
| `Ses1_enhanced.md` | `zh` | `Ses1_enhanced_zh.md` |
| `notes.md` | `ja` | `notes_ja.md` |
| `readme.md` | `zh` | `readme_zh.md` |

If the user wants a different naming convention, ask.

## Phase 2: Survey the Files

For each file, collect:

```bash
wc -l <file>          # total lines
grep -c '$$' <file>   # display math count
grep -c '```' <file>  # code fence count
grep -c '<!--' <file> # HTML comment count
```

Use this to assess complexity:

| Metric | Threshold | Strategy |
|--------|-----------|----------|
| ≤ 300 lines | Small | Direct LLM translation |
| 300–800 lines | Medium | Read + translate in sections |
| > 800 lines | Large | Chunk by major headings |

### Large File Strategy

For files > 800 lines, split by `##` (level-2) headings:

1. Read the file and identify `##` heading boundaries
2. Group sections into chunks of ~200–400 lines each
3. Translate each chunk separately, carrying context from the previous chunk
4. Concatenate results, verify continuity

## Phase 3: Translate

### Direct Translation (files ≤ 800 lines)

Read the file, then translate the entire content in one pass. The LLM is
instructed to produce the translated Markdown with all protected elements
preserved.

### Chunked Translation (files > 800 lines)

1. Read the file in sections (e.g., 300-line windows)
2. Translate each section, noting the last heading for context
3. Assemble the translated sections
4. Verify structural integrity

## Phase 4: Verify

After translation, check:

### Math Integrity

```bash
# Count $$ blocks should match between source and translation
echo "Source: $(grep -c '\$\$' input.md)"
echo "Output: $(grep -c '\$\$' output.md)"
```

### Code Block Integrity

```bash
# ``` fences should be even in both files
echo "Source: $(grep -c '```' input.md)"
echo "Output: $(grep -c '```' output.md)"
```

### Structural Scan

```bash
# Heading count should match
echo "Source headings: $(grep -c '^#' input.md)"
echo "Output headings: $(grep -c '^#' output.md)"

# Image count should match
echo "Source images: $(grep -c '!\[.*\](.*)' input.md)"
echo "Output images: $(grep -c '!\[.*\](.*)' output.md)"
```

### Quick Visual Check

Scan the translated file for:
- Unbalanced `$` signs (each `$$` count must be even; `$...$` must not span paragraphs)
- Raw URLs that should have been in links
- Corrupted LaTeX (e.g., missing backslashes on commands)
- Untranslated blocks that should have been translated

## Phase 5: Clean Up

After the translation is written and verified, **ask the user:**
*"Translation complete. Delete the source Markdown file(s)?"*

Default to **keep** (no deletion). If the user says yes:

```bash
rm <original>.md
```

For batch mode, list the files that would be deleted and ask once.

Only offer this for files that were the direct input to translation.
Do **not** offer to delete files that were not part of the translation
task (e.g., don't touch `*_raw.md` or `*_clean.md` from pdf-math-convert).

## Translation Quality Guidelines

When translating, follow these principles:

### For Math-Heavy Content (Lecture Notes, Papers)

1. **Read the surrounding English first** — understand the mathematical
   context before translating
2. **Preserve mathematical register** — use the target language's standard
   math terminology (e.g., "derivative" → "导数" in zh, "導関数" in ja)
3. **Keep notation explanations clear** — when the text explains what a
   formula means, ensure the translation is equally precise
4. **Variable names in prose**: when the text says "let f(x) be..." the
   math stays as `$f(x)$` but the surrounding words are translated

### Caveat: Source Formulas May Be Imperfect

**The source Markdown content is generated from PDF via OCR + LLM inference.**
This means formulas may contain errors:

1. **Formula-Text Conflict**: If the surrounding article text clearly
   describes a formula that differs from the rendered LaTeX, **trust the
   article text**. The OCR-to-LaTeX pipeline can misinterpret symbols or
   structure. Correct the formula to match what the text describes.

2. **Derivation Depth May Be Off**: Some formula derivations may be
   unnecessarily verbose or overly terse. There is no universal standard
   for "right" — follow the context:
   - **If a partial derivation of this formula appeared earlier in
     detail**, avoid repeating it verbosely here; a concise restatement
     is sufficient.
   - **If this formula is the core thesis of the section** (the central
     point the section builds toward), emphasize its derivation and core
     logic, and de-emphasize secondary/tangential steps.
   - When in doubt, **preserve the source's level of detail**. Only
     adjust when the imbalance is clearly harmful to understanding.

3. **Check for Omitted Context**: Sometimes the source may have lost
   intermediate steps during OCR. If the article text logically implies
   a step that the formula skips, add a brief clarifying intermediate
   hint in the translation. Use `<!-- TN: added intermediate step for
   clarity -->` to mark such additions.

4. **When to Leave As-Is**: If the formula looks plausible and the
   surrounding text is not contradictory, do not second-guess the
   inference — leave it unchanged.

### Consistency

- Use the same translation for the same term throughout all files
- For academic content, prefer formal/standard terminology over colloquial
- When in doubt about a technical term's translation, add a brief note:
  `<!-- TN: "eigenvalue" → 固有値 -->`

### Formatting Preservation

- Never add or remove blank lines around math blocks
- Never change indentation of list items
- Never convert `*` lists to `-` lists or vice versa
- Preserve the original's link reference style (inline vs reference-style)

## Batch Processing (Multiple Files)

When the user asks to translate **more than one** file, follow this
orchestrated workflow.

### Batch Phase 1: Survey All Files

Collect line counts and complexity metrics:

```bash
for f in <files>; do
    echo "$f: $(wc -l < "$f") lines, \
      $(grep -c '\$\$' "$f") display-math, \
      $(grep -c '```' "$f") code-fences"
done
```

### Batch Phase 2: Ask Language Once

**Ask the user once:**
- Source language? (default: auto-detect)
- Target language?
- Output naming: `<stem>_<lang>.md` OK?

### Batch Phase 3: Partition Work

Group files by complexity:

| Per-agent budget | Threshold |
|------------------|-----------|
| Total lines | ≤ 800 |
| Or file count | ≤ 5 small files |

Partition greedily — add files to agent-N until adding the next would
exceed either limit.

### Batch Phase 4: Spawn Sub-Agents

Use the `Agent` tool with `subagent_type: "general-purpose"` for each
sub-agent. Spawn them **in parallel** so they run concurrently.

Each sub-agent's prompt must be **fully self-contained** — include:

1. **File list** assigned to this agent
2. **Source language** and **target language**
3. **Full translation instructions** — copy the Protected Elements table
   from the Core Principle section, plus the Translation Quality Guidelines
4. **Output naming convention**
5. **Verification steps** from Phase 4

Example sub-agent prompt:

```
You are translating Markdown files from English (en) to Chinese (zh).
Your task: translate the following files while preserving all Markdown
formatting, LaTeX math, code blocks, images, and HTML comments.

Files to translate:
  - /path/to/Ses1_enhanced.md → Ses1_enhanced_zh.md
  - /path/to/Ses2_enhanced.md → Ses2_enhanced_zh.md
  - /path/to/Ses3_enhanced.md → Ses3_enhanced_zh.md

## Protected Elements — Do NOT Translate

| Element | Action |
|---------|--------|
| $...$ inline math | Copy verbatim |
| $$...$$ display math | Copy verbatim |
| \( ... \) inline math | Copy verbatim |
| \[ ... \] display math | Copy verbatim |
| ``` code blocks ``` | Copy verbatim |
| `inline code` | Copy verbatim |
| ![](images) | Copy verbatim |
| <!-- comments --> | Copy verbatim |
| [text](url) links | Translate text, keep URL |
| ![alt](url) images | Translate alt, keep URL |
| --- frontmatter | Translate values, keep keys |

## Translation Quality

- Use standard mathematical terminology in Chinese
- Preserve the original's formatting exactly (blank lines, indentation, list markers)
- Be consistent with terminology across all files
- Read the surrounding context to understand the math before translating

## Verification

After translating each file:
1. Count $$ blocks (must match source)
2. Count ``` fences (must match source)
3. Count headings (must match source)
4. Scan for unbalanced $ signs

## Report

For each file, report:
- File name
- Any issues encountered
- Verification results (math blocks match? code blocks match?)
```

### Batch Phase 5: Collect and Summarize

After all sub-agents complete, run a quick audit:

```bash
for f in *_zh.md *_ja.md; do
    echo "=== $f ==="
    echo "Display math blocks: $(grep -c '\$\$' "$f")"
    echo "Code fences: $(grep -c '```' "$f")"
    echo "Headings: $(grep -c '^#' "$f")"
done
```

Present a summary table:

| File | Lines | Math OK | Code OK | Headings OK | Status |
|------|-------|---------|---------|-------------|--------|
| Ses1_enhanced_zh.md | 245 | ✓ | ✓ | ✓ | Done |
| Ses2_enhanced_zh.md | 198 | ✓ | ✓ | ✓ | Done |

If any file fails verification, flag it and ask the user whether to
re-translate or inspect manually.

### Batch Phase 6: Clean Up

After the summary, **ask the user once:**
*"Delete the source Markdown files that were translated?"*

List every source file that would be affected and default to **keep**.

If the user confirms:

```bash
rm <source1>.md <source2>.md ...
```

Only delete files that were the direct input to this translation batch.
Do **not** touch unrelated files (e.g., `*_raw.md` or `*_clean.md` from
pdf-math-convert) — those belong to other skills.

## Edge Cases

### Mixed-Language Content

If the source already contains multiple languages (e.g., English math
notes with Chinese annotations), ask the user which parts to translate:
- Translate everything to target language
- Translate only the primary language sections
- Skip already-translated parts

### Very Long Math Blocks

If a single `$$...$$` block spans many lines and contains comments in
the source language surrounded by `\text{}`:

```
$$
f'(x) = \lim_{h \to 0} \frac{f(x+h) - f(x)}{h}
\quad \text{this is the definition of the derivative}
$$
```

The `\text{}` content **should** be translated, but the math should not.
Handle this carefully — translating `\text{}` inside math requires
understanding LaTeX math mode boundaries.

### Links to External Resources

For `[text](url)` links:
- Translate the display text
- **Never modify the URL**
- If the URL contains language-specific content, note it but don't change

### Diplomatic / Sensitive Content

If the content appears politically or culturally sensitive, translate
literally and neutrally. Do not editorialize or add commentary.
When in doubt, add a translator's note: `<!-- TN: literal translation -->`

## Fallbacks

If the LLM translation quality is poor for a specific domain:

1. **Build a glossary** — collect domain-specific terms and their preferred
   translations, include at the top of the translation prompt
2. **Chunk smaller** — reduce context window to improve focus
3. **Two-pass**: first pass translates, second pass reviews and polishes
   specific terminology
4. **Human review markers**: add `<!-- REVIEW: ... -->` comments on
   uncertain translations for later human review
