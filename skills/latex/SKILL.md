---
name: latex
description: Compile LaTeX documents to PDF with BibTeX support.
metadata: { "openclaw": { "requires": { "bins": ["pdflatex", "bibtex"] } } }
---

# LaTeX Compiler

Wraps `pdflatex` and `bibtex` to compile academic papers with full citation resolution.

## Tools

### `compile_tex`

Compile a `.tex` file to PDF using a multi-pass strategy (pdflatex -> bibtex -> pdflatex -> pdflatex).

- **file** (string, required): Path to the `.tex` file.
- **clean** (boolean, optional): Clean auxiliary files (.aux, .log, .bbl, etc) after build (default: true).
- **timeout** (integer, optional): Compilation timeout in seconds (default: 300).

## Usage

Run the python wrapper to compile and clean up auxiliary files:

```bash
python3 skills/latex/scripts/compile.py workspace/paper.tex --clean
```

This will automatically handle cross-references and bibliography generation.
