---
name: optimizer-triad
description: A Meta-Skill coordinating Antigravity, Codex, and Math Invariants to autonomously refactor and optimize Python models without corrupting physical laws (Triad Protocol).
---

# Optimizer-Triad Skill

## Overview
This meta-skill is triggered whenever the Boss requests "optimization", "parameter tuning", or "code speeding up". Optimization without boundaries leads to OOM massacres or "Silent Divergence" (AI masking NaNs with `nan_to_num` just to pretend the training succeeded).

This skill enforces the **Triad Orchestration Protocol** defined in `15_TRIAD_ORCHESTRATION_LAW.md`.

## Execution Workflow (Mandatory)

1. **Pre-flight Sandbox Check**
   - The Agent MUST switch to a non-production Git branch. (e.g., `git checkout -b opt_sandbox`).
2. **Setup Optimization Boundaries**
   - Identify the hardware (L20 / 4090) and exact physics target (e.g. "Do not break the `dt <= dx` CFL bound").
3. **Trigger Codex Headless Proxy**
   - Agents DO NOT write massive core training loop rewrites.
   - Invoke `codex exec "Optimize the loop in main.py, enforce TF32, add reentrant=False gradient checkpointing..." --json`
4. **The Science-First Audit (Crucial Step)**
   - Before accepting Codex's output, MUST run our static analyzer probe:
   ```bash
   python3 ~/openclaw/skills/optimizer-triad/scripts/audit_science_first.py /path/to/project/dir/
   ```
   - If the probe throws an `EXIT(1)` (Fake Math Masking), reject the optimization immediately.
5. **SSoT Sync & Queue Deployment**
   - Commit the changes and the `.codex_history`.
   - Dispatch to GPU ONLY using `vram-queue-manager` (which natively isolates `TRITON_CACHE_DIR`).
