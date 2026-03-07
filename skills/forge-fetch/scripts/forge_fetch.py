#!/usr/bin/env python3
"""
GPU-First Global Data Synchronization Script.
Enforces System Law 06 (Data Governance) and Law 07 (Hardware Network Topology).

- Node 01 (Local Mac): ONLY orchestrates. Contains NO raw data.
- GPU Server: The Forge. Executes the download using its local reverse proxy (Port 7890).
- Node 03 (Vault): Permanent NAS backup. Receives data asynchronously from the GPU after download.
"""
import os
import argparse
import subprocess
import sys
import textwrap

# Define Node IPs/Aliases
NODE_03 = "node03" # The Vault
GPU_NODE_DEFAULT = "gpu02"

def run_cmd(cmd, check=True):
    print(f"🚀 Executing locally: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=check)
    except subprocess.CalledProcessError as e:
        print(f"❌ Command Failed: {e}")
        if check:
            sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Asynchronous GPU-First Data Synchronizer")
    parser.add_argument("--project", type=str, required=True, help="Project name (e.g., PESSO, CaLaM)")
    parser.add_argument("--source_url", type=str, required=True, help="URL to download (HF/Kaggle/Direct)")
    parser.add_argument("--filename", type=str, required=True, help="Target filename")
    parser.add_argument("--target_gpu", type=str, default=GPU_NODE_DEFAULT, help="GPU node alias in ssh config")
    
    args = parser.parse_args()
    
    project_path_gpu = f"~/workspace/projects_core/{args.project}/data/raw/"
    project_path_vault = f"~/workspace/projects_core/{args.project}/data/raw/"
    
    # STEP 1: Node 01 Pre-check
    print("🛡️ [Phase 1/3] Node 01 Verification (Zero-Weight Policy)")
    local_data_dir = f"/Users/roy-jd/workspace/projects_core/{args.project}/data/raw"
    os.makedirs(local_data_dir, exist_ok=True)
    with open(os.path.join(local_data_dir, ".gitignore"), "w") as f:
        f.write("*\n!.gitignore\n")
    print("✅ Node 01 protected. .gitignore enforced in local data folder.\n")

    # STEP 2: Asynchronous GPU Download Logic
    print(f"🧱 [Phase 2/3] Dispatching Async Download to {args.target_gpu}")
    
    # We will write a small bash script to the GPU node that handles:
    # 1. Setting the ALL_PROXY
    # 2. Downloading the file
    # 3. Securely pushing it to Node 03 for backup
    
    remote_script_name = f"/tmp/async_fetch_{args.filename}.sh"
    remote_log = f"{project_path_gpu}download_{args.filename}.log"
    
    remote_bash_script = textwrap.dedent(f"""\
        #!/bin/bash
        mkdir -p {project_path_gpu}
        cd {project_path_gpu}
        
        echo "[1/2] GPU Download Starting (Using Local Reverse Proxy 7890)..." > {remote_log}
        export ALL_PROXY=socks5h://127.0.0.1:7890
        
        curl -L "{args.source_url}" -o "{args.filename}" >> {remote_log} 2>&1
        
        if [ $? -eq 0 ]; then
            echo "\\n[2/2] Download Complete. Pushing Backup to Vault (Node 03)..." >> {remote_log}
            # Unset proxy for internal SCP transfer
            unset ALL_PROXY
            ssh {NODE_03} "mkdir -p {project_path_vault}" >> {remote_log} 2>&1
            scp "{args.filename}" {NODE_03}:{project_path_vault}{args.filename} >> {remote_log} 2>&1
            echo "\\n✅ ALL DONE. Data is ready on GPU and backed up to Node 03." >> {remote_log}
        else
            echo "\\n❌ Download Failed. Check proxy or URL." >> {remote_log}
        fi
        
        rm {remote_script_name}
    """)
    
    # 2.1 Send the bash script to the GPU
    cmd_send_script = ["ssh", args.target_gpu, f"cat > {remote_script_name}"]
    print(f"   ↳ Sending async worker script to {args.target_gpu}:{remote_script_name}...")
    try:
        proc = subprocess.Popen(cmd_send_script, stdin=subprocess.PIPE, text=True)
        proc.communicate(remote_bash_script)
        if proc.returncode != 0:
            raise Exception("Failed to push script to GPU")
    except Exception as e:
        print(f"❌ Failed: {e}")
        sys.exit(1)
        
    # 2.2 Make it executable
    run_cmd(["ssh", args.target_gpu, f"chmod +x {remote_script_name}"])
    
    # STEP 3: Execute in Background (nohup)
    print("\n🚀 [Phase 3/3] Firing and Forgetting (Background Task)")
    
    # We use nohup to detach the process so the user doesn't have to wait.
    run_cmd(["ssh", "-f", args.target_gpu, f"nohup {remote_script_name} > /dev/null 2>&1 &"], check=True)
    
    print(f"\n🎉 Dispatch successful! The download is now running asynchronously on {args.target_gpu}.")
    print(f"   ↳ You do not need to wait. Data will automatically backup to {NODE_03} when done.")
    print(f"   ↳ To check status, ssh into {args.target_gpu} and run: tail -f {remote_log}")

if __name__ == "__main__":
    main()
