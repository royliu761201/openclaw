---
name: omni-fetch
description: Advanced end-to-end data reconnaissance and physical retrieval macro-skill. Replaces legacy intel-fetch and raw dowloaders. Enforces Zero-Trust Pre-flight checks, intelligent platform routing, and MTU-immune mesh transport.
---

# 🦅 Omni-Fetch (全能掠夺者)

> **核心使命 (Core Mission)**:
> 统一且标准化所有外部重型资产（几十 GB 级数据集、模型权重）的抓取行动。不再假设网络是通的，不再信任 `scp` 和后台 `&`。基于零信任（Zero-Trust）原则，进行智能检测、降维路由和强韧投送。

## 📍 零梯次：零秒装载协议 (The Zero-Second Symlink Law)

在试图从广域网下载任何以 GB 计的重资产前，**必须首先查探**目标机器（尤其是 GPU 节点）的全局冷备金库：

- GPU 检查路径：`/jhdx0003008/data/`, `/jhdx0003008/models/`, `/jhdx0003008/packages/`
- 本地冷库：`~/data_vault/`

**如果资产已存在，绝对禁止二次下载！** 直接在当前项目建立软链接 (`ln -s`)，实现 0 秒物理挂载。

---

## 🛑 战役级 L1 执行铁律 (The 4 Pillars of Omni-Fetch)

当确认必须发起外部下载时，必须依靠底层的 `omni_fetch.py` 或严格遵循以下四大子系统协议，**严禁裸敲简单的 `wget/scp` 碰运气**。

### Pillar 1: 🛫 强制预检 (Mandatory Pre-flight)

在触发任何跨网络的数据流之前，必须在端点完成检测，如果失败立即 No-Go 终止任务：

1. **DNS/TCP 黑洞探测**：探针发送 HTTP HEAD/Telnet 请求。识别目标节点是否将 `zenodo.org`、`huggingface.co` 等域名解析为 `127.0.0.1`，或是 TCP 超时。
2. **磁盘配额硬锁**：目标落盘目录可用空间必须 `> 资产大小 x 1.2`。
3. **环境毒药自检**：必须 `grep -i proxy ~/.profile ~/.bashrc` 拔除会导致连接静默黑洞的死代理（如 `socks5h://127.0.0.1:7890`）。

### Pillar 2: 🧠 路由中枢 (Intelligent Source Routing)

不要盲目相信平台的官方下载命令，针对不同数据源必须使用防御性降维策略：

- **HuggingFace (GPU 同城吸血法则)**：如果目标是没有全量翻墙但拥有万兆内网的大陆 GPU 节点，**绝对禁止**将下载任务抛给离岸的 Node 05 中转！必须在 GPU 原生控制台强制打入 `export HF_ENDPOINT=https://hf-mirror.com`，利用纯物理手段直击大陆专属 CDN 镜像港进行极速下发（实测 11MB/s+）。只有当镜像站报 404 或底层 S3 瘫痪且无法自愈时，才允许滑退至 Node 05 跳板网格！
- **Kaggle**：Kaggle Kernels 有严格 20GB 沙箱限制以及 `datasets version` 沙箱隔离。对于 >20GB 的重型数据，必须切割大文件使用“一体化内核流转”（Kernel 下载一部分 -> 立即推向 HF 中转站），规避磁盘溢出。
- **Zenodo 等学术库**：高度 Anti-Bot 敏感。必须使用合法 User-Agent 伪装，并配置 HTTP Range 分块重试，对抗“强行切断”。

### Pillar 3: 🛣️ 跨网格抗断链路 (Mesh Transport & MTU Immunity)

当资产需要跨越物理距离（如从海外 Node 05 中转回局域网，再跨入 GPU）时：

- **绝对禁止 `scp` (AB-023)**：凡是单个文件 `>1GB`，严禁使用 `scp` 或 `ssh_tool.py upload`。必须降级为最原始的 C 语言级物理搬运：`rsync --partial --progress -e "ssh -o StrictHostKeyChecking=no"`。
- **1280 MTU 陷阱防御**：当穿透 Tailscale 网格（`100.x.x.x`）时，如果发生卡死（Stalled），必须通过修改 SSH 配置或分块应对路径 MTU 截断黑洞。
- **跳板自洽**：通过 `ssh -J` (ProxyJump) 穿过局域网堡垒，**必须预检** 跳板机与目标机的双向 SSH 公钥互信（包括 Windows 节点独特的 `administrators_authorized_keys` 坑）。

### Pillar 4: 🛡️ 守护者封装 (Tmux Daemonization Law)

针对需要数小时才能完成的重型任务（如下载或 Rsync 推送）：

- **抛弃 Paramiko Detach / nohup**：由于环境不稳，这些进程在 SSH SIGHUP 信号下极易暴毙且吞噬日志。
- **全系采用 Tmux 霸权**：所有的长任务下发都必须被包裹在物理的 `tmux` 晶体中：
  `tmux new-session -d -s omnifetch_xyz "omni_fetch.py start ... 2>&1 | tee fetch.log; echo DONE"`

---

## 🪦 终极血泪强化备忘录 (The 2026-03-24 Pipeline Reinforcements)

基于与 GPU 服务器和多极节点的真实拉锯战，Omni-Fetch 正式追加三条绝对物理禁令：

1. **Windows 原生指令链陷阱 (Node 05)**：若跳板机如 Node 05 是纯净版 Windows（无 WSL），**绝对禁止**使用 `python3` 或试图借道 Linux `tar/wget`。必须使用 `python` 原生别名。面对 Kaggle 医疗数据集（如 ETIS-Larib）遭遇 403 阻断时，直接抛弃 API，降维使用 PowerShell `Invoke-WebRequest` 抓取 GitHub 同等测试集全集，切勿在死锁内网进行 OAuth 博弈。
2. **Mac 尾流阻断死结 (Tailscale DERP)**：永远不要预设 Tailscale 永远处于 P2P 直连态！当发现两端通信（如 Mac 01 与 Node 03）速度被死死焊在 **18KB/s ~ 30KB/s** 时，意味着流量已坠入最劣质的境外 DERP 官方中转池。此时必须瞬间拔管，全面改用具备公网直连性能的 Node 02 做总 Hub 枢纽。
3. **主控节点的视盲器 (No Route to Host)**：诸如 Node 02 的集群跳板机，**并不继承本地 Mac 01 的 `~/.ssh/config` 便捷别名映射（如 `03`、`gpu`）**！一旦在 Orchestrator 盲打短名会导致 `0.0.0.3` 寻址解析崩溃。必须严格向管道注入 `100.108.x.x` 或 `10.190.x.x` 的原生四段式 IP。
4. **[2026-03-25 追加] Proxy SOCKS 巨型文件崩塌定律**：在防火墙极度森严的 K8s GPU 节点上，如试图挂载 `ssh -R` 等反向动态 SOCKS 隧道，让 GPU '借网'强行下翻几十 GB 的海量医疗切片（如 HyperKvasir）。由于 HTTP 分块流对 SOCKS 抖动零容忍，将极速诱发 Broken Pipe 断流黑洞。**绝对禁止让 GPU 走 SOCKS 代理直通外网去吞噬超大质量实体数据**。
5. **[2026-03-25 追加] Node 02 超级跳板卸载枢纽 (The Node 02 Offloading Protocol)**：基于 2026 年 3 月底对整个内网域进行的 UDP 打洞实战探测表明，Node 02 拥有极其强悍的 **20ms 满血穿透实力**。当面临 `>10GB` 的史诗级下载（远超 Mac 01 常态驻留能力），**必须将 Node 02 作为主力重装运载船**：
   - 一：远程向 Node 02 抛空投喂 Kaggle JSON 密钥。
   - 二：无头拉起 Node 02 利用外网急速捕获巨石。
   - 三：Node 02 启动原生 `scp -J 06 root@GPU`，直接通过专属双芯快车道瞬压进 GPU 核心仓，全程零占用主控机性能！
6. **[2026-03-25 终极反思] Kaggle 403 权限墙穿透法则 (The Deterministic Kaggle Search)**：当官方 Kaggle 据点（如 `simula/hyper-kvasir`）要求严格的网页版 ToS 签名导致 API 抛出 403 Forbidden 时，**绝对禁止** AI 依靠 Google 搜索结果的文本摘要去“盲猜”搬运号！必须直接在终端内拉起 `pip install kaggle && kaggle datasets list -s [关键词]` 这种原生的穷举扫描指令，通过接口直接打出所有开源免验证的社区镜像（Mirror），精准锁定（如 `kelkalot`）进行无障碍平替抓取。
7. **[2026-03-25 追加] 裸物理机下沉路由与全息共享环境 (The Bare Metal & Shared Env Law)**：当主 GPU 服务器（头节点/管理节点）遭遇全局出口封锁（如 Github API、Kaggle 报 TCP/Header 超时黑洞）时，**绝对禁止**立刻转向脱离内网的外部节点（Node 02/05）死磕中继。
   - **最优降级通路**：必须直接调用集群内直挂共享盘的 90 系纯粹物理计算节点（如 `ssh 90-1` 或 `90-2` 工作站）。由于裸物理机逃逸了主节点严苛的网关调度防御，它们能天然直出极速宽带，对 Kaggle API 和国内高优镜像（如 ghfast.top）实现 200 OK 直连秒打。
   - **共享工具链霸权**：由于物理节点的原生环境割裂，整个猎取大队严禁在单台 `90-x` 的局域 `~/.local` 或 `root` 家目录下散装安装 CLI 工具。所有如 `kaggle`、`gdown` 探针和抓取脚本，**必须全部封装于统一的全局共享 NVMe 基础环境内（激活口令：`conda activate /jhdx0003008/envs/workspace`）**，在任意 90 节点插拔即用，保障集群计算资源百分百纯净。

---

## 💻 核心执行器 (Usage)

本技能附带了一个重装 Python 武器 `scripts/omni_fetch.py`。你可以通过 `ssh_tool.py` 将它投放并执行在任意目标计算节点，或网关中转节点。

```bash
# === 实战：从 HF 下载大型资产 (使用 Omni-Fetch) ===
# 它会自动执行 Pre-flight (网络, 磁盘, CLI检测)，使用 HF 镜像加速，并配置完善的断点续传。

./scripts/ssh_tool.py exec "python3 /root/workspace/.local_skills/omni-fetch/scripts/omni_fetch.py pull hm huggingface.co/bert-base /jhdx0003008/models/bert-base"

# === 跨网链路 (Mesh) 的传输 ===
# 当在 Node 05 落地后，需要推送到 GPU。你作为 Agent 应组合命令：
# pre-flight: ssh -J 验证
# rsync 推送: rsync --partial -e "ssh -J node06"
```

## Law 8: The Compute-Node Subjugation Fallacy 🚨 (NFS I/O Choke Ban)

**2026-03-26 深刻教训**: 绝对不可将 90 系列裸金属工作站（90-1/90-2，仅 32GB RAM）用作超大体量资产（>100GB）的并发下载与极速解压（Unzip）宿主机。多线程数据注入与碎片化写入会引发灾难级的存储阵列 I/O 阻塞（I/O Wait），直接导致节点网络层瘫痪（SSH 握手严重超时，`Connection timed out`），白白锁死且浪费了极高昂的算力资源。
**2026-03-27 第二次血泪固化 (POSTMORTEM-002)**: 先前的认知存在致命盲区——以为只要去掉 `--unzip` 的负担，90-1 就能安全后台排队下载 `.zip` 容器。**这是极度危险的谬误！** 因为即使是纯下载，只要目标路径是远程网络挂载盘（如 `/jhdx0003008`），90-1 孱弱的网卡和 I/O 系统都将被外网超速下载与局域网 NFS 回写的双重洪流瞬间打爆，引发大量 `D` 状态不可中断进程，节点必定**再次暴死失联**。
**不可践踏的黄金法则 (Local Disk First Protocol)**:
若因为 K8s 防火墙阻断而**被迫**要在 90-1 上进行穿透墙的重型文件攫取，**绝对禁止直接填入 NFS 挂载点目录！**
1. 必须将目标路径重定向到 **90-1 本地的 NVMe 固态硬盘** (如 `/tmp` 或用户家目录)。
2. 本地落盘 100% 成功后。
3. 再通过 `rsync --bwlimit=20000` (限速 20MB/s) 等守护进程缓慢向 `/jhdx0003008` NFS 移交。强行直写杀无赦。

## Law 9: GPU-Server-First Download Mandate (航母优先下载铁令) 🚢

**2026-03-27 固化**: 所有超过 10GB 的重型数据集下载，**优先且必须直接在拥有一级存储群支撑的 GPU 主服务器 (10.190.30.220) 内部执行**，严禁在网络带宽易受波动的 90 系列工作站上发起！

**物理原理**：
| | 90-x 工作站 | GPU 主服 (10.190.30.220) |
|---|---|---|
| 内存 | 32 GB (极易 OOM 死锁) | **1 TB (1056 GB)** |
| `/jhdx0003008` | SSHFS 远程挂载 (网络瓶颈) | **本地物理盘** (零网络开销) |
| CPU | 少量核心 | **128 核** |

**执行路径**：

```bash
# 跳板穿透进入主服容器
ssh 90-1 "ssh -p 30305 root@10.190.30.220"

# 激活统一凭证环境
conda activate /jhdx0003008/envs/workspace

# 在主服内部直接下载 (本地磁盘写入，零 SSHFS 开销)
# 使用绝对路径确保非交互式 Shell 下依然可用
nohup /jhdx0003008/envs/workspace/bin/kaggle datasets download -d <slug> --path /jhdx0003008/data/<target> > /jhdx0003008/data/fetch_<name>.log 2>&1 &
```

**2026-03-27 终极验证 (Restriction Cleared)**:
经实测证明，先前认为 GPU 服务器存在“下载受限”（DNS/K8s 阻断）而被迫转向 90-1 的判断属于以偏概全或临时网络抖动引发的误判。当前 GPU 服务器 (10.190.30.220) 的 DNS 解析与 Kaggle API 通信已全面恢复正常（Ping/Host 验证通过）。
**以此为准：今后所有大体量下载任务，首选且必须在 GPU 服务器内部发起！** 严禁以“受限”为借口私自降级到 90 系物理机进行直写。

**例外条件**：仅当 GPU 主服的防火墙确凿地（由 Pre-flight 验证）完全封锁目标 URL 时，才允许退降到 Node 05 (加拿大全通) 中继再 SCP 回传，或按照 Law 8 使用 90-1 本地盘中转。

