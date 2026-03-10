---
name: workspace
description: The core gatekeeper skill for the OpenClaw SSoT (Single Source of Truth). Strictly handles global task reading, artifact tracking, and session archival.
---

# `workspace` Skill

The `workspace` skill governs the top-level cognitive state of the Agent. It enforces the rules defined in `~/workspace/.clinerules` regarding reading global tasks and permanently archiving session brains.

> **[L1 Architecture Note]**: As of V7, cluster monitoring (`gpu_status_board`, `cluster_net`) and secret distribution (`sync_secrets`) have been strictly decoupled into the `cluster-monitor` and `vault-keeper` skills respectively. Do not invoke `workspace` for those tasks.

## ⚡️ TRIGGER RULES

You MUST execute this skill FIRST whenever:

- The user asks ANY question about tasks, eg: "check global board", "check tasks", "what's next", "下一步做什么", "看大盘", "任务".
- The user asks ANY question about tasks, eg: "check global board", "check tasks", "what's next", "下一步做什么", "看大盘", "任务".
- You need to leave a message, note, or error stack trace for another Agent session (`--board-write`).
- You need to view or present ANY non-session global text document (.md files) on the SSoT (Global Board, PDCA files, Rules, Idea Lists).
- You enter a new project or start a session and need context.
- The user explicitly issues "close", "archive" (Archive/Close) to shutdown the current session.

## 🛠️ USAGE (Pure MD-Driven SOP)

### 1. Reading the Global Board (Task Synchronization)

When the user specifies a global task (e.g. "Work on global task CaLaM"), isolate that task from the SSoT board:

```bash
python3 $HOME/workspace/.local_skills/workspace/scripts/sync_global.py \
  --global_board /Users/roy-jd/workspace/docs/system_core/memory_core/01_GLOBAL_TASK_BOARD.md \
  --checkout "CaLaM"
```

### 2. Creating a new Global Task

When the user explicitly creates a task (e.g., "Create a global task to investigate Node 02 speed"):

```bash
python3 $HOME/workspace/.local_skills/workspace/scripts/sync_global.py \
  --global_board /Users/roy-jd/workspace/docs/system_core/memory_core/01_GLOBAL_TASK_BOARD.md \
  --create "Investigate Node 02 speed" --category "System Infrastructure"
```

### 3. Archiving the Session Brain (Closure Protocol)

**⚠️ THE DEATHBED CONFESSION RULE ⚠️**
Before you execute the close/archive protocol:
If you have any UNFINISHED tasks `[ ]` in your local `task.md` or if your exploration ended in an unresolved error, you MUST use `--board-write` (see Section 4) to leave a "Deathbed Confession" (a short summary of what blocked you or what to do next) on the global board for the next Agent. Do not die in silence!

When you are explicitly ordered to terminate or archive (e.g., "close"):
First, you MUST sync with the remote Git network to prevent cross-node brain split, then commit your completed local `task.md` checkmarks back to the SSoT, and push:

```bash
cd $HOME/workspace && git pull --rebase --autostash --strategy-option=theirs && \
python3 $HOME/workspace/.local_skills/workspace/scripts/sync_global.py \
  --global_board /Users/roy-jd/workspace/docs/system_core/memory_core/01_GLOBAL_TASK_BOARD.md \
  --commit && \
git commit -am "chore(board): sync global task progress" && git push
```

Then, legally physically commit your temporary session artifacts into the persistent vault. The script will output a `Vault Receipt` anchor.

```bash
python3 $HOME/workspace/.local_skills/workspace/scripts/archive.py --source $BRAIN_DIR
```

**REPORTING**: You must explicitly report the `Vault Receipt` (e.g., `session_20260310_b3f9...`) to the user as your final act before shutdown.

### 4. Cross-Session Whiteboard (Shared Memory)

To leave an ephemeral note, stack trace, or warning for yourself in another session or for another Agent working on the same task, write to the whiteboard block of a specific task:

```bash
python3 $HOME/workspace/.local_skills/workspace/scripts/sync_global.py \
  --global_board /Users/roy-jd/workspace/docs/system_core/memory_core/01_GLOBAL_TASK_BOARD.md \
  --board-write "CaLaM" "Discovered CUDA OOM error; falling back to batch_size 4."
```

When a task is successfully resolved or the whiteboard is too cluttered, clear it:

```bash
python3 $HOME/workspace/.local_skills/workspace/scripts/sync_global.py \
  --global_board /Users/roy-jd/workspace/docs/system_core/memory_core/01_GLOBAL_TASK_BOARD.md \
  --board-clear "CaLaM"
```

### 5. Viewing & Grooming the Global Board

- **Viewing (The Artifact Projection)**:
  **CRITICAL RULE: DO NOT use `cat` or `view_file` to read the global board or any other SSoT Markdown files if the user is asking to see them.** Raw markdown text has a terrible visual experience for the Boss.
  Instead, you MUST use the Universal Projection mechanism:

  ```bash
  python3 $HOME/workspace/.local_skills/workspace/scripts/project.py \
    --source /Users/roy-jd/workspace/docs/system_core/memory_core/01_GLOBAL_TASK_BOARD.md \
    --brain_dir $BRAIN_DIR
  ```

  After running this, the script will output an artifact anchor path (e.g. `GLOBAL_TASK_BOARD_PROJECTION.md`). You **MUST** immediately invoke the `notify_user` system tool, passing this generated `.md` file in the `PathsToReview` array. This triggers the native UI to render a rich interactive dashboard for the Boss.

- **Grooming (Clean up)**: If the user asks you to "clean the board", "archive tasks", or "review tasks":
  1. DO NOT try to use a script. You are intelligent enough to do it manually.
  2. Read `01_GLOBAL_TASK_BOARD.md` in full (for your own eyes only, `view_file` is fine here).
  3. Identify old, closed tasks `[x]` that have been successfully integrated and are taking up space.
  4. Manually cut these completed tasks from the active sections.
  5. Paste them at the bottom under the `## 🗄️ Archived (Max 3-5)` section.
  6. **CUTOFF RULE**: The `Archived` section must never contain more than 5 items. If merging new closed tasks exceeds 5, permanently delete the oldest ones.
  7. Commit directly to git: `cd $HOME/workspace && git add docs/system_core/memory_core/01_GLOBAL_TASK_BOARD.md && git commit -m "chore(board): groom and archive completed global tasks"`

### 6. Universal SSoT Projection (Any Document)

This Projection power is not limited to the Global Board. If the user asks to see the "Idea List", a "PDCA tracker", or any other permanent `.md` file, you MUST use `project.py` in the exact same way to cast it into a rich Artifact UI panel.

## ⚠️ CONSTITUTIONAL ANCHORS

- **Zero Content Pollution**: Never inject native LLM chat artifacts back into the pure `01_GLOBAL_TASK_BOARD.md` SSoT file. The board must remain clean markdown links only.
- **The Boss Directive Echo**: When the Boss highlights text on an Artifact Projection and leaves a Comment, you must physically weave that Comment back into the original SSoT source file you projected from, prefixing it with `> [!Boss Directive]`.
- **Archive Verification**: You cannot report a successful "Close" or "Archive" unless the `archive.py` script exits with code `0`.
