---
name: skill-aligner
emoji: ⚖️
description: The ultimate System Constitution Enforcement Scanner. Audits all OpenClaw skills perfectly against the Gemma L1 Constitution, detecting legacy paths, bloated downloads, and hallucinated logic. Zero tolerance.
metadata: { "openclaw": { "requires": { "bins": ["python3"] } } }
---

# ⚖️ Skill Aligner (宪兵审计团)

## Overview

The `skill-aligner` is a highly-physical, zero-hallucination automated auditing tool. Its sole purpose is to forcibly align all `openclaw/skills/` documents with the **05_SYSTEM_AUDIT_PROTOCOL**. It accomplishes this by unleashing regex-driven Python probes (`audit.py`) across the entire skill base to catch specific structural or semantic violations of the `GEMINI_L1_CONSTITUTION`.

**DO NOT attempt to "read files and check manually" when updating the system. ALWAYS execute the `audit_skills` tool first to get a deterministic failing report.**

## Target Violations (The Audit Blacklist)

When run, the tool strictly scans for:
1. **[Heavy Asset Visa Check]**: Any tool downloading models/datasets (like `kaggle`, `huggingface`) that fails to physically write `[L1 Constitution Block]` to block Git Repo bloat.
2. **[Ghost Path Eradication]**: Any tool referencing the eradicated archaic Linux paths like `[/roo` + `t/research_bot/]` instead of the canonical `~/workspace/projects_core/`.
3. **[Anti-Hallucination]**: Any occurrence of "requests", "BeautifulSoup", or "cat >" in skills where native system proxies stand (e.g., `academic-search` must be used instead of building scrapers).

## Action Toolkit

### `audit_skills`
Scans all `SKILL.md` files under `~/Documents/projects/openclaw/skills/` against the constitution blacklist.

**Usage:**
```bash
python3 scripts/audit.py
```

### Remediation Protocol

If `audit.py` returns `[FAILED]`, you (the Agent) MUST:
1. Open the violating `SKILL.md` using the `view_file` tool.
2. Use `replace_file_content` to surgically remove the bad path or inject the missing `[L1 Constitution Block]`.
3. Re-run `audit_skills` until the output is globally `[ALL PASSED]`.

---

> *"Under the 5th Law, we trust the code, not the promise."*
