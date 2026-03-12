---
name: skill-aligner
emoji: ⚖️
description: The ultimate System Constitution Enforcement Scanner. Audits all OpenClaw skills perfectly against the L1 Constitution, detecting legacy paths, bloated downloads, and hallucinated logic. Zero tolerance.
metadata: { "openclaw": { "requires": { "bins": ["python3"] } } }
---

# ⚖️ Skill Aligner (Constitution Integrity Audit)

## Overview

The `skill-aligner` is a highly-physical, zero-hallucination automated auditing tool. Its sole purpose is to forcibly align all `openclaw/skills/` documents with the **05_SYSTEM_AUDIT_PROTOCOL** and the new **9D Anti-Overengineering & Security Codex**. It accomplishes this by unleashing regex-driven Python probes (`audit_9d.py` and `audit.py`) across the entire skill base to catch specific structural or semantic violations of the `GEMINI_L1_CONSTITUTION`.

**DO NOT attempt to "read files and check manually" when updating the system. ALWAYS execute the `audit_9d` and `audit_skills` tools first to get a deterministic failing report.**

## The 9D Target Violations (The Audit Blacklist)

When run, the tool `audit_9d.py` strictly scans for:

1. **[DIM_1: NPM Bloat]**: Node.js/NPM artifacts (`.js`, `.mjs`, `package.json`) inside purely backend/Edge scraping skills. (Banned to prevent dependency hell on Node 02).
2. **[DIM_2: Wrapper Bloat]**: Calling naive CLIs via Python `subprocess` (e.g., bare `curl`) instead of native modules (like `requests` or `urllib`).
3. **[DIM_3/6: Hardcoded Secrets]**: Finding `Bearer token` or `API_KEY=...` mapped directly into scripts. All keys MUST stream purely from `~/.openclaw_env`.
4. **[DIM_4/5: Server Bloat]**: Building persistent MCP servers for simple HTTP tasks instead of direct scripts.
5. **[DIM_7: Destructive Ops]**: Finding raw `rm -rf` commands targeting non-`/tmp` directories (violates OpenClaw L0 Invulnerability Law). Must use `.Trash` isolation.
6. **[DIM_8: Shell Injection]**: Catching `subprocess.run(shell=True, ...)` which introduces lethal injection vulnerabilities. Must use array-based argument vectors.
7. **[DIM_9: Egress Control]**: Finding covert tracking, telemetry, or analytics endpoints inside scripts that report back without explicit OpenClaw SSOT verification.
8. **[Legacy 1: Ghost Path Eradication]**: Eradicating archaic paths like `[/roo` + `t/research_bot/]`.
9. **[Legacy 2: Anti-Hallucination]**: Arbitrary arXiv HTML scrapers without using `academic-search`.

## Action Toolkit

### `audit_9d_scanner` (The Supreme Executioner)

Scans all scripts (`.py`, `.sh`, `.mjs`) under `~/openclaw/skills/` against the 9D security and anti-bloat blacklist.

**Usage:**

```bash
python3 scripts/audit_9d.py
```

### `audit_skills` (Legacy Semantic Check)

### Remediation Protocol

If `audit.py` returns `[FAILED]`, you (the Agent) MUST:

1. Open the violating `SKILL.md` using the `view_file` tool.
2. Use `replace_file_content` to surgically remove the bad path or inject the missing compliance blocks.
3. Re-run `audit_skills` until the output is globally `[ALL PASSED]`.

---

> _"Under the 5th Law, we trust the deterministic probe, not the LLM promise."_
