---
name: workspace
description: Use this skill to solidify and enforce the OpenClaw Workspace standards. It defines the authoritative path (~/workspace), the Git-as-SSoT law, and the "Toolification of Experience" principle. Use whenever context about workspace structure, sync rules, global tasks (全局任务), global task sync, or project isolation is needed.
---

# 🌐 OpenClaw Workspace (SSoT)

This skill serves as the **operational anchor** for all workspace activities. It transforms abstract rules into deterministic procedures.

## 💾 Authoritative Path
The ONLY legal path for code and mission-critical documentation on Node 01 is:
**`/Users/roy-jd/workspace`** (Shorthand: **`~/workspace`**)

> [!CAUTION]
> **Documents/workspace** is a legacy ghost path. Any operation within it violates the SSoT Law.

> [!IMPORTANT]
> **Rule 15: Workspace Invulnerability Law**: NEVER use `rm -rf` in this directory. 

## ⚔️ The Laws of the Workspace

1. **Git-Only Sync Law**: All cross-node synchronization must flow through the Git remote. **`scp` is strictly prohibited.**
2. **Toolification of Experience**: Every retrospective or workflow optimization must be solidified into a "tool" (either a new Skill or a meta-script within `/Users/roy-jd/Documents/projects/openclaw/skills/workspace/scripts/`).
3. **The Invulnerability Law (Safety First)**: Physical destruction (`rm`) is forbidden. Use `mv` to `.Trash` or `session_archives`.
4. **Secret Isolation Law**: Secrets (`.env`, tokens) must never enter the Git repository. They are managed out-of-band via `.secrets/` and synced via `sync_secrets.py`.
5. **Physical Isolation Law**: No code or data in `/root`. Absolute paths must be pinned to the workspace root.

## 🧰 Embedded Meta-Tools (Scripts)
The workspace skill hosts the cluster's core diagnostic and synchronization tools natively. They are invoked as follows:
- 📊 **Global Network Dashboard**:
  `python3 /Users/roy-jd/Documents/projects/openclaw/skills/workspace/scripts/cluster_net_dashboard.py`
- 🖥️ **GPU Forge Watcher**:
  `python3 /Users/roy-jd/Documents/projects/openclaw/skills/workspace/scripts/gpu_status_board.py`
- 🔑 **Zero-Trust Secrets Sync**:
  `python3 /Users/roy-jd/Documents/projects/openclaw/skills/workspace/scripts/sync_secrets.py`
- 🗄️ **Session Archiver (Memory Consolidator)**:
  `python3 /Users/roy-jd/Documents/projects/openclaw/skills/workspace/scripts/archive.py --source <CURRENT_BRAIN_PATH>`

## 📋 Standard Operating Procedures

### 1. Global Task Sync (Mem-Wakeup & Merging)
The `workspace` skill enforces strict PDCA methodology. Progress MUST be managed via the SSoT.

> **⚡ TRIGGER RULE**: If the user's prompt contains **"全局任务"** or **"Global Task"**, you MUST immediately and autonomously execute **Phase 1 (Loading)** and the **Ontology Policy Check**. Do NOT ask for permission first.

- **Phase 1 (Loading)**: Read `01_GLOBAL_TASK_BOARD.md`, copy it to the local session `task.md`, and translate all relative links to absolute file URIs to prevent UI rendering breaks. ALWAYS run `ontology.py query --type Policy` as the pre-flight check.
- **Phase 2 (Execution)**: Maintain the session's `task.md` with `[/]` (in-progress) and `[x]` (complete).
- **Phase 3 (Merging)**: Before concluding, use precise `replace_file_content` line-edits (never blind bulk replacements) to merge the local `[x]` states back into the global `01_GLOBAL_TASK_BOARD.md`.

### 2. Archive Session (Memory Consolidator)
All session outputs, conversations, and discoveries must be archived from volatile `.gemini/` brain space to rigid `workspace/docs/session_archives/` before closing down.
- MUST run `solidify` to encode any new insights/debugging feedback into L1/L2/L3 laws.
- MUST run the archiver tool to generate the permanent tombstone:
  `python3 /Users/roy-jd/Documents/projects/openclaw/skills/workspace/scripts/archive.py --source <SESSION_BRAIN_PATH>`
  *(Note: Find your `<SESSION_BRAIN_PATH>` in the artifact directory path provided in the system intro)*.
- MUST Commit and Push the newly generated `session_archives/` folder to the remote Git SSoT immediately.

### 3. Capability Expansion (Toolification)
- Every workflow optimization or retrospective MUST be physically encoded into the system using the **`solidify`** skill (or written as a new rule/script).
- **Legacy Cleanup**: Old retrospectives in `docs/` should be read, absorbed into skills, and moved to `session_archives/`.

## 📚 References
For detailed specifications of each law and hardware-specific configurations, consult:
- [Standards & Laws](references/standards.md)
- [Hardware Profiles](file:///Users/roy-jd/workspace/docs/HARDWARE_PROFILE.md)
