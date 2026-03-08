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
