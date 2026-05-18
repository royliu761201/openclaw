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
bash $HOME/openclaw/skills/omni-scheduler/scripts/start_scheduler.sh
```

> **CRITICAL**: Never use raw `tmux` or `python` commands to start the local daemon. You MUST use the `start_scheduler.sh` SOP to guarantee `conda` environment injection and safe singleton takeover.

**To run for Kaggle Cloud**:

```bash
python3 $HOME/openclaw/skills/omni-scheduler/scripts/auto_scheduler.py \
  --mode kaggle \
  --log-path ~/workspace/projects_core/matrix_intent.jsonl \
  --db-path ~/workspace/projects_core/.scheduler_state/pesso_state.sqlite \
  --target kaggle_account_A
```

### 4. CQRS Event Sourcing Schema (The JSONL + SQLite Reducer)

The `matrix_intent.jsonl` file and `pesso_state.sqlite` database form the definitive CQRS contract between the Agent (Producer) and the Daemon (Consumer).

- **The Intent Log (Write-Only)**: Every task action is strictly an append-only event recorded in `projects_core/matrix_intent.jsonl`. No code should ever `open(..., 'r+')` or rewrite this file.
- **The Projection (Read-Only SSoT)**: The Python reducer instantaneously replays the event log into a local, high-concurrency WAL database: `projects_core/.scheduler_state/pesso_state.sqlite`.
- **The State Fold**:
  1. `task.enqueued` events default to `PENDING`.
  2. `task.assigned` events translate to `RUNNING` along with a GPU ID lock.
  3. `task.completed` / `task.failed` emit terminal statuses.
- **Git Protocol**: The `.jsonl` log is optionally tracked. The `.sqlite` projection is ephemeral and strictly git-ignored to prevent continuous merge conflicts.

### 5. Task Generation (The Producer CLI)

To safely inject event intents into the CQRS backend without manual parsing errors, both the Boss and the AI Agent **MUST** use the provided CLI:

```bash
python3 $HOME/openclaw/skills/omni-scheduler/scripts/enqueue_task.py \
  --project "CaLaM" \
  --entry "scripts/run_exp_02.sh" \
  --target "local"
```

_This instantaneously appends a `task.enqueued` intent payload into `matrix_intent.jsonl` and triggers a synchronous flush to the SQLite projection._

## 🛡️ ANTI-HALLUCINATION LAWS (Production Incident Fixes)

> [!IMPORTANT]
> **Law #1 (Daemon Launch Protocol - Updated 2026-03-25)**
>
> The scheduler daemon **MUST** be launched via the formalized SOP script.
> **NEVER** use `nohup ... &` or raw `tmux new-session` strings, as they either break log monitoring or fail to inherit `.bashrc` conda initialization lines leading to instant `command not found` execution failures.
>
> **Correct Launch Command**:
> `bash scripts/start_scheduler.sh`
>
> This gracefully kills old instances and securely injects the `pesso` conda environment before handing off to a detached `tmux` daemon.

> [!IMPORTANT]
> **Law #5 (Graceful Restart & SIGHUP Immunity - Updated 2026-03-25)**
>
> If you need to restart the `auto_scheduler` daemon while experiments are actively utilizing physical GPU hardware, the `start_scheduler.sh` script is completely safe to run.
>
> Because the local dispatch mechanism internally fires `subprocess.Popen` with `start_new_session=True`, all dispatched GPU experiments belong to orphaned detached process groups. They are **100% immune to `SIGHUP`** broadcasted by `tmux kill-session`. A restart of the daemon perfectly achieves a "Smooth Transition" (平稳过渡) without annihilating existing compute.

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

> [!CAUTION]
> **Law #16 (幽灵 Singleton 防锁定 — Production Incident Fix 2026-03-25)**
>
> **事故复盘**：一个 Agent 在 `tmux data_dl`（非标准数据下载会话）内手动启动了 `auto_scheduler.py`，cwd 为 `/root`（不在 Git 仓库内）。该幽灵进程占据 Singleton 锁，导致所有合规新 daemon 被 FATAL 自杀。幽灵进程因 cwd 错误导致 Git sync 永久失败，同时 Zombie Reaper 将 33 个实验全部误杀为 FAILED。5 张 A40 空闲数小时。
>
> **三重防线（必须全部遵守）：**
>
> 1. **tmux 会话命名强制**：scheduler 只能在 `tmux -s scheduler` 会话中启动。禁止在 `data_dl`、`monitor` 或任何其他会话中手动运行 `auto_scheduler.py`。
> 2. **cwd 必须为 Git 仓库根目录**：启动命令必须以 `cd /jhdx0003008/workspace &&` 开头，确保 Git sync 能找到 `.git` 目录。cwd 为 `/root` 或其他路径一律视为违规。
> 3. **启动前必须执行幽灵扫描**：在运行 `tmux new-session -d -s scheduler` 之前，必须先执行 `ps aux | grep auto_scheduler | grep -v grep` 确认没有残留 scheduler 进程。如果有，必须先 `kill` 再启动。
>
> **代码侧增强建议**：`auto_scheduler.py` 的 Singleton 检查应增加"占锁进程健康度审计"——检测到旧 PID 存活时，额外验证其 cwd 是否合法、是否有活跃子进程。若旧进程为空转幽灵，应自动接管而非自杀。

> [!WARNING]
> **Law #17 (W&B 离线死锁免疫 — Production Incident Fix 2026-03-25)**
>
> **事故复盘**：在服务器断网/不稳定的环境下（设置了 `WANDB_MODE=offline`），如果 Python 主进程因为任何报错（如 `NameError`, OOM）意外退出，如果全局没有强制结束 W&B 句柄，W&B 的 C++ 守护线程（`atexit` 钩子）会陷入无限期的网络等待环（`status_report` lock）。导致主进程永远不死，GPU 显存（如 8GB）被永久占用锁死 0% 利用率，集群彻底瘫痪。
>
> **Fix**: 在所有整合了 `wandb` 的训练脚本主入口 `main()`，必须使用至高权重的防爆套包裹主函数逻辑：
>
> ```python
> try:
>     train_task(args)
> finally:
>     if args.wandb:
>         wandb.finish(exit_code=exit_code)
> ```
>
> 强制斩断 W&B 亡语阻塞，确保进程抛异常时也能 100% 把显存吐出来。

> [!IMPORTANT]
> **Law #18 (强制冒烟前置法则 — DevOps Meta-Protocol 2026-03-25)**
>
> **事故复盘**：在修复上述连环死锁的紧急状态时，由于图快，只过了本地静态 Python `py_compile` 语法校验，就直接按 Git SSoT 工作流把代码推上了 GitHub，结果把之前复制粘贴漏改的 `NameError` 隐患直接送上了生产 GPU，引发了更大面积的实验挂载。
>
> **Fix (The Rule)**：任何针对集群守护层 (`auto_scheduler.py`)、基座物理求解器、数据加载器 (`train_*.py`) 的热修复（Hotfix/Refactor），在向主干执行 `git commit + push` 进行 SSoT 分发之前，**必须在受控算力节点上，强制用对应的 `--smoke`（或 `-h` / 1 个 epoch截断）进行至少一次活体前台冒烟测试**。确信没有任何运行期崩溃（Runtime Crashing）、挂载后再合入主线。**“先冒烟试跑，后 Git SSoT”！**
