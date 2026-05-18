#!/usr/bin/env python3
"""
queue_manager.py - OpenClaw Safe Queue Editor
Provides safe offline CRUD operations for experiment_queue.json and syncs with Git.
This prevents SSH-based manual edits from causing Git conflict deadlocks on the GPU.
"""

import json
import argparse
import os
import subprocess
from datetime import datetime

QUEUE_FILE = os.path.expanduser("~/workspace/projects_core/experiment_queue.json")
QUEUE_DIR = os.path.dirname(QUEUE_FILE)

def load_queue():
    if not os.path.exists(QUEUE_FILE):
        return {"tasks": []}
    with open(QUEUE_FILE, "r") as f:
        return json.load(f)

def save_queue(data):
    with open(QUEUE_FILE, "w") as f:
        json.dump(data, f, indent=4)

def git_sync(msg="Update queue via queue_manager"):
    print("📡 Syncing queue to GitHub...")
    subprocess.run(["git", "add", "experiment_queue.json"], cwd=QUEUE_DIR, check=True)
    try:
        subprocess.run(["git", "commit", "-m", msg], cwd=QUEUE_DIR, check=True)
    except subprocess.CalledProcessError:
        print("✅ No changes to commit.")
        return
    subprocess.run(["git", "push", "origin", "main"], cwd=QUEUE_DIR, check=True)
    print("🚀 Push successful. GPU auto_scheduler will apply this in <60s.")

def main():
    parser = argparse.ArgumentParser(description="Safe Queue Manager")
    parser.add_argument("--list", action="store_true", help="List all tasks")
    parser.add_argument("--delete", type=str, help="Delete task by ID")
    parser.add_argument("--pending", type=str, help="Reset task to PENDING by ID")
    parser.add_argument("--push", action="store_true", help="Commit and Push changes")
    args = parser.parse_args()

    data = load_queue()
    tasks = data.get("tasks", [])

    if args.list:
        print(f"{'ID':<15} {'STATUS':<10} {'ENTRY':<20} COMMAND")
        print("-" * 80)
        for t in tasks:
            print(f"{t.get('id', 'N/A'):<15} {t.get('status', '?-?'):<10} {t.get('entry', '?-?'):<20} {t.get('command', '')[:40]}...")
        return

    modified = False

    if args.delete:
        initial_len = len(tasks)
        data["tasks"] = [t for t in tasks if t.get("id") != args.delete]
        if len(data["tasks"]) < initial_len:
            print(f"🗑️ Deleted task {args.delete}")
            modified = True
        else:
            print(f"⚠️ Task {args.delete} not found.")

    if args.pending:
        for t in data.get("tasks", []):
            if t.get("id") == args.pending:
                t["status"] = "PENDING"
                t.pop("start_time", None)
                t.pop("end_time", None)
                t.pop("assigned_gpu", None)
                print(f"🔄 Reset task {args.pending} to PENDING")
                modified = True
                break
        else:
            print(f"⚠️ Task {args.pending} not found.")

    if modified:
        save_queue(data)
        print("💾 Saved changes locally.")

    if args.push:
        git_sync()

if __name__ == "__main__":
    main()
