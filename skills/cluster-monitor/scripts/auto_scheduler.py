#!/usr/bin/env python3
"""
Unified Auto-Scheduler (The Polymorphic Dispatcher)
Deployed as part of the `cluster-monitor` skill.
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
    """Returns VRAM utilization %. Mock 0.0 if not on Linux."""
    try:
        res = subprocess.run(["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader"], 
                             capture_output=True, text=True, timeout=5)
        if res.returncode == 0:
            val_str = res.stdout.strip().replace(' %', '')
            try:
                return float(val_str)
            except ValueError:
                return -1.0
    except Exception:
        pass
    
    logging.warning("nvidia-smi check failed. Returning mock value 0.0 (Idle detected).")
    return 0.0

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
        return data

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
        
    return data

def pull_next_task_locked(f, data, target_name):
    """Pulls the next PENDING task for the specified target, marks it RUNNING, saves, and returns."""
    for index, task in enumerate(data.get("tasks", [])):
        if task.get("status") == "PENDING" and task.get("target", "local") == target_name:
            data["tasks"][index]["status"] = "RUNNING"
            data["tasks"][index]["start_time"] = datetime.now().isoformat()
            
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

def _launch_local(task):
    """Fires the CLI command natively into the background."""
    cmd = task.get("command")
    cwd = task.get("directory", os.path.expanduser("~/workspace/projects_core"))
    job_id = task.get("id")
    logging.info(f"🔫 [LOCAL LAUNCH] Task [{job_id}]: {cmd} in {cwd}")
    
    try:
        subprocess.Popen(cmd, shell=True, cwd=cwd)
        logging.info("Task successfully launched locally. Relinquishing daemon lock.")
    except Exception as e:
        logging.error(f"Failed to launch task: {e}")

def _pack_and_launch_kaggle(task, queue_path):
    """Cloud proxy launcher. Executes push and marks completion immediately."""
    cmd = task.get("command")
    cwd = task.get("directory", "/tmp")
    job_id = task.get("id")
    logging.info(f"☁️ [KAGGLE LAUNCH] Packing Payload for [{job_id}]: {cmd}")
    
    try:
        subprocess.Popen(cmd, shell=True, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info("Payload sent to Kaggle cloud. Relinquishing local lock.")
        # Mark as completed because the cloud takes over execution from here.
        mark_completed(queue_path, job_id, "COMPLETED")
    except Exception as e:
        logging.error(f"Failed to launch payload: {e}")

def daemon_loop(args):
    """Unified polling loop."""
    logging.info(f"Initializing Unified Auto-Scheduler Daemon.")
    logging.info(f"Mode: {args.mode.upper()}")
    if args.mode == "kaggle":
        logging.info(f"Targeting: {args.target}")
        logging.info(f"Max Concurrent: {args.max_concurrent}")
    else:
        logging.info(f"Targeting: local")
        logging.info(f"Trigger Threshold: < {args.threshold}% VRAM")
    logging.info(f"Poll Interval: {args.poll}s")
    
    while True:
        f = get_file_lock(args.queue)
        if f:
            try:
                # 1. Prune junk
                data = prune_queue_locked(f)
                
                # 2. Check Quotas
                can_pull = False
                if args.mode == "local":
                    util = check_nvidia_smi()
                    logging.info(f"[Local] Current GPU Utilization: {util}%")
                    if 0 <= util < args.threshold:
                        can_pull = True
                        logging.info(f"🚨 IDLE STATE DETECTED (< {args.threshold}%). Querying Queue...")
                    else:
                        logging.info("GPU is active. Skipping trigger.")
                        
                elif args.mode == "kaggle":
                    running = check_kaggle_quota()
                    if running < args.max_concurrent:
                        can_pull = True
                    else:
                        logging.info(f"Cloud Quota FULL ({running}/{args.max_concurrent}). Sleeping...")

                # 3. Pull and Execute
                if can_pull:
                    target_name = "local" if args.mode == "local" else args.target
                    task = pull_next_task_locked(f, data, target_name)
                    if task:
                        logging.info(f"Lock acquired. Launching Task: {task['id']}")
                        # We release the lock BEFORE launching so long-running prep commands don't block JSON
                        release_file_lock(f)
                        f = None # prevent double release
                        
                        if args.mode == "local":
                            _launch_local(task)
                        else:
                            _pack_and_launch_kaggle(task, args.queue)
                    else:
                        logging.info(f"No PENDING tasks for [{target_name}]. Sleeping...")
            except Exception as e:
                logging.error(f"Daemon Loop Error: {e}")
            finally:
                if f:
                    release_file_lock(f)
                    
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
    
    # 🚨 ANTI-NODE 01 GUARD BLOCK 🚨
    host = os.uname().nodename
    if 'node01' in host.lower() or 'master' in host.lower():
        logging.critical("FATAL: Constitutional Violation! You are attempting to run a background daemon on Node 01.")
        sys.exit(1)
        
    daemon_loop(args)
