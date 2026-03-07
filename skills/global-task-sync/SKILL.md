---
name: global-task-sync
description: Unified Task Synchronization & Methodology skill for Managing Memory (SSoT) and Process (PDCA).
---

# Global Task Sync (The Memory & methodology Engine)

## Objective

This skill is the central nervous system of OpenClaw. It ensures that every session starts with the latest global context and ends by solidifying experience into the Single Source of Truth (SSoT).

## ⚔️ The Iron Rules (PDCA Methodology)

1.  **Experience is Toolification (经验固化即工具化)**: Any retrospective or process discovery MUST eventually be encoded into a Skill or Tool.
2.  **No Cognitive Orbs (禁留孤立文档)**: Do not leave "floating" markdown files in `docs/` or `workspace/`. If it's a rule, it belongs in a Skill.
3.  **SSoT Integrity**: Git is the only truth. All `task.md` progress MUST be merged via this skill.

## Lifecycle Protocols (Agent Instructions)

### 1. 🅿️ Phase 1: Loading Protocol (Mem-Wakeup)

At the start of every session, the Agent MUST initialize the session's task board using the following protocol:

1.  **Read Global Board**: Call `view_file` on `01_GLOBAL_TASK_BOARD.md` to get the latest mission state.
2.  **Create Shard**: Call `write_to_file` to create a `task.md` in the current session's brain directory.
3.  **Inherit Content**: Exact-copy the content of the global board into the session `task.md`.

### 2. ㄉ Phase 2: Execution Protocol (Status Update)

During work, the Agent MUST maintain the session's `task.md`:

-   Mark items as `[/]` when in progress.
-   Mark items as `[x]` when verified complete.

### 3. Ⓒ Phase 3: Merging Protocol (SSoT Update)

Before concluding a task or session, the Agent MUST merge results back to the global board. 
**[Anti-Hallucination Strict Rule]**: The Agent MUST NOT blindly paste huge chunks of text across boards. You must act like a precise patch engine using `replace_file_content` targeting explicit line numbers.

1.  **Read Both**: Call `view_file` on both the session `task.md` and `01_GLOBAL_TASK_BOARD.md`.
2.  **Diff & Discover**: 
    - Identify lines in the global board that are now `[x]` in the session.
    - Identify NEW tasks added to the session `task.md` that are not in the global board.
3.  **Apply Merge via `replace_file_content`**: 
    -   **Target precision**: Only edit the localized line chunks inside `01_GLOBAL_TASK_BOARD.md` that need status switching (`[ ]` -> `[x]`). Do not update the whole file at once.
    -   **New Tasks**: Insert newly discovered tasks precisely into the correct quadrant without destructing surrounding text.

### 4. Ⓐ Phase 4: Solidification Protocol (ACT)

Any new insights, rules, or retrospective findings related to system behavior or methodology MUST NOT just be added as text to the global board. The Agent MUST physically inject these rules into the immune system (L1, L2, L3) by explicitly executing the **`solidify`** skill.
