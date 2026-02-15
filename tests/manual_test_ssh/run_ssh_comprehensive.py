
import os
import sys
import json
import time
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Load env credentials
load_dotenv()

SSH_HOST = os.getenv("SSH_HOST")
SSH_USER = os.getenv("SSH_USER")
WANDB_API_KEY = os.getenv("WANDB_API_KEY")

if not SSH_HOST:
    print("Error: SSH_HOST must be set in .env")
    sys.exit(1)

BASE_DIR = Path(__file__).parent.resolve()
PROJECT_DIR = BASE_DIR / "project"
TOOL_SCRIPT = BASE_DIR.parent.parent / "skills" / "ssh" / "scripts" / "ssh_tool.py"

ENV_NAME = f"openclaw_test_{int(time.time())}"
REMOTE_PROJECT_DIR = f"/tmp/{ENV_NAME}_project"

def run_tool(command, *args):
    """Execute the SSH tool wrapper."""
    cmd = [sys.executable, str(TOOL_SCRIPT), command, *args]
    print(f"Running: {' '.join(cmd)}")
    subprocess.check_call(cmd)

def run_tool_output(command, *args):
    """Execute tool and capture output."""
    cmd = [sys.executable, str(TOOL_SCRIPT), command, *args]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Command failed: {result.stderr}")
    return result.stdout.strip()

def setup_project():
    print("Setting up local project...")
    PROJECT_DIR.mkdir(exist_ok=True)
    
    # 1. requirements.txt
    # Minimal deps for quick test. 
    # 'wandb' for tracking, 'numpy' for computation. keeping it light.
    # Note: Torch is heavy to install every time.
    # Maybe check if conda env creation can inherit or use pre-installed?
    # For test speed, we'll try to just install numpy and wandb.
    # GPU check can be done via nvidia-smi without torch if needed, 
    # or assumption is the base system has drivers.
    with open(PROJECT_DIR / "requirements.txt", "w") as f:
        f.write("numpy\nwandb\n")
        
    # 2. Main Script
    script_content = r"""
import os
import sys
import time
import numpy as np
import wandb
import subprocess

print("--- OpenClaw SSH Test Start ---")

# 1. W&B Init
wb_key = os.getenv("WANDB_API_KEY")
if wb_key:
    wandb.login(key=wb_key)
    wandb.init(project="openclaw-ssh-test", name="comprehensive-test-run")
    print("W&B Initialized.")
else:
    print("Warning: WANDB_API_KEY not found.")

# 2. Dependency Test
print(f"Numpy Version: {np.__version__}")

# 3. GPU Test (via nvidia-smi since installing torch is slow)
try:
    smi = subprocess.check_output(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"])
    print(f"GPU Detected: {smi.decode().strip()}")
    if wb_key:
        wandb.log({"gpu_available": True})
except Exception as e:
    print(f"GPU Check Failed: {e}")
    if wb_key:
        wandb.log({"gpu_available": False})

# 4. Long Running Task (Simulation)
print("Starting simulation...")
for i in range(5):
    loss = np.random.random()
    print(f"Step {i+1}/5 - Loss: {loss}")
    if wb_key:
        wandb.log({"loss": loss})
    time.sleep(1)

# 5. Output File
with open("result.txt", "w") as f:
    f.write("SUCCESS")

if wb_key:
    wandb.finish()

print("--- OpenClaw SSH Test End ---")
"""
    with open(PROJECT_DIR / "main.py", "w") as f:
        f.write(script_content)

def main():
    setup_project()
    
    try:
        # 1. Create Conda Env
        print(f"\n[Step 1] Creating Conda Env: {ENV_NAME}...")
        # create valid base env first
        run_tool("conda", "create", "-n", ENV_NAME, "--packages", "python=3.10", "--detach")
        
        # Wait for creation (it's detached but might be fast)
        # Checking env list?
        print("Waiting for env creation...")
        time.sleep(20) # Simple wait
        
        # 2. Install Dependencies
        print("\n[Step 2] Installing Dependencies...")
        # Create temp requirements file on remote? Or just pass packages?
        # Tool supports --packages. 
        # But we have requirements.txt. 
        # Let's use `pip install -r` via exec in env.
        
        # First upload project
        print(f"Uploading project to {REMOTE_PROJECT_DIR}...")
        # Create remote dir first
        run_tool("exec", f"mkdir -p {REMOTE_PROJECT_DIR}")
        
        # Upload files
        for f in ["main.py", "requirements.txt"]:
             run_tool("upload", str(PROJECT_DIR / f), f"{REMOTE_PROJECT_DIR}/{f}")
             
        # Install via pip in env
        # Note: ssh skill `conda exec` wrapper handles activation?
        # Usage: ssh_tool.py exec "cmd" --conda_env my_env
        install_cmd = f"pip install -r {REMOTE_PROJECT_DIR}/requirements.txt"
        print(f"Running install: {install_cmd}")
        run_tool("exec", install_cmd, "--conda_env", ENV_NAME)
        
        # 3. Execute with GPU and W&B
        # Need to pass W&B key env var.
        # SSH tool `exec` generally doesn't pass local envs unless specified?
        # Paramiko env passing is tricky.
        # We can prepend export.
        print("\n[Step 3] Executing Remote Script...")
        
        if not WANDB_API_KEY:
             print("Warning: WANDB_API_KEY missing locally, remote test will skip W&B login.")
             env_prefix = ""
        else:
             env_prefix = f"export WANDB_API_KEY={WANDB_API_KEY} && "
             
        # Run in background (nohup) to simulate 'offline' / detach
        # But we want to 'monitor output'.
        # If we use `exec`, it blocks until done.
        # If we want to detach and monitor, we used `nohup ... > output.log &`
        # Then poll `tail output.log`.
        
        remote_log = f"{REMOTE_PROJECT_DIR}/output.log"
        # Use full path to python in env for detached nohup
        python_bin = f"/root/miniconda3/envs/{ENV_NAME}/bin/python"
        run_cmd = f"{env_prefix} cd {REMOTE_PROJECT_DIR} && nohup {python_bin} main.py > {remote_log} 2>&1 & echo $! > {REMOTE_PROJECT_DIR}/pid"
        
        print(f"Launching background process with {python_bin}...")
        # Note: We don't use --conda_env here because we are manually specifying the python binary
        # and we want to avoid complex wrapping in nohup if possible. 
        # But wait, ssh_tool exec wrapper for --conda_env does `conda run ... cmd`.
        # If we use `conda run` with nohup, it should work.
        # The issue is `nohup sh -c '... conda run ... python ...'`.
        # `conda run` might not put python in path for the subprocess if not shell activated?
        # Actually `conda run -n env python` should work.
        # The failed command was `nohup sh -c '... conda run ... python main.py' ...`
        # Error `nohup: failed to run command 'python': No such file or directory` suggests `conda run` failed to find python?
        # Or maybe `conda` wasn't found in the detached shell?
        # ssh_tool.py uses absolute path for `conda` (/root/miniconda3/bin/conda).
        # Let's try explicit python path to be safe.
        run_tool("exec", run_cmd)
        
        # 4. Monitor Progress
        print("\n[Step 4] Monitoring Progress...")
        for i in range(10):
            time.sleep(2)
            print(f"Poll {i+1}...")
            # Read log
            try:
                # Use 'cat' to read log
                log_content = run_tool_output("exec", f"cat {remote_log}")
                print(f"--- Remote Log ---\n{log_content}")
                
                if "OpenClaw SSH Test End" in log_content:
                    print("Execution Finished!")
                    break
            except Exception as e:
                print(f"Poll error: {e}")
                
        # 5. Get Output
        print("\n[Step 5] Retrieving Artifacts...")
        run_tool("download", f"{REMOTE_PROJECT_DIR}/result.txt", str(BASE_DIR / "result.txt"))
        
        with open(BASE_DIR / "result.txt") as f:
            print(f"Result Verification: {f.read()}")
            
    finally:
        # Cleanup
        print("\n[Cleanup] Deleting Remote Env and Files...")
        try:
             # Delete env
             run_tool("conda", "delete", "-n", ENV_NAME)
             # Delete files
             run_tool("exec", f"rm -rf {REMOTE_PROJECT_DIR}")
             print("Cleanup complete.")
        except Exception as e:
             print(f"Cleanup failed (manual check required): {e}")

if __name__ == "__main__":
    main()
