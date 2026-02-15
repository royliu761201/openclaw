
import subprocess
import os
import sys
from dotenv import load_dotenv

# Force load .env from current directory
load_dotenv(override=True)

def run_tool(script_rel_path, args):
    base_dir = os.getcwd()
    script_path = os.path.join(base_dir, script_rel_path)
    
    if not os.path.exists(script_path):
        print(f"❌ Script not found: {script_path}")
        return None

    cmd = ["python3", script_path] + args
    print(f"Running: {' '.join(cmd)}...")
    
    try:
        # Pass current environment which includes loaded .env vars
        result = subprocess.run(cmd, capture_output=True, text=True, env=os.environ)
        
        if result.returncode != 0:
            print(f"❌ Command failed with return code {result.returncode}")
            print(f"Stderr: {result.stderr}")
            return None
            
        print(f"✅ Success")
        return result.stdout.strip()
    except Exception as e:
        print(f"❌ Execution error: {e}")
        return None

def main():
    print("🚀 Starting Skills Integration Test (Headless)\n")

    # 1. Kaggle: Fetch latest kernel status
    print("--- Step 1: Querying Kaggle Kernels ---")
    kaggle_out = run_tool("skills/kaggle/scripts/kaggle_tool.py", 
                         ["kernels_list", "--user", "xiaohualiu", "--search", "openclaw"])
    
    if not kaggle_out:
        print("❌ Kaggle Step Failed")
        sys.exit(1)
    
    # Parse just to verify we got data
    print(f"   output preview: {kaggle_out[:100]}...")
    
    # 2. SSH: Check Remote System (Simulating a check on the training machine)
    print("\n--- Step 2: Checking Remote Server (SSH) ---")
    # Using 'uname -a' as a safe, generic check if nvidia-smi isn't present
    ssh_out = run_tool("skills/ssh/scripts/ssh_tool.py", 
                      ["exec", "uname -a"])
    
    if not ssh_out:
        print("❌ SSH Step Failed")
        sys.exit(1)
        
    print(f"   remote info: {ssh_out}")

    # 3. WandB: Log the successful check
    print("\n--- Step 3: Logging Result to WandB ---")
    wandb_out = run_tool("skills/wandb/scripts/wandb_tool.py", 
                        ["log", 
                         "--project", "verification-test", 
                         "--metric", "integration_check_passed", 
                         "--value", "1"])
                         
    if not wandb_out:
        print("❌ WandB Step Failed")
        sys.exit(1)
        
    print(f"   wandb response: {wandb_out}")

    print("\n✨ INTEGRATION TEST PASSED: interaction verified.")

if __name__ == "__main__":
    main()
