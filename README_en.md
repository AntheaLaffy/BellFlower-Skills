# Skills of 如月风铃

[en](README_en.md) | [zh](README.md) | [ja](README_ja.md)

## Introduction

These are some skill documents I wrote while experimenting with Claude Code, intended to address various problems I encountered during university life.

My computer runs Arch Linux, which may differ from yours. I hope these materials are helpful to you.

## Installation

There are no fancy steps: clone the entire repository and place it in Claude Code's `skills` folder.

You may also put it into a project's `skills` folder instead.

---

## Document processing

- `pdf-math-convert`: Convert math-heavy PDFs (lecture notes, textbooks, papers) into clean Markdown with proper LaTeX math and image handling
  > Features: 1. Auto-detect and fix formula placeholders 2. LaTeX math wrapping 3. Base64 embedded or referenced image mode 4. Batch parallel processing

- `markdown-translate`: Translate Markdown text with LLM, preserving LaTeX math, code blocks, images, and all formatting
  > Features: 1. Protects math/code/images from translation 2. Batch parallel translation 3. Post-translation integrity verification 4. Large file chunked translation

- `ocr-md-polish`: Fix formula rendering issues in OCR-generated Markdown (subscripts, exponent grouping, nested delimiters), clean up OCR-duplicated text near images
  > Features: 1. Fix missing subscripts (x0 → x_0) 2. Fix exponent grouping (e^x arctan(x) → e^{x \arctan(x)}) 3. Merge nested $...$ math mode 4. Tesseract OCR verification for dedup

- `md-to-pdf`: Convert Markdown with LaTeX math, images, and tables into a polished PDF. Pure Python — no Pandoc or LaTeX needed.
  > Features: 1. LaTeX → MathML rendering (fractions/limits/integrals/subscripts) 2. Local & Base64 image embedding 3. CJK font selection (LXGW WenKai / Noto Serif CJK SC / Noto Sans SC) 4. Batch conversion (multi-file / directory / glob) 5. Auto-dependency check, chains with ocr-md-polish for OCR→clean→PDF pipeline

## Programming help

- `find-docs`: Retrieve up-to-date documentation, API references, and code examples for any developer technology using the Context7 CLI
  > Features: 1. More current and accurate than training data 2. Version-specific queries 3. Support for major frameworks/libraries/tools

