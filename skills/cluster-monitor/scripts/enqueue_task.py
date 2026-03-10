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

def enqueue_task(queue_path, project, command, directory):
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
    
    new_task = {
        "id": f"task_{task_id}",
        "project": project,
        "command": command,
        "directory": directory,
        "status": "PENDING",
        "created_at": datetime.now().isoformat()
    }
    
    data.setdefault("tasks", []).append(new_task)
    
    # Save safely
    with open(queue_path, 'w') as f:
        json.dump(data, f, indent=4)
        
    logging.info(f"Successfully enqueued new PENDING task for project [{project}].")
    logging.info(f"  -> Task ID: {new_task['id']}")
    logging.info(f"  -> Command: {command}")
    logging.info(f"  -> At: {directory}")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Safely inject a new task into the experiment Queue.")
    parser.add_argument("--queue", default=os.path.expanduser("~/workspace/projects_core/experiment_queue.json"), help="Path to PDCA JSON queue")
    parser.add_argument("--project", required=True, help="Target project name (e.g., CaLaM, Frenet)")
    parser.add_argument("--command", required=True, help="The literal bash command to execute (e.g., 'conda run -n calam bash scripts/run.sh')")
    parser.add_argument("--dir", required=True, help="The absolute directory to execute the command inside.")
    
    args = parser.parse_args()
    
    enqueue_task(args.queue, args.project, args.command, args.dir)
