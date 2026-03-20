#!/usr/bin/env python3
"""
Queue Producer (Task Generator)
Used by the Agent (during PDCA) or the Boss to safely inject new PENDING tasks into the SSoT JSON queue.
"""
import argparse
import json
import os
import uuid
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='➕ [Queue Producer] %(message)s')

def enqueue_task(queue_path, project, command, directory, target, entry, datasets, conda_env):
    # Ensure queue exists
    if not os.path.exists(queue_path):

        data = {"tasks": []}
        logging.info("Queue file not found. Creating a fresh JSON schema.")
    else:
        try:
            with open(queue_path, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            logging.error(f"FATAL: The queue file {queue_path} is corrupted. Could not parse JSON.")
            return False

    task_id = str(uuid.uuid4())[:8]
    
    # Auto-wrap the command in the designated Conda environment for headless GPU servers
    if not conda_env:
        conda_env = project.lower()  # fallback to project name
        
    # Prevent double wrapping if the user already typed conda run
    if not command.startswith('/root/miniconda3/bin/conda run') and not command.startswith('conda run'):
        command = f"/root/miniconda3/bin/conda run -n {conda_env} {command}"
    elif command.startswith('conda run'):
        command = command.replace('conda run', '/root/miniconda3/bin/conda run')
        
    new_task = {
        "id": f"task_{task_id}",
        "project": project,
        "target": target,
        "command": command,
        "entry": entry,
        "directory": directory,
        "status": "PENDING",
        "created_at": datetime.now().isoformat()
    }

    if datasets:
        new_task["kaggle_payload"] = {
            "dataset_mounts": datasets,
            "gpu_type": "P100",
            "internet": True
        }
    
    data.setdefault("tasks", []).append(new_task)
    
    # Save safely
    with open(queue_path, 'w') as f:
        json.dump(data, f, indent=4)

        
    logging.info(f"Successfully enqueued new PENDING task for project [{project}].")
    logging.info(f"  -> Task ID: {new_task['id']}")
    logging.info(f"  -> Target:  {target}")
    logging.info(f"  -> Entry:   {entry}")
    logging.info(f"  -> Command: {command}")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Safely inject a new task into the experiment Queue.")
    parser.add_argument("--queue", default=os.path.expanduser("~/workspace/projects_core/experiment_queue.json"), help="Path to PDCA JSON queue")
    parser.add_argument("--project", required=True, help="Target project name (e.g., CaLaM, Frenet)")
    parser.add_argument("--target", default="local", help="Execution target (e.g., local, kaggle_account_A)")
    parser.add_argument("--entry", required=True, help="Entry script for cloud execution packaging.")
    parser.add_argument("--datasets", nargs='*', help="List of Kaggle dataset mounts (e.g., rajat936/pdebench-coarse)")
    parser.add_argument("--command", required=True, help="The literal bash command to execute (e.g., 'conda run -n calam bash scripts/run.sh')")
    parser.add_argument("--dir", required=True, help="The absolute directory to execute the command inside.")
    parser.add_argument("--env", help="The specific conda environment to execute in (defaults to lowercase project name)")
    
    args = parser.parse_args()
    
    enqueue_task(args.queue, args.project, args.command, args.dir, args.target, args.entry, args.datasets, args.env)
