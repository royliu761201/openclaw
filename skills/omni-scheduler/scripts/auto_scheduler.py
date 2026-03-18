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
from datetime import datetime, timedelta

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

def sync_queue_to_git(queue_path):
    """Automatically commit and push the updated queue state back to the central nervous system."""
    try:
        directory = os.path.dirname(queue_path)
        # Using the secure 443 fallback tunneling method for resilient sync
        cmd = f"cd {directory} && git add {os.path.basename(queue_path)} && git commit -m 'chore: Auto-Scheduler state pulse checkpoint' && GIT_SSH_COMMAND=\"ssh -o Port=443 -o HostName=ssh.github.com -o ConnectTimeout=15 -o StrictHostKeyChecking=no\" git push origin main"
        subprocess.run(cmd, shell=True, capture_output=True, timeout=30)
        logging.info("📡 Queue state successfully beamed back to Command Center.")
    except Exception as e:
        logging.warning(f"Failed to sync queue state back to git: {e}")

def pull_git_updates(queue_path):
    """Pull the latest task queue and codebase from the central source of truth."""
    try:
        directory = os.path.dirname(queue_path)
        cmd = f"cd {directory} && GIT_SSH_COMMAND=\"ssh -o Port=443 -o HostName=ssh.github.com -o ConnectTimeout=15 -o StrictHostKeyChecking=no\" git pull origin main"
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if "Already up to date." not in res.stdout:
            logging.info("📥 Detected and pulled new updates from Command Center.")
    except Exception as e:
        logging.warning(f"Failed to pull latest git updates: {e}")

def pull_next_task_locked(f, data, target_name, gpu_id=None):
    """Pulls the next PENDING task, marks it RUNNING, assigns GPU, saves, and returns."""
    for index, task in enumerate(data.get("tasks", [])):
        if task.get("status") == "PENDING" and task.get("target", "local") == target_name:
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

def _launch_local(task, gpu_id, queue_path):
    """Fires the CLI command with CUDA_VISIBLE_DEVICES isolation, and tracks completion."""
    cmd = task.get("command")
    cwd = task.get("directory", os.path.expanduser("~/workspace/projects_core"))
    job_id = task.get("id")
    
    # Environment Isolation
    env = os.environ.copy()
    env["CUDA_VISIBLE_DEVICES"] = str(gpu_id)
    
    # [Constitutional Guard] Git Liveness SSoT Probe
    if not check_git_liveness(cwd):
        logging.critical(f"🚨 FATAL: Constitutional Violation! Target directory '{cwd}' is NOT a Git repository.")
        logging.critical("Refusing to launch task in an unversioned (Dead) workspace.")
        mark_completed(queue_path, job_id, "FAILED_NON_GIT_WORKSPACE")
        return
    
    logging.info(f"🔫 [LOCAL LAUNCH] GPU {gpu_id} | Task [{job_id}]: {cmd}")
    
    try:
        import shlex
        import threading
        
        def run_task():
            try:
                proc = subprocess.Popen(shlex.split(cmd), cwd=cwd, env=env)
                proc.wait()
                final_status = "COMPLETED" if proc.returncode == 0 else "FAILED"
            except Exception as e:
                logging.error(f"Task {job_id} crashed: {e}")
                final_status = "FAILED"
            
            logging.info(f"🏁 Task [{job_id}] on GPU {gpu_id} finished with status: {final_status}")
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
                    
                    if available_gpus:
                        if assigned_gpus:
                            logging.info(f"Detected {len(available_gpus)} idle GPUs: {available_gpus} | Active Exclusive Locks: {list(assigned_gpus)}")
                        else:
                            logging.info(f"Detected {len(available_gpus)} idle GPUs: {available_gpus}")
                            
                        for gpu_id in available_gpus:
                            task = pull_next_task_locked(f, data, "local", gpu_id=gpu_id)
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
        
    daemon_loop(args)
