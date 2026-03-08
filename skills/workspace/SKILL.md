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
2. **Toolification of Experience**: Every retrospective or workflow optimization must be solidified into a "tool" (either a new Skill or a meta-script within `/Users/roy-jd/openclaw/skills/workspace/scripts/`).
3. **The Invulnerability Law (Safety First)**: Physical destruction (`rm`) is forbidden. Use `mv` to `.Trash` or `session_archives`.
4. **Secret Isolation Law**: Secrets (`.env`, tokens) must never enter the Git repository. They are managed out-of-band via `.secrets/` and synced via `sync_secrets.py`.
5. **Physical Isolation Law**: No code or data in `/root`. Absolute paths must be pinned to the workspace root.
6. **Multi-Agent Workspace SSoT Law**: NEVER use `OPENCLAW_STATE_DIR` to configure edge agents serving multiple channels. You MUST hard-code their exact physical SSoT directory (e.g., `~/workspace/agent_workspaces/node02/workspace-agent-research`) explicitly into the `workspace` property of their specific `agents.list` entry within `openclaw.json`.

## 🧰 Embedded Meta-Tools (Scripts)
The workspace skill hosts the cluster's core diagnostic and synchronization tools natively. They are invoked as follows:
- 📊 **Global Network Dashboard**:
  `python3 /Users/roy-jd/openclaw/skills/workspace/scripts/cluster_net_dashboard.py`
- 🖥️ **GPU Forge Watcher**:
  `python3 /Users/roy-jd/openclaw/skills/workspace/scripts/gpu_status_board.py`
- 🔑 **Zero-Trust Secrets Sync**:
  `python3 /Users/roy-jd/openclaw/skills/workspace/scripts/sync_secrets.py`
- 🗄️ **Session Archiver (Memory Consolidator)**:
  `python3 /Users/roy-jd/openclaw/skills/workspace/scripts/archive.py --source <CURRENT_BRAIN_PATH>`
- 📥 **Global Task Loader**:
  `python3 /Users/roy-jd/openclaw/skills/workspace/scripts/load_global_task.py --global_board <GLOBAL_BOARD_PATH> --session_task <BRAIN_PATH>/task.md`

## 📋 Standard Operating Procedures

### 1. Global Task Sync (Mem-Wakeup & Merging)
The `workspace` skill enforces strict PDCA methodology. Progress MUST be managed via the SSoT.

> **⚡ TRIGGER RULE**: If the user's prompt contains **"全局任务"** or **"Global Task"**, you MUST immediately and autonomously execute **Phase 1 (Loading)** and the **Ontology Policy Check**. Do NOT ask for permission first.

- **Phase 1 (Loading)**: Run the loader script to pull `01_GLOBAL_TASK_BOARD.md` to your local session `task.md` with auto-resolved absolute URIs. ALWAYS run `ontology.py query --type Policy` as the pre-flight check.
  `python3 /Users/roy-jd/openclaw/skills/workspace/scripts/load_global_task.py --global_board /Users/roy-jd/workspace/docs/system_core/memory_core/01_GLOBAL_TASK_BOARD.md --session_task <SESSION_BRAIN_PATH>/task.md`
  > **⚠️ CRITICAL UI BUGFIX**: The python script above bypasses the UI! Immediately after running it, you MUST run a `write_to_file` tool call with `IsArtifact: true` (copying the newly loaded contents) to explicitly sync the Agent's UI so the user can see the full global board!
- **Phase 2 (Execution)**: Maintain the session's `task.md` with `[/]` (in-progress) and `[x]` (complete).
- **Phase 3 (Merging & Archiving)**: Before concluding, use precise `replace_file_content` line-edits to merge the local `[x]` states back into the global `01_GLOBAL_TASK_BOARD.md`. **Crucial Rule**: Completed sub-tasks must be swept into the `### 📦 已归档` block situated at the absolute bottom of the document, strictly capped at retaining only the 3 to 5 most recent records.

### 2. Archive Session (Memory Consolidator)
All session outputs, conversations, and discoveries must be archived from volatile `.gemini/` brain space to rigid `workspace/docs/session_archives/` before closing down.
- MUST run `solidify` to encode any new insights/debugging feedback into L1/L2/L3 laws.
- MUST run the archiver tool to generate the permanent tombstone:
  `python3 /Users/roy-jd/openclaw/skills/workspace/scripts/archive.py --source <SESSION_BRAIN_PATH>`
  *(Note: Find your `<SESSION_BRAIN_PATH>` in the artifact directory path provided in the system intro)*.
- MUST Commit and Push the newly generated `session_archives/` folder to the remote Git SSoT immediately.

### 3. Cross-Node Inbox Drop (Node 02 Token Economy Delivery)
When operating as a detached gateway (e.g., Node 02 via Feishu) and receiving heavy documents, YOU MUST NOT summarize them. Invoke the "Token Economy Handoff":
**(A) For Web Links (Arxiv, Github, URLs):**
1. Create a rigid manifest file at `~/workspace/docs/projects_pdca/<topic>_inbox.md`.
2. Write exactly: `[指令：请 01 本脑狂烧算力深度阅读并研发]` followed by the raw URL.
3. Git add, commit, push.

**(B) For Physical Binary Files (PDF, Word, etc.):**
> ⚠️ **The Zero-Weight Policy**: NEVER commit PDFs or Word docs to Git.
1. Save the physical file to a `.gitignore`d directory, e.g., `~/workspace/projects_core/<Project>/data/raw/<filename>.pdf`.
2. Use `scp` or `rsync` to blindly push this physical file directly to Node 01's (or Node 03 Vault's) identical path:
   `scp <file> <user>@<node01_ip>:~/workspace/projects_core/<Project>/data/raw/`
3. Create the `xxx_inbox.md` file in Git, writing:
   `[指令：请 01 本脑深度阅读。文件已物理送达你的: ~/workspace/projects_core/<Project>/data/raw/<filename>]`
4. Git add, commit, push the MD file as the execution signal.

### 4. Capability Expansion (Toolification)
- Every workflow optimization or retrospective MUST be physically encoded into the system using the **`solidify`** skill (or written as a new rule/script).
- **Legacy Cleanup**: Old retrospectives in `docs/` should be read, absorbed into skills, and moved to `session_archives/`.

## 📚 References
For detailed specifications of each law and hardware-specific configurations, consult:
- [Standards & Laws](references/standards.md)
- [Hardware Profiles](file:///Users/roy-jd/workspace/docs/HARDWARE_PROFILE.md)

### 🚫 防坑禁区 (Anti-Hallucination)
- **UI Task Desync (Double Fault)**: Running `load_global_task.py` writes ONLY to the hard drive, NOT the Agentic UI. The UI will show old contents while the file is updated. To fix this, you must run `view_file` on `task.md` and then mirror its content back via `write_to_file` with `IsArtifact: true` immediately after Phase 1.
- **The Grounding Law Exception**: When loading global tasks or updating project descriptions via this skill, you MUST NOT generate project descriptions from system memory. You MUST force a read of the original SSoT documents or the `09_GROUNDED_*_INDEX.md` registries. No hallucinated background text is permitted during task decomposition.
