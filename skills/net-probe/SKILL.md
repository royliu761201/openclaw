---
name: net-probe
description: Use when you need to verify network topology, port reachability, or SSH gateway status BEFORE executing heavy cross-node commands.
---

# 📡 Net-Probe 跨网格探针技能

> **诞生基因**: 基于《GEMINI_L1_CONSTITUTION.md》中的 **Rule 10 (拓扑情报与凭证先导法则)** 提炼而来。

本技能用于在执行任何重量级跨节点操作（如大文件 `scp`、启动远程大模型服务、跨越 TLS 阻断的 Node 02/03 同步）前，进行**轻量级的连通性盲测**。

## 🎯 核心场景 (When to Use)

1. **环境探路**: 在写复杂的远端 Python / Bash 脚本前，先用此技能验证目标节点是否存活。
2. **端口审计**: 验证穿透隧道的映射端口（如 `2235`，`8080`）是否已通。
3. **消除幻觉**: 禁止直接硬编码重试 `ssh` 连接。如果断了，先用探针诊断 L3/L4 连通性。

## 🛠️ 使用指南 (How to Use)

### 1. 基础连通性探测 (Basic Port Probe)

本工具提供了一个极度轻量的 `nc` (Netcat) 探针脚本，用于安全探测任意主机的 TCP 端口。

**命令语法:**
```bash
/Users/roy-jd/Documents/projects/openclaw/skills/net-probe/scripts/probe.sh <target_host_or_ip> [port] [timeout_seconds]
```

**实战示例:**
探测 Node-02 的 SSH 端口是否连通（默认超时 3 秒）：
```bash
/Users/roy-jd/Documents/projects/openclaw/skills/net-probe/scripts/probe.sh node-02 22
```

探测本地映射的 Node-03 穿透端口：
```bash
/Users/roy-jd/Documents/projects/openclaw/skills/net-probe/scripts/probe.sh 127.0.0.1 2235 5
```

### 2. SSH 隧道盲测 (SSH Tunnel Diagnosis)

若常规端口阻断（如 GFW TLS Timeout），你应当主动使用以下命令拉起一个免配的背景隧道进行连通性审计（不要写死在代码里，先用纯命令探路）：

```bash
# 诊断 Node-03 联通性，静默退出
ssh -q -o BatchMode=yes -o ConnectTimeout=5 node-03 exit
echo $? # 如果是 0 即连通，255 即阻断
```

## 🚫 探针修养防线 (Anti-Hallucination Guardrails)

- **绝对禁止盲人摸象**: 如果 `net-probe` 探测目标端口返回 `Exit 1`（Unreachable），**立刻中止**任何针对该端口的代码部署或大文件传输行为。你必须先转回网络排障模式（如检查 `nc` 状态，检查跳板机）。
- **禁止造轮子**: 不要为了测个端口去写 `import socket` 的 python 脚本。强制调用本技能提供的 `probe.sh`。

### 3. 全网格上帝视角仪表盘 (Cluster Network Dashboard)
在决定是否拉取大模型、是否下放训练任务前，直接呼叫仪表盘获取全网的真实外网带宽和过墙拓扑：
```bash
python3 /Users/roy-jd/Documents/projects/openclaw/skills/workspace/scripts/cluster_net_dashboard.py
```
*此工具将并发盲测全系节点对 Google/HF/Aliyun 的出站能力。*

### 4. GPU 算力高塔巡检 (GPU Forge Status Board)
部署深度学习任务前，不要盲测，秒级启动 GPU 仪表盘获取实时利用率与显存：
```bash
python3 /Users/roy-jd/Documents/projects/openclaw/skills/workspace/scripts/gpu_status_board.py
```
