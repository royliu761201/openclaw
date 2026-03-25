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
tmux new-session -d -s scheduler "python3 $HOME/openclaw/skills/omni-scheduler/scripts/auto_scheduler.py \
  --mode local \
  --queue ~/workspace/projects_core/experiment_queue.json \
  --poll 30 \
  --max-gpus 4"
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
> **Law #1 (Daemon Launch Protocol - Updated 2026-03-20)**
>
> The scheduler daemon **MUST** be launched via **tmux**.
> **NEVER** use `nohup ... &` as it makes log monitoring and process management messy.
>
> **Correct Launch Command**:
> `tmux new-session -d -s scheduler "python3 scripts/auto_scheduler.py ..."`
>
> This guarantees the scheduler survives SSH disconnection and its logs can be attached to at any time via `tmux attach -t scheduler`.

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

> [!CAUTION]
> **Law #4 (Air-Gapped Dispatch SOP — Production Incident Fix 2026-03-19)**
>
> On air-gapped GPU nodes (no public DNS), `auto_scheduler.py` **CANNOT** git pull new tasks.
> Git push from local is for **record-keeping only**. The actual dispatch MUST use SCP.
>
> **Mandatory 6-Step Dispatch Flow:**
>
> ```
> 1. ssh download  GPU queue → local       (GPU JSON is SSoT)
> 2. enqueue_task.py                       (inject task locally)
> 2.5 ssh exec: data path preflight        (verify ALL data_path exist + are files, NOT dirs)
> 3. git commit + push                     (record-keeping)
> 4. ssh upload   local queue → GPU        (PRIMARY dispatch channel)
> 5. sleep 90s → ssh exec check status     (verify RUNNING)
> ```
>
> **Step 2.5 is MANDATORY.** For each task, SSH to GPU and verify:
>
> - `os.path.isfile(data_path)` → True (not directory, not missing)
> - If data_path is a CSV/JSON, confirm it can be opened with at least 1 row
> - If check fails, FIX before proceeding to Step 3. Do NOT waste GPU time on bad paths.
>
> **Step 5 is NOT optional.** If task status != RUNNING after 90s, alert Boss immediately.
> **NEVER** assume git sync will work on air-gapped nodes. SCP is the primary channel.

> [!CAUTION]
> **Law #5 (GPU Isolation — Production Incident Fix 2026-03-19)**
>
> When running parallel experiments on multi-GPU nodes via `conda run`:
>
> **Shell-level `CUDA_VISIBLE_DEVICES` DOES NOT WORK.** `conda run` resets environment variables.
>
> **The ONLY reliable method:** Set `os.environ['CUDA_VISIBLE_DEVICES']` **inside Python, BEFORE `import torch`**.
>
> Every experiment script that supports multi-GPU parallel execution **MUST** have a `--gpu` argument:
>
> ```python
> # BEFORE any torch imports:
> import sys, os
> if '--gpu' in sys.argv:
>     os.environ['CUDA_VISIBLE_DEVICES'] = sys.argv[sys.argv.index('--gpu') + 1]
> import torch  # Now torch only sees the specified GPU
> ```
>
> **Applies to ALL projects** (CaLaM, PhysDiff, PESSO, Frenet).
> If a new experiment script is created without `--gpu` support, it **CANNOT** be used in parallel sweeps.

> [!CAUTION]
> **Law #6 (MD-Driven Verification — Design Decision 2026-03-19)**
>
> **Experiment completion verification is driven by PDCA markdown, NOT by automated scripts.**
>
> When an experiment task transitions to COMPLETED:
>
> 1. Agent **proactively** pulls results from W&B (SSoT)
> 2. Agent compares results against the PDCA **Check section** criteria
> 3. Agent updates PDCA with actual metrics, flags anomalies with ⚠️
> 4. Agent notifies Boss if any Check criterion fails
>
> **Why not scripts?** Different projects need different verification. The PDCA Check section
> already defines project-specific criteria in human-readable form. Scripts that nobody reads = waste.
>
> **Execution discipline > automation tooling.** Don't wait for Boss to ask "what are the results?"

> [!CAUTION]
> **Law #7 (Paper-Code Semantic Audit — Production Incident Fix 2026-03-19)**
>
> **Pre-flight MUST include paper↔code semantic verification, not just "exit 0".**
>
> Before launching any experiment that implements a paper's algorithm:
>
> 1. **Trace parameter flow**: config value → argparse → function call → math operation
> 2. **Match against paper equation**: verify the code implements the exact formula
> 3. **Verify value ranges**: if paper says `α ∈ [0,1]`, confirm code bounds it (sigmoid, clamp, etc.)
> 4. **Different configs → different outputs**: quick sanity check that varying a parameter actually changes the result
>
> **Incident**: `α` parameter was set to 2/5/10 in config, but `risk_model` output (≈6.95, unbounded)
> replaced it every step. Paper defined `α_t = sigmoid(a·r_t + c)` but code used raw `risk_score` as `alpha`.
> Result: 6 experiments produced identical data, all wasted.
>
> **"Exit 0" is not validation. Correct output requires correct math.**

> [!CAUTION]
> **Law #8 (Kill Safety — Production Incident 2026-03-19)**
>
> **NEVER batch-kill processes by pattern.** Pattern-based `pkill -f` or `grep | kill` is a
> destructive operation that can hit valid experiments.
>
> **Mandatory kill procedure:**
>
> 1. `ps aux | grep <target>` — list PIDs + full command lines
> 2. **Show Boss the list** — confirm which PIDs to kill
> 3. `kill <PID>` one by one — never `pkill -f <pattern>`
>
> **Incident**: `kill -9` with broad grep filter killed vanilla_rtp (2.5h, 33% done)
> and pplm_rtp (2.5h, 22% done). Hours of GPU compute wasted.
>
> **This is an L0 Anti-Destruction Anchor violation.** No exceptions.

> [!CAUTION]
> **Law #9 (Single Dispatch Entry — Production Incident 2026-03-19/20)**
>
> **ALL experiments MUST be launched via `experiment_queue.json` + `auto_scheduler` ONLY.**
> Manual `nohup` is PROHIBITED. It causes:
>
> 1. Queue state desynchronization (hand-launched won't update JSON)
> 2. Scheduler re-launches the same task → duplicate processes
> 3. Concurrent journal writes → data corruption
>
> **Four-Layer Defense enforced in code:**
>
> - Layer 1: Pre-launch guard (`pgrep` detects duplicates)
> - Layer 2: Journal `flock()` (exclusive write lock)
> - Layer 3: Singleton check (only one scheduler instance)
> - Layer 4: Health alert (`/tmp/scheduler_alert.txt`)

> [!IMPORTANT]
> **Law #10 (Daemon Surgeon & Quota Integrity — Production Incident Fix 2026-03-24)**
>
> **1. Zombie JSON Locks**: If the Python daemon hard-crashes (or is killed via `pkill`), any tasks it was actively chewing remain tagged as `"status": "RUNNING"` with `"assigned_gpu"` in the JSON. The newly restarted daemon will blindly trust these locks and falsely assume GPUs are busy, starving the queue.
> **Fix**: You MUST run a scrubber script on the JSON to downgrade these abandoned tags back to `"PENDING"` before cold-booting the new daemon.
>
> **2. Quota Isolation**: When running multiple projects (e.g. CaLaM vs PESSO), the daemon MUST enforce the JSON `gpu_quota` dict. Without `if project_counts.get(proj, 0) >= quotas.get(proj, 99): continue`, the daemon defaults to a greedy "First-In-First-Out" sweep, starving tail-end payloads. Any patched `auto_scheduler` must retain this logic.

## ⚠️ CONSTITUTIONAL ANCHORS

- **Strategic Action Exemption**: While `cluster_net_dashboard` and `gpu_status_board` remain strictly read-only, the unified `auto_scheduler` possesses a specialized surgical exemption to execute pre-approved CLI commands from the `experiment_queue.json` solely to prevent expensive GPU idle time. It cannot arbitrarily modify parameters.

> [!IMPORTANT]
> **Law #11 (The Zombie Reaper Protocol — Production Incident Fix 2026-03-24)**
>
> A built-in garbage collection mechanism inside `auto_scheduler.py` performs rigorous multi-dimensional anomaly detection every cycle to clean up 0% utilization "Hung Processes" or missing PIDs.
>
> 1. **Hung at 0% GPU**: If a task has been running > 1 hour, but GPU utilization remains strictly <= 1.0%, the daemon assumes it is a deadlocked process (e.g. W&B `CommError` with background thread zombies), force-kills it via `pkill -9`, and marks it `FAILED` with `reaper_reason`.
> 2. **24h Timeout**: Absolute timeout; processes spanning >24h are killed and aborted to prevent infinite locking.
> 3. **Orphaned Lock**: If the JSON queue claims a task is `RUNNING`, but `pgrep` cannot find the process in the OS (e.g. container hard crash), the lock is instantly discarded.

> [!CAUTION]
> **Law #12 (The SSoT Anti-Shortcut Dictate — Production Incident Fix 2026-03-24)**
>
> **NEVER use `scp` to hot-patch code bypassing version control.**
> If code needs fixing (e.g. baseline architecture changes), you MUST:
>
> 1. Edit the files on the designated SSoT repository (Mac).
> 2. `git commit` and `git push` to the remote origin.
> 3. `ssh` to the GPU cluster and `git pull`.
>    **Violating this fractures the Git tree, causes silent execution drift, and bypasses formal architectural audits.**

> [!IMPORTANT]
> **Law #13 (Constitutional Tracking Identifier — Fail-Fast Guard)**
>
> The daemon scheduler MUST instantly abort any experimental payloads that do not map the `--task <name>` argument.
> Without `--task`, the Zombie Reaper and Duplicate Tracker natively break, leading to unobservable multi-GPU starvation deadlocks. This Fail-Fast ensures runtime tracking integrity.

> [!IMPORTANT]
> **Law #14 (The Zombie Reaper String Parsing Flaw — Production Incident Fix 2026-03-24)**
>
> When using `pgrep -f` to track string matches in the OS process table, if the search term starts with a double dash (like `--task calam`), `pgrep` will misinterpret it as an illegal command line flag and immediately crash with a non-zero exit code. This causes the scheduler to falsely assume the process is dead (the "Orphaned Lock" hallucination), aggressively killing and marking all healthy tasks as `FAILED`.
> **Fix**: You MUST explicitly inject a `--` terminator before the search string to force literal evaluation: `pgrep -f -- "--task {name}"`.

> [!IMPORTANT]
> **Law #15 (GFW Network Immunization & Git SSoT Bridge — Production Incident Fix 2026-03-25)**
>
> **1. W&B TCP Reset Crash (`WANDB_MODE=offline`)**: In strict GFW-proxied GPU clusters, long-lived metrics telemetry connections (like W&B) over port 443 are routinely subjected to TCP Connection Resets (`ConnectionResetError`). Because `wandb` operates synchronously in the main thread by default on crash, it will drag down the entire training process (Exit Code 125).
> **Fix**: Always forcefully inject `env["WANDB_MODE"] = "offline"` into the dataset generation/training subprocess OS environments, forcing W&B to cache telemetry to disk entirely offline. Manual `wandb sync` can push data later.
>
> **2. The Git SSH Port Override Desync**: Hardcoding `GIT_SSH_COMMAND="ssh -o Port=443 -o HostName=ssh.github.com"` in Python explicitly bypasses standard proxy settings in the host's `~/.ssh/config`. If DNS resolution for `ssh.github.com` fails, Git fetching drops dead.
> **Fix**: Rely entirely on the host's native `ssh` and git configurations. Remove all hard-coded network TLS overrides from the python scheduling daemon to ensure it inherits the cluster's resilient proxy tunnels.
