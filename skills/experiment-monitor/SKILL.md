---
name: experiment-monitor
description: Local experiment monitor with macOS notifications, auto-analysis, and auto-queue-promotion for GPU experiments
---

# Experiment Monitor Skill

## Purpose

Autonomous local monitor that watches GPU experiment progress via SSH, providing:

- **macOS desktop notifications** for anomalies and completions
- **Auto-analysis** comparing finished experiments to baseline
- **Auto-promotion** of HOLD → PENDING tasks when GPU slots free up

## Architecture

```
[Local Mac]                        [GPU Server]
  monitor.py ──SSH──→  Queue JSON + Journals + nvidia-smi
      │                      │
      ├─ 🔔 macOS notify     ├─ auto_scheduler.py (omni-scheduler)
      ├─ 📊 /tmp/results.json├─ experiment_queue.json
      ├─ 🚨 /tmp/alert.txt   └─ logs/*_journal.jsonl
      └─ 🚀 HOLD→PENDING
```

## Usage

### Quick Start

```bash
# Start monitor (background, every 5 min)
nohup python3 /path/to/scripts/local_monitor.py > /tmp/calam_monitor_stdout.log 2>&1 &
```

### Configuration

Edit the constants at the top of `local_monitor.py`:

| Variable       | Default                                   | Description                  |
| -------------- | ----------------------------------------- | ---------------------------- |
| `SSH_TOOL`     | `openclaw/skills/ssh/scripts/ssh_tool.py` | SSH tool path                |
| `HOST`         | `10.190.30.220`                           | GPU server address           |
| `INTERVAL`     | `300` (5 min)                             | Check interval in seconds    |
| `MAX_GPUS`     | `4`                                       | Max GPUs for auto-promotion  |
| `ALERT_FILE`   | `/tmp/calam_alert.txt`                    | Alert signal file            |
| `RESULTS_FILE` | `/tmp/calam_results.json`                 | Completed experiment metrics |
| `LOG_FILE`     | `/tmp/calam_monitor.log`                  | Monitor log                  |

### Output Files

- **`/tmp/calam_monitor.log`** — Full monitor log with progress bars
- **`/tmp/calam_alert.txt`** — Exists only when there's an active alert
- **`/tmp/calam_results.json`** — Metrics for all completed experiments

### Adapting for Other Projects

To use with a different project:

1. **Change `REMOTE_STATUS` script** to import the correct `EXPERIMENT_MATRIX` and set `LOGDIR`
2. **Update post-gate assertions** in the analysis section (what counts as PASS/FAIL)
3. **Update queue path** (`QUEUE` variable in the remote script)

## Laws

> **Law #10 (Monitor Autonomy)**: The monitor runs locally, checks remotely. It MUST NOT execute experiments directly — only promote HOLD→PENDING for the scheduler to pick up.

> **Law #11 (Notification Discipline)**: Desktop notifications are for (1) anomalies, (2) experiment completions only. Do NOT spam notifications for routine progress.

## Anomaly Detection

The monitor detects:

- ❌ **FAILED tasks** in queue
- 💀 **Dead scheduler** (pgrep auto_scheduler)
- 🧊 **Ghost GPU** — RUNNING task but GPU memory = 0 MiB
- 🚫 **Post-gate FAIL** — experiment metrics outside expected bounds
