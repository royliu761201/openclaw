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

### 2. Git-Ops Exclusively (No SCP Delivery)

When deploying to Edge Nodes, **NEVER** use `scp` or `ssh 02 "cat << EOF > file"` to drop physical scripts.

- **Native Git-Ops**: The `start_gateway.sh` has been stripped of plaintext secrets and acts as a pure static asset using `source ~/.openclaw_env`. Node 02 should ONLY be updated via `git pull` followed by executing this static script.

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

To safely and completely clean an OpenClaw instance without leaving behind "ghosts" (rogue processes or cron jobs):

1. **Kill Zombies**: `pm2 kill` followed immediately by `pkill -9 -f openclaw` to destroy any detached `nohup` shards.
2. **Purge History**: Use `trash ~/.openclaw/sessions/*` and `trash ~/.openclaw/agents/*` to aggressively wipe out previous contextual states without breaking architecture.
3. **Eradicate Cron Bombs**: Inspect and cut out associated cron jobs via `crontab -l | grep -v 'openclaw' | crontab -`. Skipping any of these steps during a reset is a violation of duty.

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

OpenClaw defaults to fallback configuration paths like `~/.openclaw/openclaw.json` when `OPENCLAW_CONFIG_PATH` is lost from memory (e.g., improper PM2 restarts).

- **Absolute Boss Directive**: **"Never use symbolic links to mask falls; fail as early as possible!"**
  1. **Pre-Flight Scorch**: Always run `rm -f ~/.openclaw/openclaw.json ~/openclaw/config/openclaw_core.json` to scorch any fallback attempts.
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
- **The PM2 Ghost Environment Trap**: Even if the underlying `openclaw_core.json` or `.openclaw_env` is updated via Git, the PM2 daemon (`openclaw-gateway`) continues to run with the old in-memory configuration. You are **ABSOLUTELY FORBIDDEN** from claiming a configuration change is successful until you execute `pm2 reload openclaw-gateway --update-env` on the target node. Failure to pass `--update-env` means the old environmental states persist eternally, leading to silent fallback fallacies.

## ⚡ npmmirror 强挂 (CN Regional Acceleration)

- Mandatory npm lock bypass for Edge Node setups.
- Use `npm config set registry https://registry.npmmirror.com` before executing `npm install` and `npm run build` on Node 02.

## 📡 动态 PDCA 与健康长城 (Radar & Audit Toolchain)

This skill now includes two heavily armed python scripts for active health probing and LLM-as-a-Judge dialogue auditing across Node 01 and Node 02.

1.  **`agent_radar.py` (The Pulse)**
    - **Function**: A lightweight, on-demand CLI probe run from Node 01. It SSHs into Node 02 to parse PM2 memory footprints, check the `18789` port listener, and sweep the latest 100 lines of OpenClaw native logs for stealthy `Error`/`Warn` events.
    - **Usage**: Execute `~/openclaw/skills/openclaw-node-manager/scripts/agent_radar.py` whenever the boss suspects a Node 02 physical outage.

2.  **`audit_sessions.py` (The LLM Judge)**
    - **Function**: Breaks the black box of Agent-User communication. It reaches into Node 02's `~/.openclaw/agents/<id>/sessions/*.jsonl` to extract recent raw dialogue, passing it to Gemini via the `GOOGLE_API_KEY` mapped in `~/.openclaw_env`. Gemini evaluates the agents on 3 strict criteria: Hallucination/Incompetence, PURE Law Compliance, and PDCA prompt suggestions.
    - **Usage**: Execute `~/openclaw/skills/openclaw-node-manager/scripts/audit_sessions.py` to auto-generate a timestamped Markdown PDCA report in `workspace/docs/projects_pdca/`.

3.  **The Resolution (Act & Healing - PDCA 终极闭环)**
    - **How to Process the Audit**: Once the Judge report flags a Semantic or Rule violation (e.g., "Hallucinated the Boss's name" or "Replied using internal tags"), you MUST immediately enter the **Correction Phase**.
    - **SOP**:
      1. Open the offender's physical brain: `agent_workspaces/<offender_name>/.agent/IDENTITY.md` or `USER.md` on Node 01.
      2. Inject a strict Regex-like anti-hallucination constraint.
      3. Do NOT SSH and hot-edit Node 02. Push changes to Git SSOT: `git commit -m "fix(agent): apply pdca correction" && git push`.
      4. Trigger the Zero-Downtime immunity shot over SSH: `ssh 02 "cd ~/workspace && git pull && pm2 reload openclaw-gateway --update-env"`. The Agent is instantly healed for the next conversation round without losing prior context.
