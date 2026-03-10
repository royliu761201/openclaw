---
name: shared
description: [System Module] Internal shared utilities (e.g., email_tool.py). AGENTS MUST NOT MOUNT OR INVOKE THIS DIR DIRECTLY.
---

# `shared` (System Module)

⚠️ **WARNING: AGENT COGNITIVE BARRIER** ⚠️

This directory is an internal dependency pool containing shared utility scripts (like the unified `email_tool.py`) used by other high-level skills (e.g., `126-email`, `school-email`).

## **RULES OF ENGAGEMENT (L1 AXIOM)**

1. **DO NOT INVOKE**: This is NOT an executable L2 Skill. You are **ABSOLUTELY FORBIDDEN** from attempting to "mount", "run", or "load" the `shared` name as an independent capability in your toolkit.
2. **NO MODIFICATION**: Unless explicitly commanded by the Boss to refactor underlying shared infrastructure, do not modify files inside this folder.
3. **ONLY USE VENDORED SKILLS**: If you need to send an email, use the official `126-email` or `school-email` skills physically installed. They internally wrap these shared resources.

_This file exists purely as an anti-hallucination payload to prevent Agent scanning errors._
