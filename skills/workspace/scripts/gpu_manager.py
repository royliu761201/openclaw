import os
import sys
import argparse
import re
from datetime import datetime

REGISTRY_PATH = os.path.expanduser("~/workspace/docs/system_core/08_GLOBAL_GPU_REGISTRY.md")

def read_registry():
    with open(REGISTRY_PATH, 'r') as f:
        return f.readlines()

def write_registry(lines):
    with open(REGISTRY_PATH, 'w') as f:
        f.writelines(lines)

def allocate_gpu(node, project, task, agent):
    lines = read_registry()
    allocated_gpu = None
    
    for i, line in enumerate(lines):
        if line.strip().startswith('|'):
            parts = [p.strip() for p in line.split('|')[1:-1]]
            if len(parts) >= 8 and parts[0] == f"`{node}`" and "🟢 FREE" in parts[3]:
                # Found a free GPU on the requested node
                allocated_gpu = parts[1]
                
                # Update row
                new_status = "🔴 RUNNING"
                parts[3] = new_status
                parts[4] = project
                parts[5] = task
                parts[6] = agent
                parts[7] = "TBD"
                
                new_line = "| " + " | ".join(parts) + " |\n"
                lines[i] = new_line
                break

    if allocated_gpu:
        write_registry(lines)
        print(f"SUCCESS: Allocated {allocated_gpu} on node {node}. Registration locked.")
        sys.exit(0)
    else:
        print(f"ERROR: No 🟢 FREE GPUs available on node {node}.")
        sys.exit(1)

def free_gpu(node, gpu_id):
    lines = read_registry()
    freed = False
    
    for i, line in enumerate(lines):
        if line.strip().startswith('|'):
            parts = [p.strip() for p in line.split('|')[1:-1]]
            if len(parts) >= 8 and parts[0] == f"`{node}`" and parts[1] == gpu_id:
                if "🟢 FREE" in parts[3]:
                    print(f"WARNING: GPU {gpu_id} on {node} is already FREE.")
                    freed = True
                    break
                
                # Update row
                parts[3] = "🟢 FREE"
                parts[4] = "-"
                parts[5] = "-"
                parts[6] = "-"
                parts[7] = "-"
                
                new_line = "| " + " | ".join(parts) + " |\n"
                lines[i] = new_line
                freed = True
                break

    if freed:
        write_registry(lines)
        print(f"SUCCESS: Freed {gpu_id} on node {node}. Registration unlocked.")
        sys.exit(0)
    else:
        print(f"ERROR: Could not find lock for GPU {gpu_id} on node {node}.")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Global GPU SSoT Registry Manager")
    subparsers = parser.add_subparsers(dest="action", required=True)
    
    alloc_parser = subparsers.add_parser("allocate", help="Allocate a free GPU on a node")
    alloc_parser.add_argument("--node", required=True, help="Node identifier (e.g. 90-1, gpu)")
    alloc_parser.add_argument("--project", required=True, help="Project name (e.g. CaLaM)")
    alloc_parser.add_argument("--task", required=True, help="Brief task description")
    alloc_parser.add_argument("--agent", required=True, help="Your Agent ID/Name")
    
    free_parser = subparsers.add_parser("free", help="Free an allocated GPU on a node")
    free_parser.add_argument("--node", required=True, help="Node identifier (e.g. 90-1, gpu)")
    free_parser.add_argument("--gpu_id", required=True, help="GPU ID (e.g. GPU-0)")
    
    args = parser.parse_args()
    
    if args.action == "allocate":
        allocate_gpu(args.node, args.project, args.task, args.agent)
    elif args.action == "free":
        free_gpu(args.node, args.gpu_id)

if __name__ == "__main__":
    main()
