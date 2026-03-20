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
    """Acquire an atomic file lock to prevent JSON race conditions."""
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f:
            json.dump({"tasks": []}, f)
    
    f = open(file_path, 'r+')
    try:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return f
    except BlockingIOError:
        logging.warning("JSON Queue is currently locked by another process. Skipping this cycle.")
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

def prune_queue_locked(f):
    """7-Day GC for old JSON records, assumes file is already locked and loaded."""
    f.seek(0)
    try:
        data = json.load(f)
    except json.JSONDecodeError:
        return data, False

    now = datetime.now()
    active_tasks = []
    pruned = 0
    
    for t in data.get("tasks", []):
        if t.get("status") in ["COMPLETED", "FAILED"]:
            try:
                created_t = datetime.fromisoformat(t.get("created_at", ""))
                if now - created_t > timedelta(days=7):
                    pruned += 1
                    continue
            except Exception:
                pass
        active_tasks.append(t)
        
    if pruned > 0:
        logging.info(f"🧹 GC Triggered: Pruned {pruned} old tasks from queue.")
        data["tasks"] = active_tasks
        f.seek(0)
        json.dump(data, f, indent=4)
        f.truncate()
        return data, True
        
    return data, False

def sync_queue_to_git(queue_path, max_retries=3):
    """Automatically commit and push the updated queue state back to the central nervous system.
    Uses exponential backoff retry to survive transient DNS/network failures."""
    directory = os.path.dirname(queue_path)
    cmd = f"cd {directory} && git add {os.path.basename(queue_path)} && git commit -m 'chore: Auto-Scheduler state pulse checkpoint' && GIT_SSH_COMMAND=\"ssh -o Port=443 -o HostName=ssh.github.com -o ConnectTimeout=15 -o StrictHostKeyChecking=no\" git push origin main"
    for attempt in range(max_retries):
        try:
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            if res.returncode == 0:
                logging.info("📡 Queue state successfully beamed back to Command Center.")
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
    """Pull the latest task queue and codebase from the central source of truth.
    Retries once on failure to handle transient DNS issues."""
    directory = os.path.dirname(queue_path)
    cmd = f"cd {directory} && GIT_SSH_COMMAND=\"ssh -o Port=443 -o HostName=ssh.github.com -o ConnectTimeout=15 -o StrictHostKeyChecking=no\" git pull origin main"
    for attempt in range(max_retries):
        try:
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            if "Already up to date." not in res.stdout and res.returncode == 0:
                logging.info("📥 Detected and pulled new updates from Command Center.")
            return
        except Exception as e:
            wait = 2 ** attempt * 5
            logging.warning(f"Git pull failed (attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(wait)
    logging.error("❌ Git pull retries exhausted. Continuing with local queue state.")

def pull_next_task_locked(f, data, target_name, gpu_id=None, blocked_groups=None):
    """Pulls the next PENDING task, marks it RUNNING, assigns GPU, saves, and returns.
    blocked_groups: set of group names that have reached their GPU quota."""
    blocked_groups = blocked_groups or set()
    for index, task in enumerate(data.get("tasks", [])):
        if task.get("status") == "PENDING" and task.get("target", "local") == target_name:
            group = task.get("group", "default")
            if group in blocked_groups:
                continue
            data["tasks"][index]["status"] = "RUNNING"
            data["tasks"][index]["start_time"] = datetime.now().isoformat()
            if gpu_id is not None:
                data["tasks"][index]["assigned_gpu"] = gpu_id
            
            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()
            return data["tasks"][index]
    return None

def mark_completed(queue_path, job_id, final_status="COMPLETED"):
    """Locks the file just to mark a task completed."""
    f = get_file_lock(queue_path)
    if not f: return
    try:
        f.seek(0)
        data = json.load(f)
        for t in data.get("tasks", []):
            if t.get("id") == job_id:
                t["status"] = final_status
                t["end_time"] = datetime.now().isoformat()
        f.seek(0)
        json.dump(data, f, indent=4)
        f.truncate()
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
    
    # Environment Isolation
    env = os.environ.copy()
    env["CUDA_VISIBLE_DEVICES"] = str(gpu_id)
    
    # [Law #5] conda run strips CUDA_VISIBLE_DEVICES — inject --gpu into command
    if "--gpu" not in cmd:
        cmd = cmd + f" --gpu {gpu_id}"
    
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
                data, pruned_flag = prune_queue_locked(f)
                if pruned_flag:
                    git_sync_needed = True
                
                if args.mode == "local":
                    gpu_stats = check_nvidia_smi()
                    
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
                            g = t.get("group", "default")
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
                                    g = t.get("group", "default")
                                    group_running[g] = group_running.get(g, 0) + 1
                            blocked_groups = set()
                            for g, limit in gpu_quota.items():
                                if group_running.get(g, 0) >= limit:
                                    blocked_groups.add(g)
                            
                            task = pull_next_task_locked(f, data, "local", gpu_id=gpu_id, blocked_groups=blocked_groups)
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
    parser.add_argument("--threshold", type=float, default=10.0, help="If mode=local, VRAM idle trigger %")
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
    
    # [Layer 3: Singleton Check] Only one scheduler instance allowed (PID file approach)
    PIDFILE = "/tmp/auto_scheduler.pid"
    if os.path.exists(PIDFILE):
        try:
            old_pid = int(open(PIDFILE).read().strip())
            # Check if old PID is still alive
            os.kill(old_pid, 0)  # signal 0 = existence check only
            logging.critical(f"🚨 FATAL: Another scheduler (PID {old_pid}) is still alive! Aborting.")
            sys.exit(1)
        except (ProcessLookupError, ValueError):
            logging.info(f"Stale PID file found (PID gone). Cleaning up.")
        except PermissionError:
            logging.critical(f"🚨 FATAL: Another scheduler process exists but we can't signal it. Aborting.")
            sys.exit(1)
    # Write our PID
    with open(PIDFILE, "w") as pf:
        pf.write(str(os.getpid()))
        
    daemon_loop(args)
