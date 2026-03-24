---
name: robust-latex
description: Bulletproof LaTeX compilation skill with zero-error log scanning, engine auto-detection, and sandbox character drop prevention.
---

# Robust LaTeX Compilation

## Overview

The `robust-latex` skill completely supersedes all previous fragmented legacy LaTeX tools (such as `latex_compiler.py`, `latex_injector.py`, and custom shell scripts). It is the **single source of truth** for all OpenClaw agents, including ResearchBot and MyAI, when compiling `.tex` documents to PDF.

## Core Mandates

Agents handling LaTeX tasks **must** adhere strictly to the following execution contract:

1. **Do not use native OS commands directly.** Never invoke `pdflatex` or `xelatex` using raw terminal commands. The target host machine might be missing critical font databases (e.g., Fandol on Mac 03) or have restrictive sudo rules.
2. **Always use the `latex_tool.py` wrapper.**
   The tool handles engine selection (`pdflatex` vs `xelatex`), sequential `bibtex` passes, and crucially, an aggressive deep-scan of the generated `.log` file to catch silent `Missing character` drops that the native compiler ignores.
3. **The Overflow Prevention Rule.** All TikZ graphics, large tables, or wide code blocks MUST be wrapped in `\resizebox{\textwidth}{!}{...}` or structured in equivalent boundary containers to prevent page margin overflows.
4. **Mandatory Artifact Storage.** The generated `.tex` source and final `.pdf` output must reside in the working artifact directory where the user can access them easily.

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

## Rendering Verification (Mandatory)

After successful compilation (Exit Code 0), the agent **must** perform visual rendering verification before delivering the PDF to the user. This catches issues that log scanning alone cannot detect (e.g., layout overflow, misaligned tables, font substitution artifacts).

### Verification Steps

1. **Open PDF in browser** using browser_subagent: `file:///path/to/output.pdf`
2. **Capture screenshots** of at least:
   - Cover/title page (check CJK text, special symbols)
   - Table of contents (check section titles)
   - A page with tables (check alignment, borders)
   - A page with figures (check image rendering)
3. **View screenshots** via `view_file` to visually confirm rendering
4. **Fix and recompile** if any issues are found

### Common CJK Font Issues on macOS

| Font                | Status            | Notes                                    |
| ------------------- | ----------------- | ---------------------------------------- |
| `STSong`            | ⚠️ Incomplete     | Missing glyphs for some CJK characters   |
| `Songti SC`         | ✅ Recommended    | Full coverage, has Bold variant          |
| `Heiti SC`          | ✅ Recommended    | Sans-serif, has Medium variant           |
| `Kaiti SC`          | ✅ Recommended    | Monospace alternative                    |
| `Noto Serif CJK SC` | ✅ Alternative    | Google Noto family                       |
| `Helvetica Neue`    | ⚠️ No math/arrows | Use `\rmfamily` for `$\rightarrow$` etc. |

### Recommended xeCJK Configuration

```latex
\setCJKmainfont{Songti SC}[BoldFont={Songti SC Bold}]
\setCJKsansfont{Heiti SC}[BoldFont={Heiti SC Medium}]
\setCJKmonofont{Kaiti SC}
```

> **Rule:** Never deliver a LaTeX PDF without visual verification. A clean log does not guarantee correct rendering.
