---
name: paper-crafter
description: A CI/CD automation and quality assurance skill for generating Top-Tier (NeurIPS/ICLR) LaTeX manuscripts seamlessly without formatting errors or orphan citations.
---

# 🛠️ Paper-Crafter (The Archivist & Critic)

The Paper-Crafter skill enforces the absolute rigidness of scientific publishing. It guarantees 0 Overfull Hboxes, 0 Orphan Citations, and prevents common LLM generation mistakes (like Markdown leaking into LaTeX).

## Available Scripts

### 1. `lint_manuscript.py` 
A rigorous linter for LaTeX manuscripts.
**Usage**: `python openclaw/skills/paper-crafter/scripts/lint_manuscript.py <path_to_tex_dir>`

**Capabilities**:
- **Format Hygiene**: Raises exceptions if `**` or `__` markdown syntax leaks into `.tex` files.
- **Citation Hygiene**: Scans `.tex` against the root `.bib` file to flag "Orphan Citations" (cited but missing bibliography entry or vice versa).
- **Structure Enforcement**: Enforces that `algorithm` environments exist for formal definitions.

*(More scripts like `style_polisher.py` for Anti-ZeroGPT and `visual_reviewer.py` for DPI checks are actively being drafted.)*
