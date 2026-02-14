---
name: latex
description: Compile LaTeX documents to PDF.
metadata: { "openclaw": { "requires": { "bins": ["pdflatex"] } } }
---

# LaTeX Compiler

Wraps `pdflatex` to compile academic papers.

## Tools

### `compile_tex`
Compile a `.tex` file to PDF.

- **file** (string, required): Path to the `.tex` file.
- **clean** (boolean, optional): Clean auxiliary files after build (default: true).

## Usage
Run the python wrapper to compile and clean up auxiliary files:

```bash
python skills/latex/scripts/compile.py workspace/paper.tex --clean
```

Or raw command (not recommended):
```bash
pdflatex -interaction=nonstopmode -output-directory=workspace/papers my_paper.tex
```
