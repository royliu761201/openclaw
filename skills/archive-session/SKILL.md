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

1.  **Step 0.1 (Sync)**: Agent MUST follow the `global-task-sync` "Merging Protocol" to push all session progress (completed tasks) and discoveries (new pending tasks) to `01_GLOBAL_TASK_BOARD.md`.
2.  **Step 0.2 (Solidify)**: If the session contained any debugging, feedback, or reflections, the Agent MUST execute the **`solidify`** skill to inject those lessons into the genetic memory (L1/L2/L3) before archiving.
3.  **Identify Path**: Identify the current session's Brain directory path (which holds `task.md`, etc.). Example: `~/.gemini/antigravity/brain/bd0d0...`
4.  **Physical Copy**: Execute the archiver script:
    `python3 ~/Documents/projects/openclaw/skills/archive-session/scripts/archive.py --source <CURRENT_SESSION_BRAIN_PATH>`
5.  **Git SSoT Push**: Once copied, the Agent MUST execute the Git Sync Law to push the newly archived session to the remote:
    ```bash
    cd ~/workspace && git add docs/session_archives/ && git commit -m "Archive: Session [Timestamp]" && git push
    ```
6.  The agent can then safely conclude the session or notify the boss.
