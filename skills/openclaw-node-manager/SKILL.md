---
name: OpenClaw Node Manager
description: Solidifies the physical deployment, sync, and V3.7 authentication bypass operations for OpenClaw Core across multi-node grids (Node 01/02).
---

# OpenClaw Node Manager (V3.8 Authentication Bypass Edition)

## 📡 核心使命 (Core Mission)

This skill controls the deployment, heartbeat monitoring, and configuration bridging of OpenClaw gateway daemons across Node 01 (指挥中心) and Node 02 (边缘网关).

## 🚫 绝密防坑禁区 (V3.8 Hardened Operations)

OpenClaw 3.8 架构对底层配置文件有极其严苛的强类型检查与联动删除机制。跨网格部署时必须死守以下 5 条操作红线：

### 1. 【架构重构】鉴权字典的死亡与环境变量单点穿透 (Zero-JSON Auth Hook)

随着白盒审计的深入（`src/agents/model-auth.ts`: `resolveEnvApiKey`），我们确认了 OpenClaw V3.8 具备原生抓取底层操作系统环境变量（如 `GOOGLE_API_KEY` 等）作为最高级 Fallback 的能力。
曾经抛出 `FailoverError: No API key found` 是因为没有挂载进 PM2 的环境空间，而不是缺文件。

- **核心禁令（老板法案固化）**：跨网格部署时，绝对**禁止**使用 `vault-keeper` 等技能去提取、转化主脑配置并分发 4 份甚至更多份的 `auth-profiles.json`！由于底层已实现 Fallback 环境变量穿透，散弹枪式空投 JSON 是制造架构碎片和审计黑洞的毒药。这项旧流程即日起被永久**废黜 (Deprecated)**。
- **唯一合法鉴权路径 (Single-Point Env Injection)**：
  必须将大模型的算力密钥（`GOOGLE_API_KEY`, `ANTHROPIC_API_KEY`）与飞书网关密钥（`FEISHU_APP_ID` 等）合并！全部通过 `start_gateway.sh` 脚本的 `export` 命令硬绑定，或者通过 `ecosystem.config.js` 统一传递给 PM2。网关一旦挂载带算力 Key 的环境变量，管辖内的所有智能体皆自动雨露均沾。

### 2. 废除 SCP 脚本分发，全面拥抱 Git-Ops (Git-Ops Exclusively)

向 Edge Node 部署启动脚本当中，**严禁**使用 `scp` 或 `ssh 02 "cat << EOF > file"` 这种落后的物理文件投递方式！不仅容易引发凭据明文泄露，更会造成版本碎片化（Node 02 本身已经在运行前被 `vault-keeper` 同步好了安全的 `~/.openclaw_env` 环境）。

- **原生 Git-Ops 连招**：`start_gateway.sh` 已经被彻底剥离明文，变成了一份只包含 `source ~/.openclaw_env` 的静态代码资产。靶机 Node 02 只需要通过 `git pull` 更新代码库，然后直接运行本技能包当中的静态剧本即可。任何类似 `deploy_gateway.sh` 的外围搬运脚本都是画蛇添足的冗余，已全部强制报废！

### 3. 极危指令：`--force` 引发的连带式毁灭路径 (Cascading Deletion)

执行 `openclaw agents delete <id> --force` 时，系统不仅会抹除中枢 SQLite，还会触发后台垃圾回收机制（Garbage Collection），无声无息地将 `workspace` 下的 `.agent` 以及 `~/.openclaw/agents/<id>` 目录全盘移至废纸篓。

- **战术防线（老板法案固化）**：除非重建，否则绝不能使用 `openclaw agents delete`。如果要深度清理，必须手动执行 `pm2 kill`，并使用 `trash ~/.openclaw/agents` (或 `mv` 到废纸篓)，**严禁**直接执行不可逆的 `rm -rf` 完成物理大扫除！重建时必须前置 `mkdir -p` 重铸基础身份插槽。

### 4. 彻底切除幽灵源与冗余皮套 (SSoT Identity Merge)

若修改了 Edge Node 上主配文件（例如 `openclaw_core.json`），LLM 的认知依然会被底层文件系统带偏，原因在于 OpenClaw 极其割裂的双轨身份体系：

1. **皮套 (UI Prefix)**：网关通过 `openclaw_core.json` 强加前缀。如果不删除旧配置中的 `identity.name`，就会与底层人设打架。
2. **灵魂 (LLM Context)**：LLM 仅认同底层 SSoT 目录下的 `USER.md` 和 `IDENTITY.md`。

- **宪法级固化（老板审计铁令）**：
  1. **废黜 JSON 皮套**：`openclaw_core.json` 必须被剥离 `identity` 对象，实现 100% 身份穿透给 `IDENTITY.md`！
  2. **绝对 SSoT**：`agent_workspaces/<name>/` 目录下必须坚持并且只能依赖两份刚需文件：赋予灵魂的 `USER.md` 和锚定称呼的 `IDENTITY.md`。
  3. **消灭僵尸会话**：修改配置后，必须进入 `~/.openclaw/agents/<id>/sessions/` 目录，将存留的所有 `.jsonl` 记忆载体移动进 `~/.Trash`（严禁 `rm`），实施断网洗脑！

### 5. 终极清理与反幽灵焦土协议 (The Scorched Earth Wipe)

老板发起了灵魂质询：“以后清理 OpenClaw 怎么做？有没有技能需要加固？”
**回答：** 绝对需要加固本技能！过往由于过度迷信文明管理器（如 `pm2 delete` 或单单清理靶机），导致 Node 01 主机上暗藏幽灵进程与定时炸弹夺舍网关。

- **必须采用的焦土清理连招 (SOP)**：当收到任何“清理 OpenClaw”、“全面重置”的隐式或显式指令时，**必须**不打折扣地依次行刑：
  1. **物理超度本体**：首先 `pm2 kill`，紧接着必须补刀 `pkill -9 -f openclaw`。无论环境，直接摧毁任何可能因 `nohup` 或前台崩溃而脱壳存留的僵尸网关（PID 幽灵）。（用 `lsof -i:18789` 验尸）。
  2. **碎尸历史记忆**：绝不能用 `openclaw agents delete`（会破坏架构）。必须以暴力物理清空：`trash ~/.openclaw/sessions/*` 以及 `trash ~/.openclaw/agents/*`。让所有大模型的对话前摇、旧皮套污染统统下地狱。
  3. **铲除时间炸弹 (Crontab Wipe)**：必须强行调用 `crontab -l` 并在控制台审计，利用 `grep -v 'openclaw' | crontab -` 直接切除系统深处可能每天定时跑起来发信的早古脚本（如 `morning_report.sh`）。

未来任何企图进行初始化或清理的智能体，若敢跳过以上三步中的任何一项，将被视为失职违规！

### 6. 纯净剧本代码化纳管 (Pure Infra as Code)

在 Node 02 动态生成 `start_gateway.sh` 并在里面硬编码写入 `export FEISHU...` 等明文账密，是极度不安全以及产生配置冗余的伪 IaC 行为。

- **治理法则**：启动网关的 PM2 脚本必须是 **绝对纯净的静态文件**，并且作为**“架构设施代码 (IaC)”**永久纳管进本技能包的 `scripts/start_gateway.sh` 资源库中，通过 Git 本机拉取即可多节点复用。脚本内部绝不允许包括任何明文 Secret，全部交由顶端的一句 `source ~/.openclaw_env` 隐式挂载。

### 7. 消除环境变量“翻译层” (Zero-Translation Hooking)

> **Boss 灵魂质询**："FEISHU_RESEARCH_APP_ID 这些为什么分发？"

_血泪教训与反思：_ 以往如果底层金库定义了 `FEISHU_RESEARCH_APP_ID`，而配置中要求的是 `FEISHU_APP_ID`，我们会习惯于在某个启动脚本中插入 `export FEISHU_APP_ID=$FEISHU_RESEARCH_APP_ID`。
这是一种极其愚蠢的架构补丁行为（翻译层）！不仅徒增管理脚本的复杂性，一旦重连就会导致寻找不到映射。

- **架构师指令（老板固化）**：**禁止在代码与启动阶段对环境密钥进行再包装或重命名！** 所有的配置文件（例如 `openclaw_core.json`）必须强类型锁定、直接读取底层的真实金库键名（如直接写出 `"${FEISHU_RESEARCH_APP_ID}"`）。保持中枢配置与末端金库的命名绝对一致，实现端到端的 Zero-Translation！

## ⚡ npmmirror 强挂 (CN Regional Acceleration)

- Mandatory npm lock bypass for Edge Node setups.
- Use `npm config set registry https://registry.npmmirror.com` before executing `npm install` and `npm run build` on Node 02.
