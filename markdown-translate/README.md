# markdown-translate

Translate Markdown files between languages using LLM, preserving LaTeX math, code blocks, images, and all formatting.

## Quick Start

```
/invoke markdown-translate
```

Then answer the prompts:
- **Source language** (auto-detect or specify)
- **Target language** (e.g., `zh` for Chinese, `ja` for Japanese)
- **Files** to translate (single file, glob, or list)

The skill handles the rest — reading, translating, verifying, and writing output files.

## What It Does

1. **Reads** the Markdown source
2. **Translates** linguistic content to the target language
3. **Preserves** math (`$...$`, `$$...$$`), code blocks, images, HTML comments, and Markdown structure
4. **Verifies** that protected elements survived translation intact
5. **Outputs** `<original>_<lang>.md` (e.g., `notes_zh.md`)

## Protected Elements

These are **never translated** — they pass through verbatim:

| Element | Example |
|---------|---------|
| Inline math | `$f(x) = x^2$` |
| Display math | `$$\lim_{x \to 0} f(x)$$` |
| Code blocks | `` ```python ... ``` `` |
| Inline code | `` `variable_name` `` |
| Images | `![](diagram.png)` |
| HTML comments | `<!-- formula-not-decoded -->` |
| URLs | `[link text](https://...)` |

## Batch Processing

For multiple files, the skill orchestrates parallel sub-agents:

- Files are partitioned by size (≤ 800 lines per agent)
- All agents run concurrently
- Results are collected and verified in a summary table

## Limitations

- **Math inside `\text{}`**: may need manual review — this is translatable
  text inside math blocks
- **Very large files** (> 2000 lines): may require special handling
- **Domain-specific terminology**: provide a glossary for best results
- **Poetry / literary text**: LLM translation quality varies; consider
  human review

## Examples

Translate English calculus notes to Chinese:
```
> /markdown-translate
Source: en, Target: zh
Files: Ses1_enhanced.md
→ Ses1_enhanced_zh.md
```

Batch translate to Japanese:
```
> /markdown-translate
Source: en, Target: ja
Files: Ses*_enhanced.md
→ Ses1_enhanced_ja.md, Ses2_enhanced_ja.md, ...
```
