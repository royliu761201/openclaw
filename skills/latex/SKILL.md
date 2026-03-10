---
name: robust-latex
description: Bulletproof LaTeX compilation skill with zero-error log scanning, engine auto-detection, and sandbox character drop prevention.
---

# Robust LaTeX Compilation

## Overview

The `robust-latex` skill completely supersedes all previous fragmented legacy LaTeX tools (such as `latex_compiler.py`, `latex_injector.py`, and custom shell scripts). It is the **single source of truth** for all OpenClaw agents, including ResearchBot and MyAI, when compiling `.tex` documents to PDF.

## Core Mandates

Agents handling LaTeX tasks **must** adhere strictly to the following execution contract:

1.  **Do not use native OS commands directly.** Never invoke `pdflatex` or `xelatex` using raw terminal commands. The target host machine might be missing critical font databases (e.g., Fandol on Mac 03) or have restrictive sudo rules.
2.  **Always use the `latex_tool.py` wrapper.**
    The tool handles engine selection (`pdflatex` vs `xelatex`), sequential `bibtex` passes, and crucially, an aggressive deep-scan of the generated `.log` file to catch silent `Missing character` drops that the native compiler ignores.

## Execution Contract

To compile a project:

```sh
python ~/openclaw/skills/latex/scripts/latex_tool.py <path_to_main.tex>
```

### Interpretation of Results

- **Success (Exit Code 0):** The PDF is securely generated, and the log is confirmed 100% clean. The agent may freely return the resulting PDF to the user and mark the task as complete.
- **Failure (Exit Code 1):** The terminal output will specify exactly why the compilation was rejected.
  - If the rejection involves `Missing character:`, the agent **must** immediately investigate the required fonts or inject offline bundled dependencies before attempting another compilation. Never ignore these warnings.
  - If the rejection involves `! LaTeX Error`, the agent must parse the exact error and modify the `.tex` syntax accordingly.

## Internal Architecture

- **Engine Auto-Detection:** The script reads the target `.tex` file header. If macros like `xeCJK` or `ctexart` are present, it dynamically switches to the `xelatex` pipeline to handle CJK and massive font sets.
- **The Master Gate:** The tool will refuse to exit cleanly if it detects _any_ silent character drops in `main.log`, forcibly escalating silent LaTeX failures into hard CI/CD blockers.
