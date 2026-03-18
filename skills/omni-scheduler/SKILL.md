---
name: omni-scheduler
description: Dedicated hardware and network sentinel skill. Monitors GPU utilization and inter-node network vitality across the OpenClaw cluster architecture.
---

# `omni-scheduler` Skill

The `omni-scheduler` skill is a strictly scoped, read-only hardware observation tool. It is exclusively tasked with probing the physical infrastructure layer.

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
python3 $HOME/openclaw/skills/omni-scheduler/scripts/gpu_status_board.py
```

### 2. Cluster Network Dashboard

Pings and validates the SSH availability and network routes between the disparate cluster nodes.

```bash
python3 $HOME/openclaw/skills/omni-scheduler/scripts/cluster_net_dashboard.py
```

### 3. Unified Auto-Scheduler (The Polymorphic Dispatcher)

An active scheduler that periodically polls the shared JSON queue and fires tasks based on the operating mode: Local GPU or Kaggle Cloud.

**Key Difference**: Unlike `gpu_status_board.py` which is a _passive, one-off_ readout tool, this is an _active, long-running_ action trigger.

**🚨 THE NODE 01 DAEMON BAN 🚨**:
You are STRICTLY FORBIDDEN from running this script on Node 01. It must only be deployed on the Edge Gateway (Node 02) or directly on a local GPU Server.

**To run for Local GPUs**:

```bash
python3 $HOME/openclaw/skills/omni-scheduler/scripts/auto_scheduler.py \
  --mode local \
  --queue ~/workspace/projects_core/experiment_queue.json \
  --poll 1800 \
  --threshold 10.0
```

**To run for Kaggle Cloud**:

```bash
python3 $HOME/openclaw/skills/omni-scheduler/scripts/auto_scheduler.py \
  --mode kaggle \
  --queue ~/workspace/projects_core/experiment_queue.json \
  --target kaggle_account_A
```

### 4. Queue Lifecycle & Schema (Self-Managing JSON)

The `experiment_queue.json` file is the shared contract between the Agent (Producer) and the Daemon (Consumer).

- **The Schema**: Every task must be an object containing: `id` (uuid), `project` (str), `target` (str), `command` (str), `directory` (str), `status` (str), and `created_at` (ISO-8601).
- **The State Machine**:
  1. `PENDING`: Appended by the Agent/Boss. Waiting to be executed.
  2. `RUNNING`: Claimed by the Daemon via locking.
  3. `COMPLETED` / `FAILED`: Terminal states.
- **Garbage Collection (The 7-Day Prune)**: To prevent JSON bloat and UI crashing, the unified `auto_scheduler.py` automatically sweeps and deletes any `COMPLETED` or `FAILED` tasks that are older than 7 days during its poll cycle. No manual grooming is required.

### 5. Task Generation (The Producer CLI)

To safely inject tasks into the `experiment_queue.json` without risking JSON syntax corruption, both the Boss and the AI Agent **MUST** use the provided CLI:

```bash
python3 $HOME/openclaw/skills/omni-scheduler/scripts/enqueue_task.py \
  --project "CaLaM" \
  --command "conda run -n calam bash scripts/run_exp_02.sh" \
  --dir "~/workspace/projects_core/calam"
```

_This instantly appends the payload with a generated UUID and an exact timestamp._

## 🛡️ ANTI-HALLUCINATION LAWS (Production Incident Fixes)

> [!IMPORTANT]
> **Law #1 (Daemon Launch Protocol)**
>
> The scheduler daemon **MUST** be launched via `ssh_tool.py exec --detach` (which uses `setsid()` / `start_new_session=True`).
> **NEVER** use `nohup ... &` or raw `tmux` via Paramiko — both fail to survive SSH channel closure.
> The daemon **MUST** also set `signal(SIGHUP, SIG_IGN)` internally and use `t.daemon = False` for monitoring threads.

> [!IMPORTANT]
> **Law #2 (Git Sync Resilience)**
>
> `sync_queue_to_git()` and `pull_git_updates()` use **exponential backoff retry** (3 attempts: 5s/10s/20s).
> If all retries fail, the daemon continues running — **local JSON is always authoritative**.
> Git sync is "best-effort async"; it must **NEVER** block or crash the daemon.

> [!IMPORTANT]
> **Law #3 (Agent-Side SSoT Pull)**
>
> When querying experiment status, Agents must **SCP-download the remote JSON** (`ssh download`), not rely on `git pull`.
> The scheduler's `git push` can silently fail due to DNS/network issues.
> **Remote JSON is the SSoT**, Git is a replication channel, not the source of truth.

## ⚠️ CONSTITUTIONAL ANCHORS

- **Strategic Action Exemption**: While `cluster_net_dashboard` and `gpu_status_board` remain strictly read-only, the unified `auto_scheduler` possesses a specialized surgical exemption to execute pre-approved CLI commands from the `experiment_queue.json` solely to prevent expensive GPU idle time. It cannot arbitrarily modify parameters.
