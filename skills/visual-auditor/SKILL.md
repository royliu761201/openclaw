---
name: visual-auditor
description: A Hybrid PDF Audit Protocol combining mathematical log parsing with VLM (Vision-Language) subagent verification to ensure top-tier NLP typography compliance.
---

# `visual-auditor` Skill (Hybrid Typography Check)

The `visual-auditor` skill enforces the absolute typographical rigidness of scientific publishing for Double-Blind ACL/NeurIPS maneuvers. It mathematically zero-outs margin overflows and prevents visually jarring font distortions before taking a final Vision-Language heuristic check.

## 🧭 The V6 Hybrid Audit Doctrine

Future agents MUST execute this precise 3-phase cascade whenever preparing a final LaTeX PDF render for the user. Do not blindly trust an `Exit Code 0` from the compiler.

### Phase 1: The Engine-Level Diagnostic (Log Parsing)
You must directly extract physical margin breaches from the compiler's memory:
- Execute `grep_search` on `main.log` targeting the exact regex `Overfull|Warning|undefined`.
- Any `Overfull \hbox` indicates a table or paragraph has penetrated the column gutter.
- Any `Warning: Citation undefined` indicates a severed hyper-link (Ghost Reference mapping to `[?]`).

### Phase 2: The Zero-Resize Doctrine (Anti-Scaling)
If Table geometries trigger an `Overfull \hbox`, you are **ABSOLUTELY PROHIBITED** from using the `\resizebox{\columnwidth}{!}{...}` scaling cheat. Scaling tables arbitrarily destroys the formal font size constraints (11pt/10pt) enforced by the ACL double-blind system.
- **Remediation**: Remove `\resizebox`. 
- **Organic Compression**: Introduce `\small` or `\footnotesize`, tighten `\setlength{\tabcolsep}{3pt}`, or upgrade the environment to `\begin{table*}` (Double-Column Span).

### Phase 3: Vision-Language Verification
Once the mathematical log is perfectly silent (0 `Overfull` anomalies), you must verify the aesthetic spacing using the Agentic physical eye:
- Spawn the `browser_subagent`.
- Navigate to `file:///path/to/project/main.pdf`.
- Command the subagent to rapidly scroll the document vertically, specifically verifying that the CJK macros (`xeCJK`) render perfectly (no black squares) and that the text block proportions sit elegantly within the human visual cortex limits.
