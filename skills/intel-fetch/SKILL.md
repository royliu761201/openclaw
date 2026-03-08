---
name: intel-fetch
description: Advanced data reconnaissance and retrieval macro-skill. Replaces legacy downloaders. Enforces the "Data Follows Compute" protocol and handles proxy bouncing.
---

# 🦅 Intel Fetch (全域数据掠夺者)

> **核心使命 (Core Mission)**:
> 统一且标准化所有外部数据、模型权重的抓取行动。本技能全面吸收并替代了旧时代的 `gpu-downloader` 和零散的爬虫脚本。

## 📍 第一梯次：数据锚地探明 (The Symlink-First Protocol)

在试图从广域网下载任何以 GB 计的重型资产（如 HuggingFace 模型、Kaggle 数据集）前，Agent **必须首先查探**目标机器（尤其是 GPU 节点）的全局冷备金库：
- GPU 节点检查路径：`/jhdx0003008/data/`, `/models/`, `/packages/`
- Node 03 检查路径：`~/openclaw_data/wheels_vault/`

**如果资产已存在，绝对禁止二次下载！** 直接在当前项目工作区建立软链接 (`ln -s`)，实现 0 秒装载。

---

## 🚀 第二梯次：高维渗透抓取 (The Cascading Fetch Workflow)

如果在金库中未找到资产，必须严格遵循以下“数据找算力”的级联抓取协议。**你（Agent）是唯一的指挥大脑，严禁写死一个巨型 Python 脚本来统管全局。你必须使用 `ssh_tool.py` 操控各节点。**

### T1: 目标直连尝试 (Direct Node Fetch)
1. 使用 `ssh_tool.py` 登录目标执行节点（例如 Node 02 或 GPU）。
2. 在该节点的冷备区 (`~/data_vault/` 或 `/tmp/`) 下达最基础的下载命令：
   - **Kaggle**: `kaggle datasets download -d <dataset>`
   - **HuggingFace**: `huggingface-cli download <model>`
   - **通用**: `wget -c`, `curl -L -O`
*(如果你预判目标节点（比如局域网 Node 02/03）根本没有公网能力，直接跳过直连，进入 T2)*

### T2: 桥接跳板渗透 (The Node 05 Proxy Bypass)
当目标节点处于 GFW 墙内、代理断流、或物理断网时，必须果断启动跳板策略：
1. **呼叫 Node 05 (US Proxy)**：通过 `ssh_tool.py` 操控具备自由外网的 Node 05，命令其将资产高速拉取至 `/tmp/` 缓存栈。
2. **内网折返空投**:
   - 使用 `ssh_tool.py download` 将 /tmp 资产从 Node 05 抽回主控阵地（如 Node 01）。
   - 立即背靠背使用 `ssh_tool.py upload` 将资产精准制导到无网的 Target Node。
### T3: 灾装备份回传 (Vault Replication)
这是形成数据闭环的最后一步。当几十 GB 的重资产被成功拉取并安置在 GPU 端 (或 Node 02 等计算节点) 后，**必须立刻建立冷备**：
1. 通过 `ssh_tool.py download` 将该资产从 GPU 下载回跳机/主控节点。
2. 立即通过 `ssh_tool.py upload` 将资产传输至 Node 03 终极金库 (`~/data_vault/models/` 或 `~/data_vault/datasets/`) 永久封存。
从而保证未来其它节点再次需要该数据时，100% 触发第一梯次的 `Symlink` 零秒下发！

---

## 🛡️ 第三梯次：沙盒物理隔断 (L1 Compliance)

1. 通过本 `intel-fetch` 获取的任何数据存放目录，必须第一时间被写入项目内的 `.gitignore`，防止 Git 仓库被核爆。
2. 若 `intel-fetch` 会调用复杂的 Python 爬虫逻辑去解析网页，该 Python 脚本必须在顶部植入 L1 Constitution 第12条 **沙盒囚禁锁** (`in_venv = sys.prefix != sys.base_prefix`)。

## ⚡ 触发条件 (TRIGGER RULE)

**何时拔出此剑？**
本技能优先级无限高，只要长官下达类似以下内容的指令，**强制立刻触发**：
- *"帮我把 XXX Kaggle 数据集下载到本地"*
- *"去 HF 上把 XXX 权重拉回 Node 02 / GPU"*
- *"部署 XXX 环境，它需要好几个 G 的外部预训练缓存"*

**只要任务涉及从外网获取几百 MB 以上的重型资产，绝对禁止本地盲目裸敲 `wget` 或随意写爬虫。必须 100% 遵照本《智能掠夺协议》，由 Agent 高能大脑亲自接管跳板路由！**

---

## 💻 战斗执行演示 (Execution Example)

本技能 **没有** 专用的 Python 脚本堡垒。**你（Agent 自身）就是这个宏技能的大脑**！你需要像战区指挥官一样，组合调用现有的 `ssh_tool.py` 肌肉来完成这套高阶战术动作：

```bash
# === 实战案例：帮长官把 HF 上的 BERT 拉到断网的 Node 02 金库 ===

# 战术动作 1: 查询全局金库底座 (查重防爆)
python3 ../ssh/scripts/ssh_tool.py --host 03 exec "ls ~/data_vault/models/bert-base-uncased"

# 战术动作 2: 若金库没有，动用 Node 05 美国兵营强行外网空投至临时区
python3 ../ssh/scripts/ssh_tool.py --host node05 exec "huggingface-cli download bert-base-uncased --local-dir /tmp/bert-base"

# 战术动作 3: 内网折返空投，抽回避难所
python3 ../ssh/scripts/ssh_tool.py download --host node05 /tmp/bert-base ./bert-tmp

# 战术动作 4: 洲际导弹制导 (砸入彻底无外网的 Node 02 金库)
python3 ../ssh/scripts/ssh_tool.py upload --host 02 ./bert-tmp /Volumes/Macintosh_HD/data_vault/models/bert-base

# 战术动作 5: 炸毁跳板机 (Node 05) 上的重资产残渣
python3 ../ssh/scripts/ssh_tool.py --host node05 exec "rm -rf /tmp/bert-base"

# 战术动作 6: 建立本战区项目的软链接 (Zero-Second Load)
cd ~/workspace/projects_core/my_nlp_project/data
ln -s /Volumes/Macintosh_HD/data_vault/models/bert-base ./model_weights
```

```bash
# === 实操案例 2：GPU 内部重资产的软链寄生 (Zero-Second Local Fetch) ===

# 战术行动 1: 探查 GPU 算力枢纽的金库储备
python3 ../ssh/scripts/ssh_tool.py --host 10.190.30.220 exec "ls /jhdx0003008/models/Llama3"

# 战术行动 2: 确认已存在！100% 严禁产生任何全量网络拉取与物理复制
# 直接以 Zero-Copy 的形式建立软链至计算任务沙盒
python3 ../ssh/scripts/ssh_tool.py --host 10.190.30.220 exec "ln -s /jhdx0003008/models/Llama3 /root/workspace/projects_core/my_target_project/models/Llama3_Local"
```
