---
name: paper_drafting
description: Automated downstream pipeline for academic paper formatting, style polishing, and cross-referencing visual metrics against experiments.
---

# Paper Drafting Skill

The `paper_drafting` skill provides the downstream pipeline for taking raw scientific experimental data from the Big 4 dashbards and transforming it into submission-ready publication materials.

## Available Tools

### 1. Style Polisher (`scripts/style_polisher.py`)
Automatically reviews LaTeX and Markdown drafts for academic tone, structural flow, SSoT consistency, and formatting errors.

**Usage:**
```bash
python3 ~/openclaw/skills/paper_drafting/scripts/style_polisher.py --paper PATH_TO_TEX_OR_MD
```

### 2. Visual Reviewer (`scripts/visual_reviewer.py`)
Cross-references the paper's quantitative claims and Figure descriptions against the live `00_CORE_EXPERIMENTS_DASHBOARD.md` to ensure no hallucinations or stale data are published.

**Usage:**
```bash
python3 ~/openclaw/skills/paper_drafting/scripts/visual_reviewer.py --paper PATH_TO_TEX_OR_MD --board PATH_TO_DASHBOARD
```

## Anti-Hallucination Protections
This skill operates strictly under L1 Rule 21 and the Absolute Axiom. All metrics must be proven by SSoT, and it will emit hard errors if a paper draft claims a metric that exceeds the authorized thresholds in the Core Experiments Dashboard.
