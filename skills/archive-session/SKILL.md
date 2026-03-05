---
name: archive-session
description: A mandatory mechanism to physically copy/archive the current session's temporary brain artifacts into the permanent workspace SSoT storage before closing a session.
---

# Archive Session (Memory Consolidator)

## Objective

The boss mandated that all session outputs, conversations, reflections, and generated documents must be automatically archived from the volatile `.gemini` brain directory into the rigid `workspace/docs` before a session wraps up. This skill automates that crucial rule from the L1 Constitution.

## Usage

The agent MUST call this skill as one of the final actions in a session, or periodically during long sessions when major milestones are hit.

## Execution Steps:

1. Identify the current session's Brain directory path (which holds `task.md`, etc.). Example: `~/.gemini/antigravity/brain/bd0d0...`
2. Execute the archiver script:
   `python3 ~/Documents/projects/openclaw/skills/archive-session/scripts/archive.py --source <CURRENT_SESSION_BRAIN_PATH>`
3. The script will copy the artifacts and output `✅ ARCHIVED_TO: ...`
4. The agent can then safely conclude the session or notify the boss.
