---
name: system
description: [System Daemon Layer] Foundational OS watchdogs and probes. AGENTS MUST NOT MOUNT OR INVOKE THIS DIR DIRECTLY.
---

# `system` (System Daemon Layer)

⚠️ **WARNING: AGENT COGNITIVE BARRIER** ⚠️

This directory houses the foundational system daemons and watchdogs (e.g., `watchdog_claws.py`) for OpenClaw's node architecture. It is NOT a user-facing skill.

## **RULES OF ENGAGEMENT (L1 AXIOM)**

1. **PROHIBITION**: You are **ABSOLUTELY FORBIDDEN** from attempting to "mount", "run", or "load" the `system` name as an independent L2 Skill.
2. **HANDS OFF**: The scripts within are managed by PM2 host controllers and system `crontab`. Unless debugging a catastrophic node failure explicitly directed by the Boss, do not touch.
3. **NO HALLUCINATION**: If the Boss asks you to check system health, use the designated `healthcheck` or `cluster-monitor` skills, NOT this internal directory.

_This file exists purely as an anti-hallucination payload to prevent Agent scanning errors._
