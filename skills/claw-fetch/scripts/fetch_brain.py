#!/usr/bin/env python3
import argparse
import sys
import os
import subprocess
import logging

logging.basicConfig(level=logging.INFO, format="%(message)s")

def get_ssh_tool():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    skills_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
    ssh_tool_path = os.path.join(skills_dir, "ssh", "scripts", "ssh_tool.py")
    ssh_dir = os.path.dirname(ssh_tool_path)
    
    if ssh_dir not in sys.path:
        sys.path.insert(0, ssh_dir)
        
    try:
        import ssh_tool
        return ssh_tool, ssh_tool_path
    except ImportError as e:
        logging.error(f"❌ Failed to load OpenClaw ssh_tool module: {e}")
        sys.exit(1)

def route_request(url: str):
    """
    Intelligent routing logic.
    Returns: (is_local, rewritten_url)
    """
    # HuggingFace routing
    if "huggingface.co" in url:
        return True, url.replace("huggingface.co", "hf-mirror.com")
    
    # Add other domestic mirrors here if matching (e.g. tuna.tsinghua)
    if "tsinghua.edu.cn" in url or "aliyun.com" in url:
         return True, url

    # Default: Assumed blocked/slow, route to external exit node (Node 05)
    return False, url

def main():
    parser = argparse.ArgumentParser(description="Claw-Fetch Brain: Global Download Router")
    parser.add_argument("cmd", choices=["order"])
    parser.add_argument("--url", required=True, help="Target URL to download")
    parser.add_argument("--filename", required=True, help="Target filename")
    parser.add_argument("--category", choices=["model", "dataset", "software"], required=True, help="Category of the asset")
    parser.add_argument("--target-host", help="Optional target to deliver after vaulting")
    
    args = parser.parse_args()
    
    is_local, final_url = route_request(args.url)
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    worker_script = os.path.join(current_dir, "fetch_worker.py")
    
    import uuid
    job_id = str(uuid.uuid4())[:8]
    
    logging.info(f"🧠 [Brain] Job {job_id} Accepted.")
    logging.info(f"🔗 Original URL: {args.url}")
    logging.info(f"🔄 Rewritten URL: {final_url}")
    
    worker_args = f"--url '{final_url}' --filename '{args.filename}' --category '{args.category}'"
    if args.target_host:
        worker_args += f" --target-host '{args.target_host}'"

    if is_local:
        logging.info("📍 Routing Decision: LOCAL (Node 03) Async Download")
        cmd = f"python3 {worker_script} {worker_args} --is-local"
        # Detach and run locally
        subprocess.Popen(cmd, shell=True, start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logging.info(f"🚀 Job Submitted [ID: {job_id}] 正在 Node 03 异步冷库网格处理...")
    else:
        # Route to exit node or designated remote worker
        target_node = os.environ.get("CLAW_EXIT_NODE", "100.98.236.51") # Default Node 05
        target_user = os.environ.get("CLAW_EXIT_USER", "roy-005")
        
        logging.info(f"📍 Routing Decision: REMOTE ({target_node}) Async Download")
        ssh_mod, ssh_tool_path = get_ssh_tool()
        
        # C-Check: Enforce Git-Only SSoT Sync Law. We assume the codebase is already synced on the remote node.
        # This assumes standard OpenClaw structural layout across the grid.
        remote_worker = f"~/workspace/projects/openclaw/skills/claw-fetch/scripts/fetch_worker.py"
        if "51" in target_node: # Specific override for Node 05 Windows layout
            remote_worker = f"C:/Users/{target_user}/workspace/projects/openclaw/skills/claw-fetch/scripts/fetch_worker.py"
        
        logging.info(f"🚀 Job Submitted [ID: {job_id}] 正在委派远端节点异步跨海拾取...")
        trigger_cmd = f"python3 {ssh_tool_path} --host {target_node} --user {target_user} --port 22 exec \"python {remote_worker} --url '{final_url}' --filename '{args.filename}' --category '{args.category}'\" --detach"
        subprocess.Popen(trigger_cmd, shell=True, start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

if __name__ == "__main__":
    main()
