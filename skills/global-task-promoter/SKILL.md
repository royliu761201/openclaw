---
name: global-task-promoter
description: A built-in recovery mechanism to locate and restore the most recent task board (task.md) from the workspace or brain directory into the current session context.
---

# Global Task Promoter (Memory Wakeup Skill)

## Objective

This skill allows the agent to immediately restore its cognitive context upon starting a new session or encountering a system crash. It locates the most up-to-date `task.md` or `MASTER_INDEX` from the project's rigid storage (`workspace/docs` or `.gemini/antigravity/brain/*`).

## Usage

When the agent starts a new session and lacks the current task context, it MUST read this skill and execute the attached probing script to find and read the latest task state.

## Execution Steps:

1. Agent realizes it lacks the `task.md` or current project context.
2. Agent reads this `SKILL.md`.
3. Agent executes the native helper script via legal tool: `python3 <DIR_OF_THIS_SKILL>/scripts/restore_context.py` (Agent MUST dynamically resolve `<DIR_OF_THIS_SKILL>` to the absolute directory path where this `SKILL.md` resides).
4. The script will output the absolute path to the most recent `task.md`.
5. The agent MUST then use the native `view_file` tool to read the contents of that `task.md` and resume operations.
