---
name: latex
emoji: 📄
description: Compile LaTeX documents to PDF with BibTeX support in a single command.
metadata: { "openclaw": { "requires": { "bins": ["pdflatex", "bibtex", "python3"] } } }
---

# LaTeX Tool

A specialized CLI capability for compiling academic papers.

It handles the complex `pdflatex -> bibtex -> pdflatex -> pdflatex` multi-pass compilation cycle automatically, ensuring all cross-references and citations are resolved.

## Tools

### `compile`

Compile a .tex file to PDF using a multi-pass strategy (pdflatex -> bibtex -> pdflatex -> pdflatex).

- **file** (string, required): Path to the .tex file.
- **clean** (boolean, optional): Clean aux files after build (default: True).
- **timeout** (integer, optional): Compilation timeout in seconds (default: 300).

**Usage**:

```bash
skills/latex/scripts/latex_tool.py compile workspace/paper/main.tex
```

### `clean`

Manually clean up auxiliary files (`.aux`, `.log`, etc.) without compiling.

- **file** (string, required): Path to the .tex file (to identify base name).

**Usage**:

```bash
skills/latex/scripts/latex_tool.py clean workspace/paper/main.tex
```

## Troubleshooting

- **PDF not found**: If the command succeeds but no PDF is found, check if `pdflatex` output directory settings are correct (the script handles this automatically).
- **Undefined References**: The script will warn you if references are still undefined after 3 passes. Check your `.bib` file or keys.
