---
name: cluster-monitor
description: Dedicated hardware and network sentinel skill. Monitors GPU utilization and inter-node network vitality across the OpenClaw cluster architecture.
---

# `cluster-monitor` Skill

The `cluster-monitor` skill is a strictly scoped, read-only hardware observation tool. It is exclusively tasked with probing the physical infrastructure layer.

## ⚡️ TRIGGER RULES

You MUST execute this skill when:

- The user requests the current status of the computing cluster.
- The user asks about GPU memory, VRAM availability, or running processes.
- The user requests to check connectivity between Node 01, 02, 03, or 05.

## 🛠️ USAGE (Pure MD-Driven SOP)

### 1. GPU Status Board Check

Probes all registered nodes via SSH to extract `nvidia-smi` readouts and process lists.

```bash
python3 $HOME/openclaw/skills/cluster-monitor/scripts/gpu_status_board.py
```

### 2. Cluster Network Dashboard

Pings and validates the SSH availability and network routes between the disparate cluster nodes.

```bash
python3 $HOME/openclaw/skills/cluster-monitor/scripts/cluster_net_dashboard.py
```

## ⚠️ CONSTITUTIONAL ANCHORS

- **Read-Only Purity**: This skill contains ZERO write access. It cannot kill jobs or modify limits; it is strictly a reporting sentinel.
