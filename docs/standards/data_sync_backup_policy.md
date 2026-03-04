# OpenClaw Data Sync and Backup Policy
**Status**: Draft (Under Review by Ops & Security)
**Author**: Antigravity Node 01
**Inspired by**: 老包 (Old Bao's Requirements)

## 1. 核心理念 (Core Philosophy)
数据不互通等于死亡，数据单点存放等于高危。
本规范确立了 OpenClaw 集群架构（Node 01, 02, 06）中各层级数据的流转规矩，确保“代码、配置、记忆、成果”能够跨地域实时一致且绝对防丢。

## 2. 跨节点多维同步圈 (The N-way Synchronization Ring)
我们抛弃传统的单向覆盖机制，采用基于**严格时间戳 (Timestamp)** 的去中心化 N-way 融合策略，以 Node 03 堡垒机作为汇流中枢 (Gateway Hub)。

### 2.1 Workspace 级同步
以下核心工作区在任何一台机器发生变更，必须自动传达到全网：
- `~/Documents/projects/openclaw/skills/`: Agent 的技能定义核心库。
- `~/Documents/projects/openclaw/docs/`: 包含本制度在内的项目宪法文档。

### 2.2 Antigravity 脑区同步 (Brain Connectivity)
- `~/.gemini/antigravity/brain/`: 包含操作复盘、`task.md`、生成的图片资产，以及核心消息队列 `XX_INBOX.md`。必须无损跨节点融合，确保 Node 02 和 Node 06 的“蛋蛋”能无缝接手 Node 01 的任务，且其产出的任务验收报告能同步回传。

### 2.3 执行协议 (Execution Protocol)
- **Unix 节点 (01, 02)**：使用 `rsync -avzu` 进行更新式拉取。
- **Windows 节点 (06)**：**严禁使用原生缓慢复制**。拉动时强制采用 `Aria2c -x 16 -s 16` 霰弹枪协议从堡垒机高速下载热压包并发解压，再使用 `robocopy /XO` 实施精准替换。

## 3. 金库级涉密数据备份 (Vault-Tier Backup Matrix)
### 3.1 凭证脱离开发区网络
所有 Node（01, 02, 03, 06）均将 API Keys、SSH跳板拓扑、云厂商 Token 收拢于宿主机的单一文件：`~/.openclaw_secrets/secrets.json`，且该文件处于 `openclaw/` 源码树之外。

### 3.2 Google Drive 自动冷备
为防范整站被盗或不可抗力损毁，Node 03 (堡垒机) 必须执行无声自动冷备：
- 工具链使用 `rclone` 工具挂载 `gdrive:`。
- 每天凌晨 **03:30 AM**，守护进程自动触发，将 `secrets.json` 单向复写倒出至 Google Drive 的 `OpenClaw_Backups/Secrets/` 文件夹下。

## 4. 强制调度与监控 (Enforced Scheduling)
为了避免人性的惰性打破物理一致性，“手动打线”只能作为特例存在。
- Node 01、02、06 必须注册各自操作系统的原生守护发令器（`crontab` 与 `Windows Task Scheduler`）。每天早晨 **07:00 AM** 全网准时共振发车，进行大混血。

---
> **[Action Required]**请运营专家与安全专家就上述《老包数据同步与防遗失反思录》的规范落笔进行探讨与交叉查验。如有异议，在此文档中批注后交由老板定夺。
