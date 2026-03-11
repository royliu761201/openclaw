#!/usr/bin/env python3
"""
Zero-Idle GPU Daemon (The Long Poller)
Deployed as part of the `cluster-monitor` skill.
Runs EXCLUSIVELY on Node 02 or Local GPU Servers; strictly banned from running as a daemon on Node 01.
"""
import argparse
import subprocess
import json
import time
import os
import sys
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s [Zero-Idle Sentinel] %(message)s')

def check_nvidia_smi():
    """Mock/wrapper for grabbing VRAM utilization % via CLI."""
    try:
        # Actually call it locally or via ssh
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
    
    # If no local smi (like on Mac test environments), return mock safe value
    logging.warning("nvidia-smi check failed. Returning mock value 0.0 (Idle detected).")
    return 0.0

def pull_next_task(queue_path):
    """Pulls the next PENDING task from queue.json and marks it RUNNING."""
    if not os.path.exists(queue_path):
        logging.error(f"Queue not found at {queue_path}")
        return None
        
    with open(queue_path, 'r') as f:
        data = json.load(f)
        
    for index, task in enumerate(data.get("tasks", [])):
        if task.get("status") == "PENDING" and task.get("target", "local") == "local":
            data["tasks"][index]["status"] = "RUNNING"
            data["tasks"][index]["start_time"] = datetime.now().isoformat()
            
            with open(queue_path, 'w') as f:
                json.dump(data, f, indent=4)
                
            return task
            
    return None

def trigger_task(task):
    """Fires the CLI command associated with the task into the background."""
    cmd = task.get("command")
    cwd = task.get("directory", os.path.expanduser("~/workspace/projects_core"))
    
    logging.info(f"🔫 Triggering Task [{task.get('id')}]: {cmd} in {cwd}")
    
    # Normally we would do subprocess.Popen here or via SSH.
    try:
        subprocess.Popen(cmd, shell=True, cwd=cwd)
        logging.info(f"Task successfully launched. Relinquishing lock.")
    except Exception as e:
        logging.error(f"Failed to launch task: {str(e)}")

def prune_queue(queue_path):
    """Garbage collects tasks that are COMPLETED or FAILED and older than 7 days bounds."""
    if not os.path.exists(queue_path):
        return
        
    try:
        with open(queue_path, 'r') as f:
            data = json.load(f)
            
        original_count = len(data.get("tasks", []))
        if original_count == 0:
            return
            
        now = datetime.now()
        new_tasks = []
        
        for task in data.get("tasks", []):
            if task.get("status") in ["COMPLETED", "FAILED"]:
                created_str = task.get("created_at", "")
                try:
                    created_dt = datetime.fromisoformat(created_str)
                    if (now - created_dt).days >= 7:
                        continue # Prune this item
                except Exception:
                    pass
            new_tasks.append(task)
            
        if len(new_tasks) < original_count:
            logging.info(f"🧹 GC Triggered: Pruned {original_count - len(new_tasks)} old tasks from queue.")
            data["tasks"] = new_tasks
            with open(queue_path, 'w') as f:
                json.dump(data, f, indent=4)
                
    except Exception as e:
        logging.error(f"Queue pruning failed: {str(e)}")

def daemon_loop(queue_path, vram_threshold, sleep_interval):
    logging.info(f"Zero-Idle Poll Active. Monitoring threshold: <{vram_threshold}% util. Polling every {sleep_interval}s.")
    
    while True:
        prune_queue(queue_path)
        utilization = check_nvidia_smi()
        
        logging.info(f"Current GPU Utilization: {utilization}%")
        
        if utilization >= 0 and utilization < vram_threshold:
            logging.info(f"🚨 IDLE STATE DETECTED (< {vram_threshold}%). Querying Queue...")
            task = pull_next_task(queue_path)
            
            if task:
                trigger_task(task)
            else:
                logging.info("Queue is empty. Continuing sleep.")
        else:
            logging.info("GPU is active. Skipping trigger.")
            
        time.sleep(sleep_interval)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", default=os.path.expanduser("~/workspace/projects_core/experiment_queue.json"), help="Path to PDCA JSON queue")
    parser.add_argument("--poll", type=int, default=1800, help="Poll interval in seconds (default: 30 mins) to prevent IO strain.")
    parser.add_argument("--threshold", type=float, default=10.0, help="VRAM idle trigger percentage (default: 10).")
    
    args = parser.parse_args()
    
    # 🚨 ANTI-NODE 01 GUARD BLOCK 🚨
    # Hardcoded check to intentionally crash out if someone tries to PM2 start this on the master node
    host = os.uname().nodename
    if 'node01' in host.lower() or 'master' in host.lower():
        logging.critical("FATAL: Constitutional Violation! You are attempting to run a background daemon on Node 01.")
        sys.exit(1)
        
    daemon_loop(args.queue, args.threshold, args.poll)
