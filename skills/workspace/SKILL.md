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
- You need to leave a message, note, or error stack trace for another Agent session (`--board-write`).
- The user wants to see, check, review, or project ANY non-session global text document (.md files) on the SSoT (Global Board, PDCA files, Rules, Idea Lists).
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
If you have any UNFINISHED tasks `[ ]` in your local `task.md` or if your exploration ended in an unresolved error, you MUST use `--board-write` (see Section 4) to leave a "Deathbed Confession" on the global board for the next Agent. Do not die in silence!
**CRITICAL**: You are FORBIDDEN from writing vague generic messages like "It crashed." Your Deathbed Confession MUST strictly follow this dissection format:

- `[L0 尸检]`: What zombie background processes are left? Is the GPU memory cleared?
- `[L1 现场]`: What SSoT configuration/markdown file were you modifying when it failed?
- `[L3 阻击点]`: What specific code line, bash error, or dependency dimension blocked you?

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

- **Viewing (Implicit Artifact Projection)**:
  **CRITICAL RULE: DO NOT use `cat` or `view_file` to read the global board or any other SSoT Markdown files if the user is asking to look at them.** Raw markdown text has a terrible visual experience for the Boss.
  If the Boss says "check the board", "see the idea list", "look at frenet progress", or explicitly "project", you MUST implicitly default to the Universal Projection mechanism. YOU DO NOT NEED THE BOSS TO EXPLICITLY SAY "PROJECT":

  **🚨 THE ANTI-REDUNDANCY LAW (NO NATIVE ARTIFACT PROJECTION) 🚨**:
  You are STRICTLY FORBIDDEN from using `project.py` on any files that already live inside your current `$BRAIN_DIR` session folder (e.g., `task.md`, `walkthrough.md`, `implementation_plan.md`). These native artifacts already possess intrinsic UI rendering rights. If the user asks to see them, simply pass their absolute paths directly to the `PathsToReview` array of the `notify_user` tool! Do NOT create a redundant `_PROJECTION.md` for them!

  For truly external `.md` files, proceed with:

  For truly external `.md` files, proceed with:

  ```bash
  python3 $HOME/workspace/.local_skills/workspace/scripts/project.py \
    --source /Users/roy-jd/workspace/docs/system_core/memory_core/01_GLOBAL_TASK_BOARD.md
  ```

  **🚨 CRITICAL UI WAKEUP RULE (THE NEW ARCHITECTURE) 🚨**:
  The `project.py` script no longer writes the file to disk by itself. Doing so caused UI blank screen errors because it bypassed the artifact registry.
  Instead, `project.py` will print the massive string of the fully resolved Markdown text to the terminal `stdout`.

  You MUST capture this printed text from the terminal output, and then **explicitly use your `write_to_file` system tool** to write it to a new file named `[BASENAME]_PROJECTION.md`.
  **CRITICAL**: You MUST set `IsArtifact=True` and provide an `ArtifactMetadata` payload when calling `write_to_file`. This is the ONLY way the UI will correctly register and render the projection without black screens.

  Only after successfully writing the file via your tool, you **MUST** immediately invoke the `notify_user` system tool, passing the newly created absolute path in the `PathsToReview` array to cast it to the Boss.

- **Grooming (Clean up)**: If the user asks you to "clean the board", "archive tasks", or "review tasks":
  1. DO NOT try to use a script. You are intelligent enough to do it manually.
  2. Read `01_GLOBAL_TASK_BOARD.md` in full (for your own eyes only, `view_file` is fine here).
  3. Identify old, closed tasks `[x]` that have been successfully integrated and are taking up space.
  4. Manually cut these completed tasks from the active sections.
  5. Paste them at the bottom under the `## 🗄️ Archived (Max 3-5)` section.
  6. **CUTOFF RULE**: The `Archived` section must never contain more than 5 items. If merging new closed tasks exceeds 5, permanently delete the oldest ones.
  7. Commit directly to git: `cd $HOME/workspace && git add docs/system_core/memory_core/01_GLOBAL_TASK_BOARD.md && git commit -m "chore(board): groom and archive completed global tasks"`

### 6. Universal SSoT Projection (Any Document)

This Projection power is implicitly applied to ALL non-session documents. If the user asks to "see", "check", or "review" the "Idea List", a "PDCA tracker", or any other permanent `.md` file, you MUST seamlessly use `project.py` behind the scenes to cast it into a rich Artifact UI panel. Never serve raw text!

> **Reminder:** Again, never use this on your own `task.md` or `walkthrough.md`. Native artifacts bypass this script.

## ⚠️ CONSTITUTIONAL ANCHORS

- **Zero Content Pollution**: Never inject native LLM chat artifacts back into the pure `01_GLOBAL_TASK_BOARD.md` SSoT file. The board must remain clean markdown links only.
- **The Boss Directive Echo**: When the Boss highlights text on an Artifact Projection and leaves a Comment, you must physically weave that Comment back into the original SSoT source file you projected from, prefixing it with `> [!Boss Directive]`.
- **Archive Verification**: You cannot report a successful "Close" or "Archive" unless the `archive.py` script exits with code `0`.
