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
- The user asks to "prevent GPU idle time", "start the zero-idle daemon", or automatically process the experiment queue.

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

### 3. Zero-Idle GPU Daemon (The Long Poller)

A background daemon that periodically checks local `nvidia-smi` and fires `git push` or local execution tasks from a JSON queue if VRAM utilization stays below a threshold.

**🚨 THE NODE 01 DAEMON BAN 🚨**:
You are STRICTLY FORBIDDEN from running this script on Node 01. It must only be deployed on the Edge Gateway (Node 02) or directly on a local GPU Server.

```bash
python3 $HOME/openclaw/skills/cluster-monitor/scripts/zero_idle_daemon.py \
  --queue ~/workspace/projects_core/experiment_queue.json \
  --poll 1800 \
  --threshold 10.0
```

## ⚠️ CONSTITUTIONAL ANCHORS

- **Strategic Action Exemption**: While `cluster_net_dashboard` and `gpu_status_board` remain strictly read-only, the `zero_idle_daemon` possesses a specialized surgical exemption to execute pre-approved CLI commands from the `experiment_queue.json` solely to prevent expensive GPU idle time. It cannot arbitrarily modify parameters.
