#!/usr/bin/env python3
"""
Cluster-Aware Job Queue Manager (Advanced Scheduler: Topography & Topology)
Author: Antigravity/OpenClaw Core

Supports:
- 单卡多任务 (Single Shared)
- 单卡独享 (Single Exclusive)
- 多卡共享 (Multi-GPU Shared)
- 多卡独享 (Multi-GPU Exclusive)
"""

import argparse
import subprocess
import time
import json
import sys
import os

def get_remote_resources(target_node):
    """
    Returns (gpu_stats, free_ram_mb) for the target_node via SSH.
    - gpu_stats: dict mapping gpu_index -> {'free': MB, 'total': MB}
    - free_ram_mb: available system RAM in MB
    """
    payload = "nvidia-smi --query-gpu=index,memory.free,memory.total --format=csv,nounits,noheader; echo '==='; grep MemAvailable /proc/meminfo | awk '{print $2}'"
    cmd = ["ssh", "-q", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5", target_node, payload]
    
    try:
        out = subprocess.check_output(cmd, encoding='utf-8', stderr=subprocess.DEVNULL).strip().split('\n')
        gpu_stats = {}
        ram_mb = 0
        parsing_ram = False
        
        for line in out:
            line = line.strip()
            if not line: continue
            if line == '===':
                parsing_ram = True
                continue
            
            if parsing_ram:
                if line.isdigit(): ram_mb = int(line) // 1024
            else:
                parts = [p.strip() for p in line.split(',')]
                if len(parts) == 3 and parts[0].isdigit():
                    gpu_stats[parts[0]] = {
                        'free': int(parts[1]),
                        'total': int(parts[2])
                    }
        return gpu_stats, ram_mb
    except Exception as e:
        return {}, 0

def run_cluster_queue(tasks_file, default_min_vram_gb, poll_interval=15):
    if not os.path.exists(tasks_file):
        print(f"[Cluster Dispatcher] FATAL: Task file {tasks_file} not found.")
        sys.exit(1)
        
    with open(tasks_file, 'r') as f:
        tasks = json.load(f)
        
    print(f"\n🌍 [Cluster Dispatcher] Loaded {len(tasks)} pending topology-aware tasks.")
    
    active_processes = []
    pending_tasks = tasks.copy()
    
    # Track which node was just dispatched to prevent PyTorch boot race conditions (VRAM allocation lag)
    last_dispatch_time = {} 
    
    while pending_tasks or active_processes:
        # 1. Harvest finished processes
        for p in active_processes.copy():
            ret = p['proc'].poll()
            if ret is not None:
                status = "✅ SUCCESS" if ret == 0 else f"❌ FAILED (Code {ret})"
                print(f"[Cluster Dispatcher] Task '{p['name']}' ({status}) released. GPUs: {p['gpus_used']}")
                active_processes.remove(p)
                
        # 2. Try to schedule pending
        if pending_tasks:
            task = pending_tasks[0]
            target_node = task.get('target_node', 'localhost')
            
            # Anti-Race Condition: If we deployed to this node within 20s, PyTorch is still allocating VRAM. Skip.
            if time.time() - last_dispatch_time.get(target_node, 0) < 20:
                pass # Waiting for PyTorch to manifest its VRAM usage
            else:
                # Task parameters
                num_gpus_req = int(task.get('num_gpus', 1))
                exclusive_req = bool(task.get('exclusive', False))
                min_vram_mb = float(task.get('min_vram_gb', default_min_vram_gb)) * 1024
                req_ram_mb = float(task.get('min_ram_gb', 8)) * 1024
                
                gpu_stats, available_ram_mb = get_remote_resources(target_node)
                
                if available_ram_mb >= req_ram_mb and gpu_stats:
                    # Search for GPUs matching criteria
                    qualified_gpus = []
                    for idx, stats in gpu_stats.items():
                        free_mb = stats['free']
                        total_mb = stats['total']
                        
                        if exclusive_req:
                            # Exclusive means GPU is basically empty (>95% free)
                            if free_mb >= total_mb * 0.95 and free_mb >= min_vram_mb:
                                qualified_gpus.append(idx)
                        else:
                            # Shared means it just needs to hit min_vram_mb
                            if free_mb >= min_vram_mb:
                                qualified_gpus.append(idx)
                    
                    if len(qualified_gpus) >= num_gpus_req:
                        # Found matching hardware map! Pop and launch!
                        task = pending_tasks.pop(0)
                        chosen_gpus = qualified_gpus[:num_gpus_req] # Take the first N
                        gpu_str = ",".join(chosen_gpus)
                        
                        print(f"🚀 [Launch] {target_node} | RAM: {available_ram_mb}MB | GPUs: {gpu_str} (Exclusive: {exclusive_req}) >> {task.get('name', 'Task')}")
                        
                        workdir = task.get('workdir', '~')
                        env_setup = task.get('env_setup', 'true')
                        cmd_raw = task.get('cmd', 'echo "No CMD"')
                        
                        # Dynamically inject CUDA_VISIBLE_DEVICES into the bash chain
                        inject_env = f"export CUDA_VISIBLE_DEVICES={gpu_str}"
                        remote_payload = f"cd {workdir} && {env_setup} && {inject_env} && {cmd_raw}"
                        
                        ssh_cmd = [
                            "ssh", "-q", "-o", "BatchMode=yes", target_node,
                            f"bash -lc '{remote_payload}'"
                        ]
                        
                        proc = subprocess.Popen(ssh_cmd)
                        active_processes.append({
                            'name': task.get('name', 'Unknown'), 
                            'node': target_node, 
                            'proc': proc,
                            'gpus_used': gpu_str
                        })
                        last_dispatch_time[target_node] = time.time()
                
        # 3. Rest loop
        time.sleep(poll_interval)
        
    print("\n🏁 [Cluster Dispatcher] All topology-aware tasks have been successfully dispatched.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Multi-Node Advanced VRAM/RAM-Aware Job Scheduler")
    parser.add_argument("--tasks", required=True, help="Path to JSON file.")
    parser.add_argument("--min-vram-gb", type=float, default=10, help="Fallback minimum VRAM required per GPU if not set in JSON")
    parser.add_argument("--poll-interval", type=int, default=10, help="Seconds between polling")
    
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("🌍 ANTIGRAVITY ADVANCED TOPOLOGY DISPATCHER (X86/ARM/4090)")
    print("="*70)
    run_cluster_queue(args.tasks, args.min_vram_gb, args.poll_interval)
