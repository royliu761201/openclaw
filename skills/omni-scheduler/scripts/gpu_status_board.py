#!/usr/bin/env python3
import subprocess
import re
import sys
import json
import os
from concurrent.futures import ThreadPoolExecutor

# Unified Cluster Nodes
NODES = ["gpu", "arm-32", "arm-33", "arm-34", "90-1", "90-2"]
PROJECT_KEYWORDS = ["PhysPromoFM", "DreamNash", "RicciPruning", "TopoDiffract", "CliffFormer", "TumorOperator", "COGD", "Pesso"]

def run_remote_cmd(node, cmd, timeout=10):
    try:
        # BatchMode=yes avoids password prompts, ConnectTimeout=5 for fail-fast
        full_cmd = ["ssh", "-o", "ConnectTimeout=5", "-o", "BatchMode=yes", node, cmd]
        result = subprocess.run(full_cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except Exception:
        return None

def get_task_name(cmdline, cwd):
    combined = (cmdline or "") + " " + (cwd or "")
    for kw in PROJECT_KEYWORDS:
        if kw.lower() in combined.lower():
            return kw
    match = re.search(r'projects_core/([^/\s]+)', combined)
    if match:
        return match.group(1)
    return "Unknown Task"

def probe_node(node):
    data = {"node": node, "status": "OFFLINE", "arch": "N/A", "type": "N/A", "gpus": []}
    
    probe_out = run_remote_cmd(node, "uname -m && id -u && hostname")
    if not probe_out:
        return data
    
    lines = probe_out.split('\n')
    data["status"] = "ONLINE"
    data["arch"] = lines[0] if len(lines) > 0 else "N/A"
    uid = lines[1] if len(lines) > 1 else "N/A"
    data["type"] = "Container (Root)" if uid == "0" else "Workstation"
    
    gpu_out = run_remote_cmd(node, "nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv,noheader,nounits")
    if not gpu_out:
        return data
        
    for line in gpu_out.split('\n'):
        parts = [p.strip() for p in line.split(',')]
        if len(parts) >= 5:
            data["gpus"].append({
                "index": parts[0],
                "name": parts[1],
                "used": parts[2],
                "total": parts[3],
                "util": parts[4],
                "tasks": []
            })
            
    pid_out = run_remote_cmd(node, "nvidia-smi --query-compute-apps=gpu_index,pid --format=csv,noheader")
    if pid_out:
        pids_by_gpu = {}
        for line in pid_out.split('\n'):
            parts = [p.strip() for p in line.split(',')]
            if len(parts) == 2:
                g_idx, pid = parts
                pids_by_gpu.setdefault(g_idx, []).append(pid)
                
        for g_idx, pids in pids_by_gpu.items():
            for pid in pids:
                cmd_out = run_remote_cmd(node, f"ps -fp {pid} -o cmd= && pwdx {pid} 2>/dev/null || echo 'N/A'")
                if cmd_out:
                    lines = cmd_out.split('\n')
                    cmdline = lines[0] if len(lines) > 0 else ""
                    cwd = lines[1] if len(lines) > 1 else ""
                    task = get_task_name(cmdline, cwd)
                    for g in data["gpus"]:
                        if g["index"] == g_idx:
                            g["tasks"].append(task)
                            
    return data

def render_table(results):
    print("\n" + "═"*100)
    print(f"║ {'OPENCLAW HETEROGENEOUS CLUSTER STATUS':^96} ║")
    print("═"*100)
    print(f"║ {'Node':<10} │ {'Status':<8} │ {'Arch':<8} │ {'Type':<16} │ {'GPU Load (Used/Total)':<28} │ {'Tasks':<15} ║")
    print("╟" + "─"*11 + "┼" + "─"*10 + "┼" + "─"*10 + "┼" + "─"*18 + "┼" + "─"*30 + "┼" + "─"*17 + "╢")
    
    for r in results:
        node = r["node"]
        status = r["status"]
        arch = r["arch"]
        node_type = r["type"]
        
        if status == "OFFLINE":
            print(f"║ {node:<10} │ \033[91m{status:<8}\033[0m │ {arch:<8} │ {node_type:<16} │ {'N/A':<28} │ {'N/A':<15} ║")
            continue
            
        for i, gpu in enumerate(r["gpus"]):
            node_str = node if i == 0 else ""
            status_str = status if i == 0 else ""
            arch_str = arch if i == 0 else ""
            type_str = node_type if i == 0 else ""
            
            load = f"GPU{gpu['index']}: {gpu['used']}/{gpu['total']}MB ({gpu['util']}%)"
            tasks = ", ".join(list(set(gpu["tasks"]))) if gpu["tasks"] else "Idle"
            
            color = "\033[92m" if int(gpu["util"]) < 30 else ("\033[93m" if int(gpu["util"]) < 80 else "\033[91m")
            
            print(f"║ {node_str:<10} │ {status_str:<8} │ {arch_str:<8} │ {type_str:<16} │ {color}{load:<28}\033[0m │ {tasks:<15} ║")
        
        if not r["gpus"]:
            print(f"║ {node:<10} │ {status:<8} │ {arch:<8} │ {node_type:<16} │ {'No GPUs Found':<28} │ {'N/A':<15} ║")
            
    print("═"*100 + "\n")

if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(probe_node, NODES))
    render_table(results)
