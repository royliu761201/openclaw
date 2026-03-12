---
name: OpenClaw Node Manager
description: Solidifies the physical deployment, sync, and V3.7 authentication bypass operations for OpenClaw Core across multi-node grids (Node 01/02).
---

# OpenClaw Node Manager (V3.8 Authentication Bypass Edition)

## 📡 核心使命 (Core Mission)

This skill controls the deployment, heartbeat monitoring, and configuration bridging of OpenClaw gateway daemons across Node 01 (指挥中心) and Node 02 (边缘网关).

## 🚫 绝密防坑禁区 (V3.8 Hardened Operations)

The OpenClaw 3.8 architecture has strict type checking and cascading deletion mechanisms for underlying configuration files. When deploying across nodes, you MUST adhere to these critical operations:

### 1. Zero-JSON Auth Hook (Single-Point Env Injection)

Based on white-box auditing (`src/agents/model-auth.ts`: `resolveEnvApiKey`), OpenClaw V3.8 natively supports extracting OS environment variables (e.g., `GOOGLE_API_KEY`) as a top-level fallback mechanism.

- **Critical Ban**: You are **STRICTLY PROHIBITED** from using tools like `vault-keeper` to extract, translate, and distribute separate `auth-profiles.json` files! Since the framework supports environment variable pass-through, scattering JSON configurations creates fragmented architecture and audit blind spots.
- **The Only Legal Authentication Path**: Standardize AI API keys alongside Feishu Gateway keys. Mount them directly via the `start_gateway.sh` script (`export`) or pass them into PM2 via `ecosystem.config.js`.

### 2. Git-Ops Exclusively & The PM2 Hot-Reload Mandate

When deploying to Edge Nodes, **NEVER** use `scp` or `ssh 02 "cat << EOF > file"` to drop physical scripts.

- **Native Git-Ops**: Node 02 should ONLY be updated via `git pull`.
- **🚨 PM2 OBLITERATION LAW (Rule 4.6)**: You are **ABSOLUTELY FORBIDDEN** from simply running `git pull` and walking away. To purge ghost configurations from PM2's memory, you MUST concatenate the pull with the strict environment update flag: `ssh 02 "cd ~/workspace && git pull && pm2 reload openclaw-gateway --update-env"`. Failure to use `--update-env` triggers silent fallback fallacies.

### 3. Cascading Deletion Risk: The `--force` Trap

Executing `openclaw agents delete <id> --force` triggers background garbage collection that silently moves the corresponding `.agent` and `~/.openclaw/agents/<id>` physical directories to the trash.

- **Tactical Defense**: NEVER use `openclaw agents delete` unless intending to fully rebuild. To deep-clean, manually execute `pm2 kill`, then `trash ~/.openclaw/agents`. Never use `rm -rf` directly for the `agents` folder! When rebuilding, MUST prefix with `mkdir -p` to re-cast the identity slots.

### 4. SSoT Identity Merge (Cognitive Consistency)

In OpenClaw, if an LLM’s persona conflicts, it is usually due to the split identity system (UI Prefix config vs. LLM Context files).

- **Mandates**:
  1. Strip the `identity` object entirely from `openclaw_core.json` to allow 100% LLM persona pass-through from `IDENTITY.md`.
  2. SSoT strictly relies on two files in `agent_workspaces/<name>/`: `USER.md` (soul) and `IDENTITY.md` (naming).
  3. When an identity configuration is altered, you MUST move lingering `.jsonl` session files from `~/.openclaw/agents/<id>/sessions/` into `~/.Trash` to complete a cognitive wipe.

### 5. The Scorched Earth Wipe (Complete Anti-Ghosting SOP)

_Upgrade Warning_: The legacy Scorched Earth policy omitted low-level queue caches, resulting in the catastrophic "Ghost Cron Loop" incident. To ensure zero historical remnants survive, resetting an OpenClaw instance MUST strictly follow these 3 steps:

1. **Kill Zombies (Bypass SIGINT Memory Flush)**: You **MUST NEVER** rely solely on `pm2 stop`! PM2's graceful shutdown allows the dying process to resurrect its toxic queues back to disk in its final moments. You must execute a physical kernel kill: `pm2 stop all && pkill -9 -f node`.
2. **3D Historical Extermination (Complete Directory Wipe)**: Do not just clear `sessions`. You must simultaneously obliterate identity caches, cron jobs, and delivery queues to destroy any SQLite/JSON-based zombie intents:
   `rm -rf ~/.openclaw/sessions/* ~/.openclaw/agents/* ~/.openclaw/cron/* ~/.openclaw/delivery-queue/* ~/.openclaw/memory/subagents/*`
3. **Eradicate System Cron Bombs**: Inspect and sever system-level daemon links: `crontab -l | grep -v 'openclaw' | crontab -`. Skipping any of these reset steps is a violation of system discipline.

### 6. Routing Fallback Death Trap (Strict Bindings Injection)

_Retrospective Issue_: The work assistant mistakenly identified as DanDan.
When defining multi-account structures in `openclaw_core.json` (`accounts: {research, work}`), relying merely on token listing is fatal. The low-level router (`listRouteBindings`) defaults all incoming WebSocket traffic to the `defaultAccount` if explicit bindings are missing.

- **The Fix**: You MUST manually and explicitly cast the `bindings` array in the root of `openclaw_core.json`.
  _Example_: `"bindings": [{ "agentId": "agent-work", "match": { "channel": "feishu", "accountId": "work" } }]`

### 7. The pnpm Promise Stall (PM2 Ghost Lock)

When running the official `scripts/run-node.mjs` via PM2, do not inherently trust the PM2 `online` status. If PM2 lacks `$PATH` resolution for `pnpm`, a `spawn("pnpm", ["build"])` will throw `ENOENT` natively, but freeze the wrapper Promise causing a CPU 0% permanent stall rather than crashing outwardly.

- **Antidote**: Inject `export OPENCLAW_SKIP_BUILD=1` directly into `start_gateway.sh`. Never alter the official `run-node.mjs` script; treat the symptom through environment control.

### 8. Pure Infra as Code

Dynamically generating `start_gateway.sh` on Node 02 using `echo "export KEY=..."` is an anti-pattern.

- The PM2 gateway startup script MUST remain a 100% static file tracked via Git. All plaintext secrets must be shielded behind `source ~/.openclaw_env`.

### 9. The Fail-Fast Scorched Earth (No Soft-Link Fallbacks)

OpenClaw defaults to fallback configuration paths like `$HOME/workspace/config/openclaw_core.json` when `OPENCLAW_CONFIG_PATH` is lost from memory (e.g., improper PM2 restarts).

- **Absolute Boss Directive**: **"Never use symbolic links to mask falls; fail as early as possible!"**
  1. **Pre-Flight Scorch**: Always run `rm -f $HOME/workspace/config/openclaw_core.json ~/openclaw/config/openclaw_core.json` to scorch any fallback attempts.
  2. **Fail-Fast Assertion**: Assert the desired file existence explicitly before launch: `[ ! -f "$OPENCLAW_CONFIG_PATH" ] && exit 1`. Stop execution at the starting line.

### 10. The Evidence-Based E2E Doctrine (White-Box & Driven Verification)

Relying on "PM2 is online" or "no script error" as successful deployment validation is forbidden.

1. **White-Box Pre-Flight**: Always use `grep_search` or `view_code_item` to understand source code mechanisms and check historical `session_archives` before mutating the system. No blind guessing.
2. **E2E Case Verification**: To claim an issue like "identity cross-wiring" is fixed, you must simulate raw payload hits to the API using tools like `curl`, and actively inspect the state of directories like `sessions/` for tangible output files.
3. **Artifact Evidence Conservation**: Exact stdout, matched regex on expected identity terms (e.g., '蛋蛋' over '丹丹'), and JSON responses MUST be saved into your task or walkthrough markdown logs as case-by-case proof. No evidence, no closure.

### 11. Zero-Translation Hooking

_Retrospective Issue_: We used to map `FEISHU_RESEARCH_APP_ID` into `FEISHU_APP_ID` manually inside start scripts.
This translation layer increases architectural brittleness.

- **Directive**: **Never re-wrap or rename vault secret keys in scripts.** Configurations like `openclaw_core.json` MUST natively reference the underlying vault key (`"${FEISHU_RESEARCH_APP_ID}"`). End-to-end naming alignment is mandatory.

### 12. Production Zero-Downtime Updates (State-Preserving)

_Context_: When operating in a production environment, you must **NEVER** routinely clear the `sessions/*` or `agents/*` directories. Erasing historical memory is a catastrophic "Scorched Earth" action strictly reserved for unrecoverable cognitive collapses (as described in Section 5).

For routine operational upgrades, use the following **State-Preserving** SOPs:

1. **Scenario A: Upgrading the LLM (Model Change/API Key Rotation)**
   - **Action**: Modify `~/.openclaw_env` or the model mappings in `openclaw_core.json`.
   - **Zero-Downtime Execution**: Run `pm2 reload openclaw-gateway --update-env`. The gateway spins up a new parallel process. The old process drains existing WebSocket requests before gracefully dying. **All session histories and embeddings remain 100% intact.**

2. **Scenario B: Launching a New Sub-Agent**
   - **Action**: Add the new agent workspace and register it in `bindings`/`list`.
   - **Zero-Downtime Execution**: Run `pm2 reload openclaw-gateway --update-env`. The new agent becomes available on the execution tree instantly. Existing agents and their SQLite/JSONL histories are completely unaffected.

3. **Scenario C: Adjusting an Agent's Skills (Tool Mounting)**
   - **Action**: Modify the allowed tools in the agent's configuration or universal JSON schema constraints.
   - **Zero-Downtime Execution**: Run `pm2 reload openclaw-gateway --update-env`. The agent continues its ongoing conversations dynamically with the newly updated tool repertoire available for its next ReAct loop, suffering zero cold-start penalties and losing no prior context.

**Remember: `pm2 reload` is your surgical scalpel for production. `pkill -9` and `trash sessions/*` are your nuclear options for corrupted testing nodes. Know the absolute difference.**

### 13. The Tool-Capability Pricing Paradox (算力匹配降本法则)

_Context_: Deploying lightweight models (like `gemini-3.1-flash-lite`) to execute complex schema tools (e.g., `edit` with `oldText` matching, or `cron` JSON payloads) is a catastrophic anti-pattern.

- **The Paradox**: When a Lite model fails a strict schema validation, the Gateway engine attempts up to 5 auto-retries, forwarding the entire massive context history each time. This "cheap" model ultimately burns 5x tokens and still fails, creating a **Token Avalanche**.
- **The Blueprint Mandate**: For fully autonomous edge agents that require structural editing or scheduling, you MUST upgrade the primary engine to a flagship benchmark (`google/gemini-3.0-flash-preview` or `2.5-flash`). Do NOT use Lite models when heavy tool payloads are enabled.

### 14. The Free Web-Fetch Default (破解“缺 Key”幻觉)

_Retrospective Issue_: The agent hallucinated that it could not fetch URLs due to missing API Keys or network limits.

- **The Reality**: OpenClaw natively embeds `web_fetch` which circumvents the need for any third-party crawling key.
- **The Fix**: If an agent refuses to interact with a URL, do NOT configure new tools. Instead, perform an Identity brain-surgery (via `IDENTITY.md`) by injecting the "Tool Awareness Law": explicitly state they possess native, keyless `web_search` and `web_fetch` capabilities.

### 15. Deprecated Web Search Providers (Tavily 退市通告)

OpenClaw V3.8 Source Code (`src/agents/tools/web-search.ts`) rigidly hardcodes only five acceptable providers.

- **Legal Providers**: `["brave", "perplexity", "grok", "gemini", "kimi"]`.

### 16. The Fallback Fallacy (模型静默降级通告)

When re-configuring primary model IDs (e.g., in `openclaw_core.json`), you MUST use the exact, hardcoded strings recognized by the OpenClaw Engine (e.g. `google/gemini-3-flash-preview`).

- **The Danger**: If you use an intuitive but illegal ID (like `gemini-3.0-flash-preview`, adding an extra `.0`), the Gateway will NOT crash. Instead, it forcefully triggers a quiet **Fallback** to the last cached lightweight model (e.g. `3.1-flash-lite`), causing you to mistakenly believe the primary brain swap was successful, but actual response capabilities remain at Lite tier.
- **🚨 4.6 The Fallback Fallacy Law (PM2 Hot-Reload Mandate) 🚨**: Even if the underlying `openclaw_core.json` or `.openclaw_env` is updated via Git, the PM2 daemon (`openclaw-gateway`) continues to run with the old in-memory configuration. You are **ABSOLUTELY FORBIDDEN** from claiming a configuration change or SSoT sync is successful until you execute `pm2 reload openclaw-gateway --update-env` on the target node. Failure to pass `--update-env` means the old environmental states persist eternally, leading to silent fallback fallacies and ghost caches.

## ⚡ npmmirror 强挂 (CN Regional Acceleration)

- Mandatory npm lock bypass for Edge Node setups.
- Use `npm config set registry https://registry.npmmirror.com` before executing `npm install` and `npm run build` on Node 02.

## 📡 动态 PDCA 与健康长城 (Radar & Audit Toolchain)

This skill now includes two heavily armed python scripts for active health probing and LLM-as-a-Judge dialogue auditing across Node 01 and Node 02.

1.  **`agent_radar.py` (The Pulse)**
    - **Function**: A lightweight, on-demand CLI probe run from Node 01. It SSHs into Node 02 to parse PM2 memory footprints, check the `18789` port listener, and sweep the latest 100 lines of OpenClaw native logs for stealthy `Error`/`Warn` events.
    - **Usage**: Execute `~/openclaw/skills/openclaw-node-manager/scripts/agent_radar.py` whenever the boss suspects a Node 02 physical outage.

2.  **`test_skills_health.py` (The Proactive Skill Validation Pipeline)**
    - **Function**: A comprehensive automated validation suite testing `gog`, `kaggle`, `ssh`, `email`, `tavily`, `gemini`, and optionally `exa` across the grid.
    - **Mandatory Trigger Rule**: While this test can be manually invoked on demand, **any Agent executing a major configuration update, or triggering a "PDCA Loop" (Plan-Do-Check-Act) involving system changes, MUST proactively execute `~/workspace/.local_skills/openclaw-node-manager/scripts/test_skills_health.py` as a mandatory validation step** to ensure the ground-truth tool capabilities are intact before concluding the task.

3.  **`audit_sessions.py` (The LLM Judge)**
    - **Function**: Breaks the black box of Agent-User communication. It reaches into Node 02's `~/.openclaw/agents/<id>/sessions/*.jsonl` to extract recent raw dialogue, passing it to Gemini via the `GOOGLE_API_KEY` mapped in `~/.openclaw_env`. Gemini evaluates the agents on 3 strict criteria: Hallucination/Incompetence, PURE Law Compliance, and PDCA prompt suggestions.
    - **Usage**: Execute `~/openclaw/skills/openclaw-node-manager/scripts/audit_sessions.py` to auto-generate a timestamped Markdown PDCA report in `workspace/docs/projects_pdca/`.

4.  **`audit_identity_probe.py` (The Dynamic Cognitive Probe)**
    - **Function**: Physically sends an adversarial conversational payload to the live PM2 gateway asking for its exact model alias. If the model hallucinates (e.g., claiming to be "3.1-flash-lite"), this script enforces an immediate, automated `$ pm2 reload --update-env` sequence.
    - **Usage**: Strongly recommended to run `~/openclaw/skills/openclaw-node-manager/scripts/audit_identity_probe.py` whenever model configurations in `openclaw_core.json` are swapped to ensure no PM2 Ghost Caches remain.

5.  **`audit_skills_bindings.py` (The Static LLM-Environment Parser)**
    - **Function**: Simulates the OpenClaw Agent Engine's start-up life cycle. It rips every `requires.env` key from `~/openclaw/skills/*/SKILL.md` and explicitly cross-checks them against the native `~/.openclaw_env`.
    - **Usage**: **Mandatory Trigger Rule**: Run this meta-linter BEFORE confirming any new skill deployment or environment variable modification to avoid "Silent Tool Drift."

6.  **`semantic_memory_linter.py` (RAG Quarantine / Garbage Collector)**
    - **Function**: Actively searches `workspace/docs/session_archives` (and implicitly future vectors) to hunt down explicitly banned legacy vocabulary (e.g., deleted model IDs, deprecated APIs). Quarantines infected documents to prevent secondary RAG hallucinations.
    - **Usage**: Execute during deep system maintenance loops or immediately after discovering a severe context-poisoning event.

7.  **The Resolution (Act & Healing - PDCA 终极闭环)**
    - **How to Process the Audit**: Once the Judge report flags a Semantic or Rule violation (e.g., "Hallucinated the Boss's name" or "Replied using internal tags"), you MUST immediately enter the **Correction Phase**.
    - **SOP**:
      1. Open the offender's physical brain: `agent_workspaces/<offender_name>/.agent/IDENTITY.md` or `USER.md` on Node 01.
      2. Inject a strict Regex-like anti-hallucination constraint.
      3. Do NOT SSH and hot-edit Node 02. Push changes to Git SSOT: `git commit -m "fix(agent): apply pdca correction" && git push`.
      4. Trigger the Zero-Downtime immunity shot over SSH. **MUST INCLUDE `--update-env`**: `ssh 02 "cd ~/workspace && git pull && pm2 reload openclaw-gateway --update-env"`. The Agent is instantly healed for the next conversation round without losing prior context.

### 17. The Edge Node Verification Protocol (端到端防幻觉物理测试法则)

_Retrospective Issue_: Probes running on Node 01 falsely reported Success for Node 02 because they executed localized sanity checks (e.g., `which gog`), leading to a "Spatial Overlap Hallucination" and masking a severe "Env Binding Blackout" on the Edge Node.

- **The Boss's Ultimate Directive**: When you claim Node 02 is tested and operational, passing a Python probe script is NOT enough. You MUST conduct an active End-to-End LLM Prompt test strictly on the target Edge environment.
- **SOP for Edge Verification**:
  1. DO NOT assume tool visibility! OpenClaw will silently drop tools if their required environment variables (e.g., from `~/.openclaw_env`) are physically missing on Node 02.
  2. You MUST verify tool invocation (e.g., Gmail reading) by reading the returned physical text or parsing the `~/.openclaw/agents/<id>/sessions/test_run_1.jsonl` log. Only tangible payload evidence counts as a "Pass".

### 18. The White-Box Config Split-Brain Trap (OPENCLAW_CONFIG_PATH 失忆症)

_Context_: When deploying the SSoT blueprint (`openclaw_core.json`) to Node 02, injecting the `OPENCLAW_CONFIG_PATH` directly into the `openclaw-gateway` PM2 ecosystem is NOT sufficient. The CLI `node scripts/run-node.mjs` operates in a distinct headless SSH bash process. If the CLI shell does not explicitly source `~/.openclaw_env`, it will fall back to `~/.openclaw/config/openclaw.json`, resulting in an `Unknown agent id` error.
_Even worse_: If you mechanically patch `~/.openclaw_env` but inject the legacy default path instead of the SSoT path (`~/worksp### 19. The SIGINT Death-Rattle (Memory Flush Resurrection Trap)

_Retrospective Issue_: Even when `auth-profiles.json` was manually deleted from the disk, the locally expired Google API key resurrected itself like a ghost inside the file upon every PM2 restart.

- **The Core Poison**: OpenClaw actively intercepts `SIGINT` signals (typically sent by `pm2 restart`). In the very last millisecond before the Node.js process gracefully dies, it triggers a final synchronous `fs.writeFileSync()` call, hard-flushing its entirely corrupted memory state back to `auth-profiles.json` on the disk.
- **The SOP**: When manually wiping tainted authentication states, you **MUST NOT** rely on graceful restart mechanisms. To crush the PM2 Death-Rattle, you must execute a painless instantaneous kernel kill:
  `pkill -9 -f node && rm -f <path-to-auth-profiles.json>`
  Only after guaranteeing the ghost process is fully eliminated are you allowed to spin the gateway daemon back up.

### 20. PM2 Path Cloning & The Native Script Abstraction Trap

_Retrospective Issue_: The PM2 ecosystem silently swallowed fatal `ENOENT` faults on Node 02 because it brazenly attempted to execute Mac Homebrew system paths cloned via `ecosystem.config.cjs` from Node 01, completely ignoring Node 02's pristine NVM deployment.

- **The Native Bash Wrapper Mandate**: When deploying across multi-node topologies, you are **ABSOLUTELY FORBIDDEN** from pointing `ecosystem.config.cjs` directly to any ES Module entrypoint (`openclaw.mjs` or `run-node.mjs`)! PM2's fragile internal JavaScript spawner cannot traverse cross-OS path traps.
- **The SOP**:
  1. For Edge Nodes, you must write a pure Bash wrapper script (`start-gateway-native.sh`). This wrapper must first source the native `~/.nvm/nvm.sh` and strictly use an **absolute hardcoded path** to execute the Node binary (`/Users/roy-002/.nvm/versions/node/v22.14.0/bin/node`).
  2. Inside `ecosystem.config.cjs`, you must force the interpreter to `bash` and point it to the native Bash wrapper. This completely abstracts PM2 away from the Node.js initialization barrier.用，将有毒的完整内存状态硬写回磁盘上的 `auth-profiles.json` 中。
- **排雷标准操作流程 (SOP)**: 当你需要手动清理被深度污染的身份认证状态时，**绝不允许**依赖任何优雅的重启机制。要粉碎 PM2 的临死反扑，你必须执行无痛的瞬时内核级绞杀：
  `pkill -9 -f node && rm -f <path-to-auth-profiles.json>`
  只有在确保幽灵进程被彻底爆头后，才允许重新拉起网关守护进程。

### 20. PM2 路径克隆综合征与原生脚本剥离法则

_近期复盘事故_: PM2 进程池在 Node 02 上把致命的 `ENOENT` 错误静默咽下了，因为它试图去强行执行通过 `ecosystem.config.cjs` 从 Node 01 复制过来的 Mac Homebrew 系统路径，完全无视了 Node 02 的纯净 NVM 部署环境。

- **原生 Bash 执行外壳铁律**: 在部署多节点拓扑时，**绝对禁止**将 `ecosystem.config.cjs` 直接指向任何 ES Module 入口文件 (`openclaw.mjs` 或 `run-node.mjs`)！PM2 内部羸弱的 JavaScript 孵化器根本无法跨越不同 OS 层级的路径陷阱。
- **排雷标准操作流程 (SOP)**:
  1. 面对边缘节点，必须编写一个纯粹的 Bash 脚本外壳 (`start-gateway-native.sh`)，内部首先挂载原生的 `~/.nvm/nvm.sh`，并且必须以**绝对硬编码路径**去执行 Node 二进制文件 (`/Users/roy-002/.nvm/versions/node/v22.14.0/bin/node`)。
  2. 在 `ecosystem.config.cjs` 中，必须将解析器强制设为 `bash`，并让其指向那个原生的 Bash 外壳脚本。此举将 PM2 完全挡在 Node.js 环境的初始化屏障之外。
