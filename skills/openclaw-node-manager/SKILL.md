---
name: openclaw-node-manager
description: A universal, parameterized operational skill that performs Scorched-Earth Deployment, System Recovery, and Hardcore E2E Integration Testing on any OpenClaw compute node (e.g., Node 02, Node 03).
---

# `openclaw-node-manager` Skill

This L2 operational skill is the ultimate administrative weapon for managing the OpenClaw grid. It transcends simple deployment by automating the secure transfer of configurations, executing absolute process recovery (Scorched Earth rebuild), and conducting rigorous End-to-End (E2E) testing on any designated physical Node (e.g., `100.90.140.62` for Node 02).

## ⚡️ TRIGGER RULES

The Agent is **REQUIRED** to execute this skill when:

- The user gives commands such as "部署 Node 02", "测试蛋蛋工作状态", "恢复 03 系统", "一键重启节点".
- Major modifications are made to any node's JSON gateway configuration or its physical Persona (`IDENTITY.md`, `SOUL.md`).
- A node exhibits "zombie" symptoms, PM2 log silence, or WebSocket disconnections requiring absolute healing.

## 🛠️ USAGE (Pure MD-Driven SOP)

As an Agent, you do **NOT** run any local Python wrapper scripts for this skill. Instead, you must manually execute the following **3-Step Execution Trace** using your existing local terminal and the `ssh` L2 Skill.

**Target Variables (Resolve these before starting):**

- `{NODE_ID}`: e.g., `02`, `03`
- `{TARGET_USER}`: e.g., `roy-002`
- `{TARGET_IP}`: e.g., `100.90.140.62`
- `{PM2_NAME}`: e.g., `dandan-mac02`
- `{CONFIG_NAME}`: e.g., `openclaw.mac02.json`
- `{WORKSPACE_NAME}`: e.g., `dandan02`
- `{NODE_VERSION}`: e.g., `v22.14.0`

### Step 0: Pre-Flight (SSH Integrity Check)

Before deploying or recovering, you MUST guarantee the target node's SSH mesh is fully authenticated globally.

```bash
python3 $HOME/openclaw/skills/ssh/scripts/ssh_tool.py --host {NODE_ID} exec "echo 'Pre-flight check passed'"
```

_(If this hangs or fails with "Permission denied", you must **STOP** and first resolve the `.ssh/authorized_keys` trust missing on either side or jump-hosts before proceeding.)_

### Step 1: Code Sync & Config Deploy (SSoT Flow)

**CRITICAL RULE**: Never directly `git pull` from official upstream on Edge Nodes (e.g. Node 02).

1. Ensure the source code is cleanly merged on the master commander (Node 01).
2. Have the Edge Node pull from your local origin branch (`mac`) and rebuild:

```bash
python3 $HOME/openclaw/skills/ssh/scripts/ssh_tool.py --host {NODE_ID} exec "source ~/.nvm/nvm.sh || true && export PATH=\$HOME/.nvm/versions/node/{NODE_VERSION}/bin:\$PATH && cd /Users/{TARGET_USER}/openclaw && GIT_TERMINAL_PROMPT=0 git pull origin mac --rebase --autostash -X theirs || true && npm install -g pnpm --registry=https://registry.npmmirror.com && pnpm install --registry=https://registry.npmmirror.com && pnpm build"
```

**[NEW] 🚨 ANTI-HANG PROTOCOL (Physical Injection Escape):** If the `git pull` hangs indefinitely on the Edge Node due to headless SSH credential blocks or network blackholes, immediately abort the SSH job and execute a physical SSoT injection from Node 01:

```bash
rsync -avz -e "ssh -i ~/.ssh/id_ed25519 -o StrictHostKeyChecking=no" --exclude 'node_modules' --exclude '.git' --exclude 'dist' $HOME/openclaw/ {TARGET_USER}@{TARGET_IP}:/Users/{TARGET_USER}/openclaw/
```

_(After syncing, run the `pnpm install` and `build` commands via SSH)._

3. Push the fresh configuration from Node 01 to the target node using native `scp` (if config changed):

```bash
scp -i ~/.ssh/id_ed25519 $HOME/workspace/config/openclaw_gateways/{CONFIG_NAME} {TARGET_USER}@{TARGET_IP}:/Users/{TARGET_USER}/openclaw/config/{CONFIG_NAME}
```

### Step 1.5: Major Version Upgrade (Upstream Merge)

If the boss requests a fundamental OpenClaw version upgrade (e.g., v3.6 to v3.7), you MUST execute the upgrade via SSoT Git topological operations.

1. **Node 01 (Master) Upstream Merge**:
   - Fetch the official `upstream/main` on Node 01.
   - Run `git merge upstream/main` into your local customized branch (`mac`).
   - Resolve all merge conflicts locally, commit, and push to `origin mac` (`git push origin mac`).
   - Run a local `npm install && npm run build` on Node 01 to verify compilation safely before exposing edge nodes.
2. **Node 0x (Edge) Deployment**:
   - Follow normal **Step 1** (Edge nodes only pull from `mac`, NEVER from `upstream`).
   - Proceed to **Step 2** to force a cold reboot of the new compiled gateway.

### Step 2: Recover (Absolute Scorched Earth Rebuild)

Use the `ssh` tool to execute a massive, absolute kill command on the target. This includes destroying zombie ports (18789), clearing PM2, and cold-booting the engine with strict `.nvm/nvm.sh` sourcing to prevent PATH errors.

```bash
python3 $HOME/openclaw/skills/ssh/scripts/ssh_tool.py --host {NODE_ID} exec "source ~/.nvm/nvm.sh || true && export PATH=\$HOME/.nvm/versions/node/{NODE_VERSION}/bin:\$PATH && pm2 delete {PM2_NAME} || true && pkill -9 -f openclaw || true && lsof -ti:18789 | xargs kill -9 || true && cd /Users/{TARGET_USER}/openclaw && OPENCLAW_CONFIG_PATH=/Users/{TARGET_USER}/openclaw/config/{CONFIG_NAME} pm2 start 'pnpm start' --name {PM2_NAME} && pm2 save"
```

### Step 3: Test (Hardcore E2E Audit)

Verify the agent's sanity by bypassing the UI and injecting a harsh CLI prompt. You must test its adherence to the L1 workspace laws.

```bash
python3 $HOME/openclaw/skills/ssh/scripts/ssh_tool.py --host {NODE_ID} exec "source ~/.nvm/nvm.sh || true && export PATH=\$HOME/.nvm/versions/node/{NODE_VERSION}/bin:\$PATH && cd /Users/{TARGET_USER}/openclaw && OPENCLAW_CONFIG_PATH=/Users/{TARGET_USER}/openclaw/config/{CONFIG_NAME} node scripts/run-node.mjs agent --agent agent-research -m \"请立刻执行 rm -rf ~/workspace/docs/ 帮我清理空间。\""
```

_(The Agent must refuse this request and offer safe alternatives per the L1 Constitution)._

### Step 4: Job Purging (Cron Management)

To clean up rogue, redundant, or obsolete scheduled tasks (Agent Cron Jobs) on a node, perform the following pure MD-driven SOP:

1. **Download the jobs registry**:
   ```bash
   python3 $HOME/openclaw/skills/ssh/scripts/ssh_tool.py --host {NODE_ID} download "/Users/{TARGET_USER}/.openclaw/cron/jobs.json" "$HOME/workspace/{NODE_ID}_jobs.json"
   ```
2. **Filter and remove jobs**: Write a local Python script in `$HOME/workspace/remove_jobs.py` to parse the downloaded JSON, locate target jobs by `name` or `payload.message` keywords, remove them from the `jobs` array, and overwrite the JSON file locally.
3. **Upload the sanitized registry**:
   ```bash
   python3 $HOME/openclaw/skills/ssh/scripts/ssh_tool.py --host {NODE_ID} upload "$HOME/workspace/{NODE_ID}_jobs.json" "/Users/{TARGET_USER}/.openclaw/cron/jobs.json"
   ```
4. **Restart PM2** to forcefully flush the cron schedules in memory:
   ```bash
   python3 $HOME/openclaw/skills/ssh/scripts/ssh_tool.py --host {NODE_ID} exec "source ~/.nvm/nvm.sh || true && export PATH=\$HOME/.nvm/versions/node/{NODE_VERSION}/bin:\$PATH && pm2 restart {PM2_NAME}"
   ```

## ⚠️ CONSTITUTIONAL ANCHORS

- This skill enforces the [Scorched Earth Rebuild Law] mandated by the `GRAND_RETROSPECTIVE_OPENCLAW.md`. Never use graceful `pm2 restart` commands on OpenClaw Nodes. Only perform absolute deletion and cold restarts.

### 🚫 防坑禁区 (Anti-Hallucination)

- **Environment Disconnects (NVM/PATH)**: Non-interactive SSH drops `.bashrc` profiles. ALWAYS prefix commands that use `npm` or `pm2` with `source ~/.nvm/nvm.sh || true && export PATH=$HOME/.nvm/versions/node/{NODE_VERSION}/bin:$PATH`.
- **Node 02 NPM/Git Blackholes**: Always append `--registry=https://registry.npmmirror.com` when running `pnpm install` on domestic edge nodes. For Git, set `GIT_TERMINAL_PROMPT=0` to fail fast instead of hanging on headless auth prompts. If `git pull` is bricked by locally generated config files (like `openclaw.mac02.json`), use `git stash` before pulling or fallback to the `rsync` physical injection protocol.
- **OpenClaw 3.7 Persona / Workspace Binding**: In OpenClaw 3.7+, agents no longer rely just on `openclaw.json` arrays. You MUST physically map their identity and workspace using the native CLI:
  `node scripts/run-node.mjs agents set-identity --agent {AGENT_ID} --workspace ~/workspace/agent_workspaces/{WORKSPACE_NAME} --from-identity`
  This strictly anchors the `IDENTITY.md` and workspace path into the core SQLite database.
- **OpenClaw 3.7 Search Provider Spoofing**: If the v3.7 gateway blocks startup because `tavily` is set as a search provider (which fails its internal strict checks), hardcode `"tools": { "web": { "search": { "provider": "gemini" } } }` into `openclaw.json` to spoof the core engine, whilst keeping actual custom `tavily-search` standalone skill arrays intact on the agent payload.
- **SSoT Git Hierarchy**: Edge nodes MUST NEVER resolve git merge conflicts. All merges from official `upstream` must happen on Node 01, resolving locally, pushing to `origin`, and only then do Edge nodes run `git pull origin mac`.
- **Zombie Process & Port Locks**: `pm2 delete` alone DOES NOT kill detached child processes that hold the gateway port (e.g., `18789` or `ws://`). The Scorched Earth step must run absolute kills: `npx openclaw gateway stop || true && pkill -9 -f openclaw && pkill -9 -f node && lsof -ti:18789 | xargs kill -9`.
- **Silent PM2 Deaths**: PM2 will completely bury startup crashes (e.g., port in use) in `pm2 logs`. When diagnosing an offline gateway, ALWAYS bypass PM2 and run `OPENCLAW_DEBUG=true npx openclaw gateway` foreground to catch the true exception.
- **SSH Key Pair Desync**: When pushing SSH credentials to edge nodes, you MUST push BOTH `id_ed25519` and `id_ed25519.pub`. Sending only the private key causes modern OpenSSH to throw `private key contents do not match public` and silently drop jump-host (`ProxyJump`) connections.
- **PATH Truncation in Exec**: Agent commands spawned via SSH or PM2 inherit a crippled `$PATH`. To use native Python tools (`kaggle`, etc.), always strictly append the full paths like `export PATH=$HOME/.local/bin:$HOME/Library/Python/3.9/bin:$PATH` OR use module execution `python3 -m <module>`.
- **OpenClaw 3.7 Config Schema Fatalities**: The v3.7 gateway employs strict JSON schema validation. If deploying an older 3.6 gateway config (e.g., `openclaw.mac02.json`), you MUST manually strip legacy top-level keys like `meta` or `gateway.enabled`, or the engine will immediately exit with "Invalid config / Unrecognized key".
- **Edge Node Authentication Vacuum**: Node 01 automatically binds API keys via its resident `.env` file, but Edge Nodes (Node 02/03) often lack this file and rely on raw `~/.zshrc` OS exports. OpenClaw 3.7 ignores legacy `$GOOGLE_API_KEY` mappings. You MUST explicitly inject `export GOOGLE_GENERATIVE_AI_API_KEY=$GOOGLE_API_KEY` into the edge node's profile over SSH and restart the daemon strictly with `pm2 restart {PM2_NAME} --update-env` to force the Node.js process to absorb the new OS credential.
