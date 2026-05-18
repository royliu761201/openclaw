---
name: ooxml-to-latex
description: High-fidelity converter from Word (OOXML) documents to LaTeX PDFs, preserving absolute layout and element structures without abstraction loss.
homepage: local
metadata:
  {
    "openclaw":
      {
        "emoji": "📜",
        "requires": { "bins": ["python3", "xelatex", "pdftotext"] },
        "install":
          [
            {
              "id": "texlive",
              "kind": "system",
              "bins": ["xelatex"],
              "label": "Ensure TeX Live (xelatex) is installed",
            },
            {
              "id": "poppler",
              "kind": "system",
              "bins": ["pdftotext", "pdftoppm"],
              "label": "Ensure poppler is installed for verification",
            }
          ],
      },
  }
---

# ooxml-to-latex

A robust methodology and toolset for parsing raw Word (OOXML) documents and converting them into pixel-perfect LaTeX PDFs without losing layout, text formatting, or table structure fidelity.

## Philosophy

Word is a forgiving WYSIWYG editor; LaTeX is a strict typesetting engine. Do **not** use high-level abstraction libraries like `python-docx` for this. You must read the raw `document.xml` using `xml.etree.ElementTree` to capture exact layout values, and use a rigid "AST" translation strategy.

## Core Rules & Execution

1. **Table Matrix Reconstruction**:
   - Word evaluates table merges explicitly via `gridCol`, `gridSpan`, and `vMerge`.
   - Never trust the `gridSpan` value blindly. If a row has only 1 cell, always enforce it to span `col_count - c_grid`. Word's XML will often lazily leave `gridSpan` at an arbitrary number causing phantom empty columns in LaTeX `tabularray`.
   - Use the LaTeX package `tabularray` (environment `tblr`).

2. **Absolute Spacing & Indentation**:
   - **NO GLOBAL `\parindent`**: Never use a global `\setlength{\parindent}{...}` command. Many Word layouts contain mixed indentations.
   - Read the `<w:ind>` tag (specifically `firstLineChars`) for *every single paragraph*. Inject an explicit `\hspace*{...}` or `\noindent` at the start of the LaTeX string.

3. **Multi-Column Alignment Detection ("Magic Hacks")**:
   - Word users often align signatures by using spaces. Detect a paragraph split by `\s{3,}` into distinct, short (≤20 chars) chunks and convert it into `\makebox[width][l]{...}` chunks evenly spaced.

4. **Text Overflows & Pacing**:
   - Wrap long digit strings ($\ge 10$) in `\seqsplit{...}`.
   - Long text inside wide merged cells will bleed out of boundaries. Wrap them in a `\parbox{...}`.
   - Inject `\linespread{1.5}\selectfont` and `\justifying` inside complex `\parbox` table cells.

## Included Scripts

Located in `scripts/`:

### 1. `raw_docx2tex.py`
A highly-optimized OOXML parsing script that translates XML to LaTeX `ctexart` files (including image embedding and matrix table resolution).
```bash
python3 scripts/raw_docx2tex.py <input.docx> <output_dir>
```

### 2. `verify_conversion.py`
An automated QA pipeline checking text string preservation, layout metrics, page count estimation, and PDF image extraction.
```bash
python3 scripts/verify_conversion.py <input.docx> <converted.pdf> <report_dir>
```

Always use `verify_conversion.py` as the visual testing gate before delivering the final PDF.
