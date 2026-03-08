---
description: 强制全网格算力与存储物理拓扑探查，严防硬件级“降维或越权幻觉”。
name: ontology
---

# Ontology (系统全息物理拓扑探针)

这个核心技能的诞生是为了彻底根绝 AI Agent 在调度任务时产生的**物理拓扑幻觉**。
在过去，Agent 会因为某个节点叫 `Node 02` 或者 `remote`，就不假思索地调用它去下载百GB数据集或跑深度学习训练，导致网关节点被当场击穿。

为了捍卫 OpenClaw 算力网格的稳定，**任何 Agent 在试图发起跨端通信、带宽转移、大模型查探或计算下发时，必须首先调用本技能！** 这是一切行动的前提！

## 🚨 拓扑寻址最高防线 (Top-Level Topology Defense)

你必须始终将 Ontology 视作你的“物理侦察兵”。

1. **先问路，后发兵**: 在你决定要把任何任务 (哪怕只是 `wget` 一个文件) 发送到任何一个远端之前，**强制**执行 `ontology.py query --type Node` 获取该节点此时此刻的物理定位与角色。
2. **严禁望文生义 (No Assumption)**:
   - 绝不允许看到 `Node` 就认为有算力！
   - 绝不允许看到 `Server` 就认为网速快！
3. **刻入骨髓的物理映射 (The Absolute Truth)**:
   这是系统当前的客观物理法则，如有违背，即视为最致命的拓扑幻觉：
   - **`Node 01`**: Master Control (主脑中控，也就是你现在所在的机器)。
   - **`Node 02`**: Edge Gateway (边缘快递员，**严守零负载状态 Zero-Weight，绝对禁止跑计算实验/存大文件**)。
   - **`Node 03`**: Data Vault (冷备金库，纯 CPU 存储，跑不动 CUDA)。
   - **`GPU Server (10.190.*)`**: Air-Gapped Tensor Forge (全网**唯一**合规用于重型 AI 实验、大容量落盘 `/jhdx0003008/` 的禁区)。

## 使用指引 (Usage)

Ontology 的本体数据库是一个纯文本 JSONL (`graph.jsonl`)，位于 `docs/system_core/memory_core/ontology/` 下。

### 探底可用节点 (Probe All Nodes)

```bash
python3 /Users/roy-jd/openclaw/skills/ontology/scripts/ontology.py list --type Node
```

_如果查出来对方 Role 不是 Tensor Forge，就给我把大模型收起来！_

### 查证特定策略 (Lookup Policies)

```bash
python3 /Users/roy-jd/openclaw/skills/ontology/scripts/ontology.py query --type Policy --where '{"scope":"workspace"}'
```

记住：**Ontology 是 OpenClaw 物理世界的唯一真理 (SSoT)。不查此表盲打错配者，罪无可恕。**
