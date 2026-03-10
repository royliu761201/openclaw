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

When the user issues a termination or archival command (e.g., "close"):
First, commit your completed local `task.md` checkmarks back to the SSoT:

```bash
python3 $HOME/workspace/.local_skills/workspace/scripts/sync_global.py \
  --global_board /Users/roy-jd/workspace/docs/system_core/memory_core/01_GLOBAL_TASK_BOARD.md \
  --commit
```

Then, legally physically commit your temporary session artifacts into the persistent vault.

```bash
python3 $HOME/workspace/.local_skills/workspace/scripts/archive.py --source $BRAIN_DIR
```

## ⚠️ CONSTITUTIONAL ANCHORS

- **Zero Content Pollution**: Never inject native LLM chat artifacts back into the pure `01_GLOBAL_TASK_BOARD.md` SSoT file. The board must remain clean markdown links only.
- **Archive Verification**: You cannot report a successful "Close" or "Archive" unless the `archive.py` script exits with code `0`.
