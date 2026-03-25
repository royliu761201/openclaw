#!/usr/bin/env python3
"""
Unified Auto-Scheduler (The Polymorphic Dispatcher)
Deployed as part of the `omni-scheduler` skill.
Runs EXCLUSIVELY on Node 02 or Local GPU Servers; strictly banned from running as a daemon on Node 01.

Supports `--mode local` (GPU target puller) and `--mode kaggle` (Kaggle P100 cloud pusher).
"""
import argparse
import subprocess
import json
import time
import os
import sys
import logging
import fcntl
import re
from datetime import datetime, timedelta

ALERT_PATH = "/tmp/scheduler_alert.txt"

logging.basicConfig(level=logging.INFO, format='⚙️ [Unified Scheduler] %(asctime)s %(message)s')

def check_git_liveness(directory: str) -> bool:
    """[Liveness Probe] Ensure the target execution directory is governed by a secure Git repository."""
    try:
        res = subprocess.run(
            ["git", "-C", directory, "rev-parse", "--is-inside-work-tree"],
            capture_output=True, text=True, timeout=10
        )
        return res.returncode == 0 and res.stdout.strip() == "true"
    except Exception as e:
        logging.error(f"Git liveness probe crashed: {e}")
        return False

def get_file_lock(file_path):
    """Acquire an atomic file lock on the intent file, and load the state overlay file to prevent JSON race conditions."""
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f:
            json.dump({"tasks": []}, f)
            
    f = open(file_path, 'r') # READ ONLY FOR INTENT
    try:
        fcntl.flock(f, fcntl.LOCK_SH | fcntl.LOCK_NB) # Shared lock for reading
        return f
    except BlockingIOError:
        logging.warning("JSON Queue intent is exclusively locked. Skipping.")
        f.close()
        return None

def release_file_lock(f):
    """Release the atomic lock and close the file."""
    if f:
        fcntl.flock(f, fcntl.LOCK_UN)
        f.close()

def check_nvidia_smi():
    """Returns a dict of {gpu_id: utilization_float} for all detected GPUs."""
    try:
        res = subprocess.run(
            ["nvidia-smi", "--query-gpu=index,utilization.gpu", "--format=csv,noheader,nounits"], 
            capture_output=True, text=True, timeout=30
        )
        if res.returncode == 0:
            gpu_stats = {}
            for line in res.stdout.strip().split('\n'):
                if not line: continue
                idx, util = line.split(',')
                gpu_stats[int(idx.strip())] = float(util.strip())
            return gpu_stats
    except Exception as e:
        logging.error(f"nvidia-smi check failed: {e}")
    
    return {}

def check_kaggle_quota():
    """Returns the number of currently running Kaggle kernels."""
    logging.info("Checking Kaggle cloud quota...")
    try:
        result = subprocess.run(["kaggle", "kernels", "list", "-m"], capture_output=True, text=True)
        running_count = result.stdout.lower().count("running")
        logging.info(f"Found {running_count} running kernels online.")
        return running_count
    except FileNotFoundError:
        logging.error("Kaggle CLI not installed or not in PATH.")
        return 999 # Block execution

def prune_queue_locked(f, queue_path):
    """7-Day GC for old JSON records, now adapted for CQRS Overlay."""
    f.seek(0)
    try:
        data = json.load(f)
    except json.JSONDecodeError:
        return {"tasks": []}, False
        
    state_path = queue_path.replace("experiment_queue.json", "matrix_state.json")
    state = {}
    if os.path.exists(state_path):
        try:
            with open(state_path, "r") as sf:
                state = json.load(sf)
        except Exception:
            pass
            
    # Apply State Overlay (CQRS In-Memory Merge)
    for t in data.get("tasks", []):
        tid = t.get("id")
        if tid in state:
            t.update(state[tid])

    # No pruning logic here since we no longer write back to the Intent File!
    return data, False

def zombie_reaper(queue_path, data, gpu_stats):
    """[Zombie Reaper] Hunts down and kills orphaned locks or deadlocked 0% GPU processes."""
    now = datetime.now()
    modified = False
    reaped = 0
    
    for t in data.get("tasks", []):
        if t.get("status") == "RUNNING":
            entry = t.get("entry", "")
            assigned_gpu = t.get("assigned_gpu")
            start_time_str = t.get("start_time")
            
            is_alive = True
            if entry:
                try:
                    res = subprocess.run(["pgrep", "-f", "--", f"--task {entry}"], capture_output=True, text=True)
                    is_alive = (res.returncode == 0)
                except Exception:
                    pass
            
            is_hung = False
            is_timeout = False
            if start_time_str and is_alive and assigned_gpu is not None:
                try:
                    start_time = datetime.fromisoformat(start_time_str)
                    age_hours = (now - start_time).total_seconds() / 3600.0
                    
                    # 1. Hung at 0% logic (If > 1 hour and <= 1% util)
                    if age_hours > 1.0 and gpu_stats.get(int(assigned_gpu), 100.0) <= 1.0:
                        is_hung = True
                    
                    # 2. 24h absolute timeout
                    if age_hours > 24.0:
                        is_timeout = True
                except Exception:
                    pass
            
            if not is_alive or is_hung or is_timeout:
                reason = "Orphaned Lock" if not is_alive else ("Hung at 0% GPU" if is_hung else "24h Timeout")
                logging.warning(f"💀 [Zombie Reaper] Reaping task '{entry}' on GPU {assigned_gpu}. Reason: {reason}.")
                t["status"] = "FAILED"
                t["end_time"] = now.isoformat()
                t["reaper_reason"] = reason
                modified = True
                reaped += 1
                
                if is_alive and entry:
                    logging.warning(f"🔫 Executing pkill for zombie task: {entry}")
                    subprocess.run(["pkill", "-9", "-f", f"--task {entry}"])
                    
    return modified, reaped

def sync_queue_to_git(queue_path, max_retries=3):
    """Commit and push ONLY the matrix_state.json file back to the central nervous system.
    CQRS: The Daemon writes state, SSoT writes intent."""
    directory = os.path.dirname(queue_path)
    state_file = "matrix_state.json"
    cmd = f"cd {directory} && git add {state_file} && git diff --cached --quiet && echo 'NO_CHANGE' || (git commit -m 'chore: CQRS Auto-Scheduler STATE pulse checkpoint' -- {state_file} && git push origin main)"
    for attempt in range(max_retries):
        try:
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            if res.returncode == 0:
                if "NO_CHANGE" not in res.stdout:
                    logging.info("📡 Queue STATE state successfully beamed back to Command Center.")
                return
            else:
                raise RuntimeError(res.stderr.strip()[:200])
        except Exception as e:
            wait = 2 ** attempt * 5  # 5s, 10s, 20s
            logging.warning(f"Sync failed (attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(wait)
    logging.error("❌ All sync retries exhausted. Local JSON is authoritative; will retry next cycle.")

def pull_git_updates(queue_path, max_retries=2):
    """Fetch and checkout ONLY the queue JSON file from remote, not the entire repo.
    This prevents code overwrites during daemon runtime. (Law #16 refinement)
    Code updates must be done manually via 'git pull' by an operator."""
    directory = os.path.dirname(queue_path)
    # 计算 queue 文件相对于 Git 仓库根目录的路径
    try:
        repo_root = subprocess.run(
            f"cd {directory} && git rev-parse --show-toplevel",
            shell=True, capture_output=True, text=True, timeout=5
        ).stdout.strip()
        rel_path = os.path.relpath(queue_path, repo_root)
    except Exception:
        rel_path = os.path.basename(queue_path)
    
    cmd = f"cd {directory} && git fetch origin main 2>&1 && git checkout origin/main -- {rel_path} 2>&1"
    for attempt in range(max_retries):
        try:
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            if res.returncode == 0:
                logging.info("📥 Queue file synced from Command Center (single-file pull).")
                return
            else:
                raise RuntimeError(res.stderr.strip()[:200])
        except Exception as e:
            wait = 2 ** attempt * 5
            logging.warning(f"Queue pull failed (attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(wait)
    logging.error("❌ Queue pull retries exhausted. Continuing with local queue state.")

def write_state_overlay(queue_path, data):
    """Write the patched state to matrix_state.json without touching Intent."""
    state_path = queue_path.replace("experiment_queue.json", "matrix_state.json")
    state = {}
    for t in data.get("tasks", []):
        if "status" in t:
            state[t["id"]] = {
                k: v for k, v in t.items() if k in ["status", "assigned_gpu", "start_time", "end_time", "reaper_reason"]
            }
    with open(state_path + ".tmp", "w") as sf:
        json.dump(state, sf, indent=4)
    os.rename(state_path + ".tmp", state_path)

def pull_next_task_locked(f, data, target_name, gpu_id=None, blocked_groups=None, queue_path=None):
    """Pulls the next PENDING task, marks it RUNNING, assigns GPU, saves STATE, and returns."""
    blocked_groups = blocked_groups or set()
    
    # 强制重启接管 (Force Restart Override) Law 10 Support
    for index, task in enumerate(data.get("tasks", [])):
        force_version = task.get("force_restart_version", 0)
        state_version = task.get("executed_version", 0)
        if force_version > state_version and task.get("status") == "FAILED":
            logging.info(f"🔄 CQRS FORCE RESTART: Reviving task '{task.get('entry')}' (v{force_version})")
            data["tasks"][index]["status"] = "PENDING"
            data["tasks"][index]["executed_version"] = force_version
            write_state_overlay(queue_path, data)
            
    for index, task in enumerate(data.get("tasks", [])):
        if task.get("status", "PENDING") == "PENDING" and task.get("target", "local") == target_name:
            group = task.get("group", task.get("project", "default"))
            if group in blocked_groups:
                continue
            data["tasks"][index]["status"] = "RUNNING"
            data["tasks"][index]["start_time"] = datetime.now().isoformat()
            if gpu_id is not None:
                data["tasks"][index]["assigned_gpu"] = gpu_id
            
            write_state_overlay(queue_path, data)
            return data["tasks"][index]
    return None

def mark_completed(queue_path, job_id, final_status="COMPLETED"):
    """Locks the STATE file just to mark a task completed."""
    state_path = queue_path.replace("experiment_queue.json", "matrix_state.json")
    f = get_file_lock(queue_path)
    if not f: return
    try:
        f.seek(0)
        data = json.load(f)
        state = {}
        if os.path.exists(state_path):
            with open(state_path, "r") as sf: state = json.load(sf)
            
        for t in data.get("tasks", []):
            if t.get("id") == job_id:
                tid = t.get("id")
                if tid not in state: state[tid] = {}
                state[tid]["status"] = final_status
                state[tid]["end_time"] = datetime.now().isoformat()
                
        with open(state_path + ".tmp", "w") as sf:
            json.dump(state, sf, indent=4)
        os.rename(state_path + ".tmp", state_path)
    except Exception as e:
        logging.error(f"Failed to mark task {job_id} as {final_status}: {e}")
    finally:
        release_file_lock(f)
    sync_queue_to_git(queue_path)

def _is_task_already_running(task_entry):
    """[Layer 1: Pre-Launch Guard] Check if a task with the same --task name already has a running process."""
    try:
        res = subprocess.run(
            ["pgrep", "-f", f"--task {task_entry}"],
            capture_output=True, text=True, timeout=5
        )
        return res.returncode == 0  # 0 = found matching process
    except Exception:
        return False  # If pgrep fails, allow launch (fail-open for availability)

def _health_check(data):
    """[Layer 4: Health Alert] Detect anomalies and write ALERT file."""
    alerts = []
    
    # Check 1: Any FAILED tasks this cycle?
    failed_tasks = [t for t in data.get("tasks", []) if t.get("status") == "FAILED"]
    if failed_tasks:
        names = [t.get("entry", "?") for t in failed_tasks]
        alerts.append(f"FAILED tasks detected: {names}")
    
    # Check 2: Duplicate processes for same task?
    running_tasks = [t for t in data.get("tasks", []) if t.get("status") == "RUNNING"]
    for t in running_tasks:
        entry = t.get("entry", "")
        try:
            res = subprocess.run(
                ["pgrep", "-c", "-f", f"--task {entry}"],
                capture_output=True, text=True, timeout=5
            )
            count = int(res.stdout.strip()) if res.returncode == 0 else 0
            if count > 2:  # conda wrapper + python = 2 is normal
                alerts.append(f"DUPLICATE: task '{entry}' has {count} processes!")
        except Exception:
            pass
    
    # Check 3: All GPUs idle but no PENDING tasks (stalled queue)
    pending = [t for t in data.get("tasks", []) if t.get("status") == "PENDING"]
    if not pending and not running_tasks and failed_tasks:
        alerts.append("STALLED: No PENDING/RUNNING tasks, only FAILED. Queue needs attention!")
    
    if alerts:
        with open(ALERT_PATH, "w") as af:
            af.write(f"SCHEDULER ALERT — {datetime.now().isoformat()}\n")
            for a in alerts:
                af.write(f"  🚨 {a}\n")
                logging.warning(f"🚨 ALERT: {a}")
    else:
        # Clear old alert if everything is healthy
        if os.path.exists(ALERT_PATH):
            os.remove(ALERT_PATH)

def _launch_local(task, gpu_id, queue_path):
    """Fires the CLI command with CUDA_VISIBLE_DEVICES isolation, and tracks completion."""
    cmd = task.get("command")
    cwd = task.get("directory", os.path.expanduser("~/workspace/projects_core"))
    job_id = task.get("id")
    entry = task.get("entry", "")
    
    # [Layer 1] Pre-Launch Guard: skip if already running
    if _is_task_already_running(entry):
        logging.warning(f"⚠️ [DUPLICATE GUARD] Task '{entry}' already has a running process. Skipping launch.")
        # Revert status back to PENDING so it's not stuck as RUNNING
        mark_completed(queue_path, job_id, "PENDING")
        return
        
    # [Constitutional Guard] Fail-Fast on Tracking Identifier
    if "--task" not in cmd:
        logging.critical(f"🚨 FATAL: Payload violates tracking constraints! The command string lacks the mandatory '--task' argument.")
        logging.critical(f"Without '--task', the Zombie Reaper and Duplicate Guard cannot track this process lifecycle.")
        logging.critical(f"Offending payload: {cmd}")
        mark_completed(queue_path, job_id, "FAILED_INVALID_CLI")
        return
    
    # Environment Isolation
    env = os.environ.copy()
    env["CUDA_VISIBLE_DEVICES"] = str(gpu_id)
    
    # [Proxy Quarantine] Scrub all lethal proxy inheritance that crashes W&B / Sentry hooks
    for key in ["http_proxy", "https_proxy", "all_proxy", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"]:
        if key in env:
            del env[key]
    
    # [Law #5 - Deprecated] conda run bypass is now inherently utilized securely via env injection instead of CLI arguments,
    # preventing strict argparse implementations (like PESSO) from instantly crashing on `--gpu` unknown flags.
    
    # [Constitutional Guard] Git Liveness SSoT Probe
    if not check_git_liveness(cwd):
        logging.critical(f"🚨 FATAL: Constitutional Violation! Target directory '{cwd}' is NOT a Git repository.")
        logging.critical("Refusing to launch task in an unversioned (Dead) workspace.")
        mark_completed(queue_path, job_id, "FAILED_NON_GIT_WORKSPACE")
        return
    
    logging.info(f"🔫 [LOCAL LAUNCH] GPU {gpu_id} | Task [{entry}]: {cmd}")
    
    try:
        import shlex
        import threading
        
        def run_task():
            try:
                # [FIX] conda run detach: replace with direct env python path
                import re
                _cmd = cmd
                # Match both full-path and bare 'conda run'
                m = re.match(r'(?:(.*)/bin/)?conda run -n (\S+)\s+(.*)', _cmd)
                if m:
                    conda_base = m.group(1) if m.group(1) else '/root/miniconda3'
                    env_name, rest = m.group(2), m.group(3)
                    env_py = f'{conda_base}/envs/{env_name}/bin/python3'
                    # Replace 'python' or 'python3' in the rest with env python
                    _cmd = re.sub(r'\bpython3?\b', env_py, rest, count=1)
                    logging.info(f"🔧 conda run → direct: {_cmd[:120]}")
                # [FIX] Parse inline KEY=VALUE env var prefixes (e.g. PYTHONPATH=...)
                # shlex.split treats them as the executable, so extract and inject into env
                tokens = shlex.split(_cmd)
                extra_env = {}
                while tokens and '=' in tokens[0] and not tokens[0].startswith('-'):
                    k, v = tokens.pop(0).split('=', 1)
                    extra_env[k] = v
                if extra_env:
                    env.update(extra_env)
                    logging.info(f"🔧 Injected env vars: {list(extra_env.keys())}")
                
                # [NETWORK ARMOR] Force WandB to cache local logs, preventing GFW TCP connection resets
                env["WANDB_MODE"] = "offline"
                
                proc = subprocess.Popen(tokens, cwd=cwd, env=env)
                proc.wait()
                final_status = "COMPLETED" if proc.returncode == 0 else "FAILED"
            except Exception as e:
                logging.error(f"Task {job_id} crashed: {e}")
                final_status = "FAILED"
            
            logging.info(f"🏁 Task [{entry}] on GPU {gpu_id} finished with status: {final_status}")
            mark_completed(queue_path, job_id, final_status)
            
        t = threading.Thread(target=run_task)
        # [SECURITY FIX] Abolish daemon threads so child monitor threads safely survive main thread termination.
        t.daemon = False
        t.start()
        
        logging.info(f"Task successfully launched and monitored on GPU {gpu_id}.")
    except Exception as e:
        logging.error(f"Failed to launch task on GPU {gpu_id}: {e}")
        mark_completed(queue_path, job_id, "FAILED")

def _pack_and_launch_kaggle(task, queue_path):
    """Cloud proxy launcher. Executes push and marks completion immediately."""
    cmd = task.get("command")
    cwd = task.get("directory", "/tmp")
    job_id = task.get("id")
    logging.info(f"☁️ [KAGGLE LAUNCH] Packing Payload for [{job_id}]: {cmd}")
    
    try:
        import shlex
        subprocess.Popen(shlex.split(cmd), cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info("Payload sent to Kaggle cloud. Relinquishing local lock.")
        # Mark as completed because the cloud takes over execution from here.
        mark_completed(queue_path, job_id, "COMPLETED")
    except Exception as e:
        logging.error(f"Failed to launch payload: {e}")

def daemon_loop(args):
    """Unified multi-slot polling loop."""
    logging.info(f"Initializing Unified Multi-GPU Auto-Scheduler v2.0.")
    logging.info(f"Mode: {args.mode.upper()} | Poll: {args.poll}s | Threshold: < {args.threshold}%")
    
    first_boot = True
    
    while True:
        # [Layer 4] Read alert file at start of each cycle
        if os.path.exists(ALERT_PATH):
            with open(ALERT_PATH) as af:
                logging.warning(f"📋 Active alert:\n{af.read()}")
        
        pull_git_updates(args.queue)
        git_sync_needed = False
        f = get_file_lock(args.queue)
        if f:
            try:
                data, pruned_flag = prune_queue_locked(f, args.queue)
                if pruned_flag or first_boot:
                    write_state_overlay(args.queue, data)
                    git_sync_needed = True
                    first_boot = False
                
                if args.mode == "local":
                    gpu_stats = check_nvidia_smi()
                    
                    # --- ZOMBIE REAPER TICK ---
                    needs_sync, reaped_count = zombie_reaper(args.queue, data, gpu_stats)
                    if needs_sync:
                        write_state_overlay(args.queue, data)
                        git_sync_needed = True
                    
                    # [Solidify Scheduling] Calculate currently assigned GPUs from JSON queue to enforce EXCLUSIVE LOCK
                    assigned_gpus = set()
                    for t in data.get("tasks", []):
                        if t.get("status") == "RUNNING" and "assigned_gpu" in t:
                            assigned_gpus.add(int(t["assigned_gpu"]))
                            
                    # A GPU is truly available only if its utilization is low AND it's not locked by a RUNNING task
                    available_gpus = [idx for idx, util in gpu_stats.items() 
                                      if util < args.threshold and idx not in assigned_gpus]
                    
                    # [Law #9] Respect --max-gpus: limit total concurrent tasks
                    total_running = len(assigned_gpus)
                    slots_left = args.max_gpus - total_running
                    if slots_left <= 0:
                        available_gpus = []
                    else:
                        available_gpus = available_gpus[:slots_left]
                    
                    # [GPU Quota Groups] Compute per-group running counts
                    gpu_quota = data.get("gpu_quota", {})
                    group_running = {}
                    for t in data.get("tasks", []):
                        if t.get("status") == "RUNNING":
                            g = t.get("group", t.get("project", "default"))
                            group_running[g] = group_running.get(g, 0) + 1
                    blocked_groups = set()
                    for g, limit in gpu_quota.items():
                        if group_running.get(g, 0) >= limit:
                            blocked_groups.add(g)
                    if blocked_groups:
                        logging.info(f"GPU quota reached for groups: {blocked_groups}")
                    
                    if available_gpus:
                        if assigned_gpus:
                            logging.info(f"Detected {len(available_gpus)} idle GPUs: {available_gpus} | Active Exclusive Locks: {list(assigned_gpus)}")
                        else:
                            logging.info(f"Detected {len(available_gpus)} idle GPUs: {available_gpus}")
                            
                        for gpu_id in available_gpus:
                            # Recompute blocked_groups after each dispatch (a new task changes counts)
                            group_running = {}
                            for t in data.get("tasks", []):
                                if t.get("status") == "RUNNING":
                                    g = t.get("group", t.get("project", "default"))
                                    group_running[g] = group_running.get(g, 0) + 1
                            blocked_groups = set()
                            for g, limit in gpu_quota.items():
                                if group_running.get(g, 0) >= limit:
                                    blocked_groups.add(g)
                            
                            task = pull_next_task_locked(f, data, "local", gpu_id=gpu_id, blocked_groups=blocked_groups, queue_path=args.queue)
                            if task:
                                git_sync_needed = True
                                _launch_local(task, gpu_id, args.queue)
                            else:
                                break # No more PENDING tasks
                    else:
                        if assigned_gpus:
                            logging.info(f"All GPUs busy or locked. Active Exclusive Locks: {list(assigned_gpus)}")
                        else:
                            logging.info("All GPUs are busy or nvidia-smi failed.")
                            
                    # --- [LAW #11] END-TO-END SATURATION ASSERTION (Poka-Yoke) ---
                    # To prevent the "Sandbox Saturation Blindness" incident, mechanically guarantee throughput
                    pending_unblocked = [
                        t.get("entry", t.get("id")) for t in data.get("tasks", []) 
                        if t.get("status") == "PENDING" 
                        and t.get("target", "local") == "local"
                        and t.get("group", t.get("project", "default")) not in blocked_groups
                    ]
                    if pending_unblocked and available_gpus:
                        # At this point, if there are STILL unblocked PENDING tasks AND idle GPUs,
                        # it means the dispatch loop has fundamentally failed (e.g. a silent exception).
                        alert_msg = f"LAW #11 VIOLATION (Saturation Trap)! {len(available_gpus)} GPUs idle {available_gpus}, but {len(pending_unblocked)} unblocked PENDING tasks ignored: {pending_unblocked[:3]}..."
                        logging.critical(f"🚨 {alert_msg}")
                        with open(ALERT_PATH, "a") as af:
                            af.write(f"  🚨 {alert_msg}\n")
                        
                elif args.mode == "kaggle":
                    running = check_kaggle_quota()
                    if running < args.max_concurrent:
                        target_name = args.target
                        task = pull_next_task_locked(f, data, target_name)
                        if task:
                            git_sync_needed = True
                            _pack_and_launch_kaggle(task, args.queue)
                    else:
                        logging.info(f"Cloud Quota FULL ({running}/{args.max_concurrent}).")

                # [Layer 4] Health check every cycle
                _health_check(data)
                
            except Exception as e:
                logging.error(f"Daemon Loop Error: {e}")
            finally:
                if f:
                    release_file_lock(f)
        
        if git_sync_needed:
            sync_queue_to_git(args.queue)
            
        time.sleep(args.poll)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["local", "kaggle"], required=True, help="Execution strategy wrapper")
    parser.add_argument("--queue", default=os.path.expanduser("~/workspace/projects_core/experiment_queue.json"), help="Path to PDCA JSON queue")
    parser.add_argument("--poll", type=int, default=1800, help="Poll interval in seconds")
    parser.add_argument("--target", default="kaggle_account_A", help="If mode=kaggle, which account target to look for")
    parser.add_argument("--threshold", type=float, default=10.0, help="If mode=local, VRAM idle trigger %%")
    parser.add_argument("--max-concurrent", type=int, default=2, help="If mode=kaggle, max active kernels limit")
    parser.add_argument("--max-gpus", type=int, default=5, help="Max GPUs to use simultaneously (reserve rest for other projects)")
    
    args = parser.parse_args()
    
    # [SECURITY FIX] Install OS-level armor against SIGHUP (e.g., SSH interactive disconnects)
    import signal
    try:
        signal.signal(signal.SIGHUP, signal.SIG_IGN)
    except AttributeError:
        pass
        
    # 🚨 ANTI-NODE 01 GUARD BLOCK 🚨
    host = os.uname().nodename
    if 'node01' in host.lower() or 'master' in host.lower():
        logging.critical("FATAL: Constitutional Violation! You are attempting to run a background daemon on Node 01.")
        sys.exit(1)
    
    # [Layer 3: Singleton Check with Health Audit] (Law #16 — 2026-03-25)
    # Instead of blindly aborting when another PID exists, perform a 3-layer
    # health audit to detect ghost/zombie schedulers and auto-takeover.
    PIDFILE = "/tmp/auto_scheduler.pid"
    if os.path.exists(PIDFILE):
        try:
            old_pid = int(open(PIDFILE).read().strip())
            os.kill(old_pid, 0)  # signal 0 = existence check only
            
            # === 三重健康度审计 (Law #16) ===
            is_ghost = False
            ghost_reasons = []
            
            # 审计 1: cwd 合法性 — 必须在 Git 仓库内
            try:
                old_cwd = os.readlink(f"/proc/{old_pid}/cwd")
                # 检查 cwd 或其祖先是否包含 .git
                cwd_has_git = False
                check_path = old_cwd
                for _ in range(10):  # 最多向上查 10 级
                    if os.path.isdir(os.path.join(check_path, ".git")):
                        cwd_has_git = True
                        break
                    parent = os.path.dirname(check_path)
                    if parent == check_path:
                        break
                    check_path = parent
                if not cwd_has_git:
                    is_ghost = True
                    ghost_reasons.append(f"cwd={old_cwd} 不在任何 Git 仓库内")
            except (FileNotFoundError, PermissionError):
                ghost_reasons.append("无法读取 /proc cwd（可能在容器内）")
            
            # 审计 2: 子进程活跃度 — 健康 scheduler 应有实验子进程
            try:
                children = subprocess.run(
                    ["pgrep", "-P", str(old_pid)],
                    capture_output=True, text=True, timeout=5
                )
                has_children = (children.returncode == 0 and children.stdout.strip())
                if not has_children:
                    ghost_reasons.append("无活跃子进程（空转调度器）")
            except Exception:
                pass  # pgrep 失败不作为判定依据
            
            # 审计 3: 空转时长 — 无子进程且运行超 1 小时 = 幽灵
            try:
                proc_stat = os.stat(f"/proc/{old_pid}")
                import time as _time
                age_hours = (_time.time() - proc_stat.st_mtime) / 3600.0
                if age_hours > 1.0 and not has_children:
                    is_ghost = True
                    ghost_reasons.append(f"空转 {age_hours:.1f} 小时且无子进程")
            except Exception:
                pass
            
            if is_ghost:
                logging.warning(f"🔫 检测到幽灵 scheduler (PID {old_pid})，原因: {'; '.join(ghost_reasons)}")
                logging.warning(f"🔫 自动接管：正在终止幽灵进程 PID {old_pid}...")
                try:
                    os.kill(old_pid, 9)  # SIGKILL 强制终止
                    import time as _time
                    _time.sleep(2)
                    logging.info(f"✅ 幽灵进程 PID {old_pid} 已被清除，新 scheduler 接管控制权。")
                except Exception as kill_err:
                    logging.critical(f"🚨 无法终止幽灵进程 PID {old_pid}: {kill_err}。请手动 kill。")
                    sys.exit(1)
            else:
                # 旧进程通过了所有健康审计 → 真正的健康 scheduler，正常 abort
                logging.critical(f"🚨 FATAL: 健康的 scheduler (PID {old_pid}) 正在运行。新实例 abort。")
                sys.exit(1)
                
        except (ProcessLookupError, ValueError):
            logging.info(f"发现过期 PID 文件（进程已死）。清理中。")
        except PermissionError:
            logging.critical(f"🚨 FATAL: 存在另一个 scheduler 进程但无权限信号它。Aborting。")
            sys.exit(1)
    # Write our PID
    with open(PIDFILE, "w") as pf:
        pf.write(str(os.getpid()))
        
    daemon_loop(args)
