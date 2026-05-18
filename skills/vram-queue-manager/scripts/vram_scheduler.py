#!/usr/bin/env python3
"""
VRAM-Aware Job Queue Manager
Author: Antigravity/OpenClaw Core
Purpose: Safely pop and execute bash tasks from a JSON payload only when free VRAM > threshold.
"""

import argparse
import subprocess
import time
import json
import sys
import os

def get_free_vram():
    """Returns a list of integer free MB for all CUDA visible/available GPUs."""
    cmd = ["nvidia-smi", "--query-gpu=memory.free", "--format=csv,nounits,noheader"]
    try:
        out = subprocess.check_output(cmd, encoding='utf-8').strip().split('\n')
        return [int(x) for x in out if x.isdigit()]
    except Exception as e:
        print(f"[Queue Manager] Warning: Could not get nvidia-smi data (Are you on CPU/Mac?): {e}", file=sys.stderr)
        return []

def run_queue(tasks_file, min_vram_gb, poll_interval=10):
    if not os.path.exists(tasks_file):
        print(f"[Queue Manager] FATAL: Task file {tasks_file} not found.")
        sys.exit(1)
        
    with open(tasks_file, 'r') as f:
        tasks = json.load(f)
        
    print(f"\n🚀 [Queue Manager] Loaded {len(tasks)} pending tasks.")
    print(f"🔒 [Queue Manager] Minimum VRAM Threshold per task: {min_vram_gb} GB")
    
    active_processes = []
    pending_tasks = tasks.copy()
    min_vram_mb = min_vram_gb * 1024
    
    while pending_tasks or active_processes:
        # 1. Harvest finished processes
        for p in active_processes.copy():
            ret = p['proc'].poll()
            if ret is not None:
                status = "✅ SUCCESS" if ret == 0 else f"❌ FAILED (Code {ret})"
                print(f"[Queue Manager] Task '{p['name']}' completed. Status: {status}")
                active_processes.remove(p)
                
        # 2. Try to schedule pending
        if pending_tasks:
            vram_status = get_free_vram()
            
            # If no nvidia-smi available, assume safe-fallback (agent error) or simulate
            if not vram_status:
                print("[Queue Manager] No CUDA VRAM stats detected. Falling back to single-queue blocking...")
                # Fallback to pure sequential single-process
                if len(active_processes) == 0:
                    vram_status = [min_vram_mb + 1] # Fake enough memory
                else:
                    vram_status = [0]
            
            # Find max available VRAM across any accessible GPU
            max_vram = max(vram_status) if vram_status else 0
            
            if max_vram >= min_vram_mb:
                task = pending_tasks.pop(0)
                print(f"[Queue Manager] Found {max_vram} MB available. Launching task >> {task.get('name', 'Unknown')}")
                
                # Merge environment mappings strictly
                env = os.environ.copy()
                if 'env' in task:
                    env.update(task['env'])
                    
                cmd = task['cmd']
                print(f"   [CMD] {cmd[:100]}...")
                
                proc = subprocess.Popen(cmd, shell=True, env=env)
                active_processes.append({'name': task.get('name', 'Unknown'), 'proc': proc})
            else:
                # print(f"[Queue Manager] Waiting for resources... Max available: {max_vram} MB")
                pass 
                
        # 3. Rest loop
        time.sleep(poll_interval)
        
    print("\n🏁 [Queue Manager] All tasks in payload have been successfully dispatched and finalized.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VRAM-Aware Python Job Scheduler")
    parser.add_argument("--tasks", required=True, help="Path to JSON file containing array of task dicts: [{'name': '..', 'cmd': '..', 'env': {}}]")
    parser.add_argument("--min-vram-gb", type=float, required=True, help="Minimum free VRAM required to pop a task (GB)")
    parser.add_argument("--poll-interval", type=int, default=15, help="Seconds between nvidia-smi polling")
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("🛡️  ANTIGRAVITY VRAM-AWARE SCHEDULER")
    print("="*60)
    run_queue(args.tasks, args.min_vram_gb, args.poll_interval)
