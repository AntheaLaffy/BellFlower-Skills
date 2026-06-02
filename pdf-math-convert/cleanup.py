#!/usr/bin/env python3
"""
Generic cleanup script for docling-produced Markdown.

Fixes OCR artifacts that are independent of the specific math domain:
  - Ligature breaks (fi rst, fi nd, etc.)
  - Unicode replacement characters
  - Spaced-apart decimal numbers (0 . 75 -> 0.75)
  - Greek letter wrapping (Delta in math mode)
  - Basic function notation (f(x) pattern wrapping)
  - Broken docling tables
  - Whitespace normalization

Usage:
  python3 cleanup.py <input.md>

Output: <input>_clean.md
"""

import re
import sys
from pathlib import Path


def cleanup(input_path: str) -> str:
    with open(input_path) as f:
        text = f.read()

    # === 1. Ligature fixes (docling splits common ligatures) ===
    LIGATURES = [
        ("fi rst", "first"),
        ("fi nd", "find"),
        ("Fi nd", "Find"),
        ("fi fth", "fifth"),
        ("fi nal", "final"),
        ("fi nite", "finite"),
        ("fi eld", "field"),
        ("fi gure", "figure"),
        ("fl uid", "fluid"),
        ("fl ow", "flow"),
    ]
    for old, new in LIGATURES:
        text = text.replace(old, new)

    # Unicode replacement character (U+FFFD)
    text = text.replace("�", "'")  # most often it's a prime/apostrophe

    # === 2. Number spacing: "0 . 75" -> "0.75" etc. ===
    # Match common patterns where docling inserts spaces around decimal points
    text = re.sub(r"(\d) \. (\d)", r"\1.\2", text)
    # Also handle negative: "-0 . 75" -> "-0.75"
    text = re.sub(r"-(\d) \. (\d)", r"-\1.\2", text)

    # === 3. Greek Delta: standalone ∆/Δ in text -> $\Delta$ ===
    # Only wrap when it's a math symbol (followed by space+letter or equals)
    text = re.sub(r"(?<!\$)\b(∆|Δ)\s*(?=[xyzftm]\b|=|\\|\d)", r"$\\Delta$ ", text)
    # Also standalone ∆ after newline (docling layout artifact)
    text = re.sub(r"\n(∆|Δ)\n", r"\n$\\Delta$\n", text)

    # === 4. Basic function notation wrapping ===
    # Pattern: "f ( x )" -> "$f(x)$" (when it's clearly math notation)
    # Only when f is followed by space-parenthesis pattern (not in prose like "function of ( x )")
    text = re.sub(r"\bf \( (x[^)]*|t[^)]*) \)", r"$f(\1)$", text)

    # === 5. Remove broken docling tables ===
    # Docling sometimes produces tables where all columns are crammed into one cell
    # Pattern: rows like "| - 0 . 50 - 0 . 25 0 . 25 0 . 50 | - 0 . 88 ... |"
    broken_table_pattern = re.compile(
        r'\| - \d+ \. \d+ .*? \| - \d+ \. \d+ .*? \|\n',
        re.MULTILINE,
    )
    # Only remove if it looks like a multi-value crammed cell
    text = re.sub(
        r'\| [-\d] \. \d\d [-\d] \. \d\d [-\d] \. \d\d [-\d] \. \d\d \| [-\d] \. \d\d .*? \|\n',
        '',
        text,
    )

    # === 6. Whitespace normalization ===
    # Collapse multiple spaces (but not newlines)
    text = re.sub(r" +", " ", text)
    # Collapse >2 consecutive blank lines to max 2
    text = re.sub(r"\n{4,}", "\n\n\n", text)

    # Remove trailing whitespace on lines
    text = re.sub(r" +\n", r"\n", text)

    # Fix "the the" / "a a" typos
    text = re.sub(r"\b(the|a|in|on|to|is) \1\b", r"\1", text)

    return text


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <input.md>", file=sys.stderr)
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if not input_path.exists():
        print(f"Error: {input_path} not found", file=sys.stderr)
        sys.exit(1)

    # Derive output path
    stem = input_path.stem
    if stem.endswith("_raw"):
        output_name = stem.replace("_raw", "_clean") + ".md"
    else:
        output_name = stem + "_clean.md"
    output_path = input_path.parent / output_name

    print(f"Cleaning: {input_path}  ->  {output_path}")

    text = cleanup(str(input_path))
    with open(output_path, "w") as f:
        f.write(text)

    placeholders = text.count("formula-not-decoded")
    print(f"Done. Lines: {text.count(chr(10))}")
    if placeholders:
        print(f"Remaining 'formula-not-decoded' placeholders: {placeholders}")
        print(f"These will need LLM semantic repair (Phase 3).")


if __name__ == "__main__":
    main()
