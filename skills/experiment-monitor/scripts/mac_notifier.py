import os
import sys
import json
import time
import subprocess

REMOTE_HOST = "10.190.30.220"
REMOTE_QUEUE = "/jhdx0003008/workspace/projects_core/experiment_queue.json"
POLL_INTERVAL = 30 # seconds

def notify_mac(title, message):
    script = f'display notification "{message}" with title "{title}" sound name "Glass"'
    subprocess.run(["osascript", "-e", script])

def fetch_queue():
    cmd = ["ssh", REMOTE_HOST, f"cat {REMOTE_QUEUE}"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except Exception as e:
        print(f"Failed to fetch queue: {e}")
        return None

def main():
    print("🍎 Mac Notifier Sentinel Started. Monitoring GPU experiments...")
    known_states = {}
    
    # Initial load
    curr_data = fetch_queue()
    if curr_data:
        for t in curr_data.get("tasks", []):
            known_states[t["id"]] = t["status"]
            
    while True:
        time.sleep(POLL_INTERVAL)
        curr_data = fetch_queue()
        if not curr_data:
            continue
            
        for t in curr_data.get("tasks", []):
            tid = t["id"]
            new_status = t["status"]
            entry_name = t.get("entry", "Unknown")
            
            old_status = known_states.get(tid)
            if old_status != new_status:
                if new_status in ["COMPLETED", "FAILED"]:
                    icon = "✅" if new_status == "COMPLETED" else "🚨"
                    notify_mac(
                        title=f"{icon} Experiment {new_status}",
                        message=f"Task: {entry_name}"
                    )
                    print(f"[{time.strftime('%H:%M:%S')}] Notified: {entry_name} -> {new_status}")
                elif new_status == "RUNNING":
                    notify_mac(
                        title="🚀 Experiment Started",
                        message=f"Task: {entry_name} is now RUNNING"
                    )
                    print(f"[{time.strftime('%H:%M:%S')}] Notified: {entry_name} -> {new_status}")
                
                known_states[tid] = new_status

if __name__ == "__main__":
    main()
