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

### 3. GPU Auto-Scheduler (The Active Consumer)

An active scheduler that periodically checks local `nvidia-smi` and fires `git push` or local execution tasks from a JSON queue if VRAM utilization stays below a threshold.
**Key Difference**: Unlike `gpu_status_board.py` which is a _passive, one-off_ readout tool, this is an _active, long-running_ action trigger.

**🚨 THE NODE 01 DAEMON BAN 🚨**:
You are STRICTLY FORBIDDEN from running this script on Node 01. It must only be deployed on the Edge Gateway (Node 02) or directly on a local GPU Server.

```bash
python3 $HOME/openclaw/skills/cluster-monitor/scripts/gpu_auto_scheduler.py \
  --queue ~/workspace/projects_core/experiment_queue.json \
  --poll 1800 \
  --threshold 10.0
```

### 4. Queue Lifecycle & Schema (Self-Managing JSON)

The `experiment_queue.json` file is the shared contract between the Agent (Producer) and the Daemon (Consumer).

- **The Schema**: Every task must be an object containing: `id` (uuid), `project` (str), `command` (str), `directory` (str), `status` (str), and `created_at` (ISO-8601).
- **The State Machine**:
  1. `PENDING`: Appended by the Agent/Boss. Waiting to be executed.
  2. `RUNNING`: Claimed by the Daemon via locking.
  3. `COMPLETED` / `FAILED`: Terminal states.
- **Garbage Collection (The 7-Day Prune)**: To prevent JSON bloat and UI crashing, the `gpu_auto_scheduler.py` automatically sweeps and deletes any `COMPLETED` or `FAILED` tasks that are older than 7 days during its poll cycle. No manual grooming is required.

## ⚠️ CONSTITUTIONAL ANCHORS

- **Strategic Action Exemption**: While `cluster_net_dashboard` and `gpu_status_board` remain strictly read-only, the `gpu_auto_scheduler` possesses a specialized surgical exemption to execute pre-approved CLI commands from the `experiment_queue.json` solely to prevent expensive GPU idle time. It cannot arbitrarily modify parameters.
