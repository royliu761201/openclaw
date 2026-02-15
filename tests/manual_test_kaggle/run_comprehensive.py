
import os
import sys
import json
import time
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Load env
load_dotenv()

KAGGLE_USERNAME = os.getenv("KAGGLE_USERNAME")
KAGGLE_KEY = os.getenv("KAGGLE_KEY")
WANDB_API_KEY = os.getenv("WANDB_API_KEY")
HF_TOKEN = os.getenv("HF_TOKEN")

if not KAGGLE_USERNAME or not KAGGLE_KEY:
    print("Error: KAGGLE_USERNAME and KAGGLE_KEY must be set in .env")
    sys.exit(1)

BASE_DIR = Path(__file__).parent.resolve()
DATASET_DIR = BASE_DIR / "dataset"
KERNEL_DIR = BASE_DIR / "kernel"
TOOL_SCRIPT = BASE_DIR.parent.parent / "skills" / "kaggle" / "scripts" / "kaggle_tool.py"

DATASET_SLUG = f"{KAGGLE_USERNAME}/openclaw-test-dataset"
KERNEL_SLUG = f"{KAGGLE_USERNAME}/openclaw-test-kernel"
KERNEL_TITLE = "OpenClaw Test Kernel"

def run_tool(command, *args):
    cmd = [sys.executable, str(TOOL_SCRIPT), command, *args]
    print(f"Running: {' '.join(cmd)}")
    subprocess.check_call(cmd)

def setup_dataset():
    print("Setting up dataset...")
    DATASET_DIR.mkdir(exist_ok=True)
    
    # Metadata
    meta = {
        "title": "OpenClaw Test Dataset",
        "id": DATASET_SLUG,
        "licenses": [{"name": "CC0-1.0"}]
    }
    with open(DATASET_DIR / "dataset-metadata.json", "w") as f:
        json.dump(meta, f, indent=2)
        
    # Helper script
    with open(DATASET_DIR / "helper.py", "w") as f:
        f.write("def compute():\n    return 'HELPER_COMPUTE_OK'\n")
        
    # Data file
    with open(DATASET_DIR / "data.json", "w") as f:
        json.dump({"test_key": "test_value"}, f)
        
    # Secrets (WARNING: uploaded to private dataset)
    secrets = {
        "WANDB_API_KEY": WANDB_API_KEY,
        "HF_TOKEN": HF_TOKEN
    }
    with open(DATASET_DIR / "secrets.json", "w") as f:
        json.dump(secrets, f)
        
    print("Dataset files created.")

def setup_kernel():
    print("Setting up kernel...")
    KERNEL_DIR.mkdir(exist_ok=True)
    
    # Metadata
    meta = {
        "id": KERNEL_SLUG,
        "title": KERNEL_TITLE,
        "code_file": str(KERNEL_DIR / "main.py"),
        "language": "python",
        "kernel_type": "script",
        "is_private": "true",
        "enable_gpu": "true",
        "enable_internet": "true",
        "dataset_sources": [DATASET_SLUG],
        "competition_sources": [],
        "kernel_sources": []
    }
    with open(KERNEL_DIR / "kernel-metadata.json", "w") as f:
        json.dump(meta, f, indent=2)
        
    # Main script
    script_content = r"""
import sys
import os
import json
import time

print("--- OpenClaw Kernel Start ---")

# 1. Setup paths
# Dataset is usually mounted at /kaggle/input/{dataset-slug}
# The slug part in mount path might be normalized (e.g. 'openclaw-test-dataset')
DATASET_MOUNT = "/kaggle/input/openclaw-test-dataset"

print(f"Checking dataset mount at {DATASET_MOUNT}...")
if os.path.exists(DATASET_MOUNT):
    print("Dataset found.")
    sys.path.append(DATASET_MOUNT)
    print(f"Files: {os.listdir(DATASET_MOUNT)}")
else:
    print("Dataset NOT found! Listing /kaggle/input:")
    print(os.listdir("/kaggle/input"))
    # Fallback to look for folder name
    for d in os.listdir("/kaggle/input"):
        possible = os.path.join("/kaggle/input", d)
        if os.path.isdir(possible):
             sys.path.append(possible)
             print(f"Added {possible} to sys.path")
             DATASET_MOUNT = possible

# 2. Dependency Test
try:
    import helper
    print(f"Helper check: {helper.compute()}")
except ImportError as e:
    print(f"ImportError: {e}")

# 3. Data Test
try:
    with open(os.path.join(DATASET_MOUNT, "data.json")) as f:
        data = json.load(f)
        print(f"Data check: {data.get('test_key')}")
except Exception as e:
    print(f"Data read error: {e}")

# 4. Secrets / Env Test
try:
    with open(os.path.join(DATASET_MOUNT, "secrets.json")) as f:
        secrets = json.load(f)
        wb_key = secrets.get("WANDB_API_KEY")
        hf_token = secrets.get("HF_TOKEN")
        print(f"WANDB_API_KEY present: {bool(wb_key)}")
        print(f"HF_TOKEN present: {bool(hf_token)}")
        
        # Set them as env vars for subsequent code
        if wb_key: os.environ["WANDB_API_KEY"] = wb_key
        if hf_token: os.environ["HF_TOKEN"] = hf_token
except Exception as e:
    print(f"Secrets read error: {e}")

# 5. GPU Test
print("Checking GPU...")
try:
    import torch
    print(f"PyTorch Version: {torch.__version__}")
    print(f"CUDA Available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"Device Name: {torch.cuda.get_device_name(0)}")
    else:
        print("GPU NOT AVAILABLE")
except ImportError:
    print("PyTorch not installed")

# 6. Output Generation
with open("output.txt", "w") as f:
    f.write("OpenClaw Comprehensive Test: SUCCESS\n")

print("--- OpenClaw Kernel End ---")
"""
    with open(KERNEL_DIR / "main.py", "w") as f:
        f.write(script_content)
        
    print("Kernel files created.")

def main():
    setup_dataset()
    setup_kernel()
    
    # 1. Push Dataset
    print("\n[Step 1] Pushing Dataset...")
    run_tool("dataset_push", str(DATASET_DIR), "-m", "Auto-update for test", "-z")
    
    # 2. Push Kernel
    print("\n[Step 2] Pushing Kernel...")
    run_tool("kernel_push", str(KERNEL_DIR))
    
    # 3. Poll Monitor
    print("\n[Step 3] Monitoring Kernel...")
    slug = KERNEL_SLUG
    for i in range(40): # Wait up to 20 mins (40 * 30s)
        print(f"Poll check {i+1}/40...")
        
        # Capture output to check status
        result = subprocess.run(
            [sys.executable, str(TOOL_SCRIPT), "kernels_output", slug, str(BASE_DIR / "output")],
            capture_output=True,
            text=True
        )
        
        output = result.stdout + result.stderr
        print(f"Tool Output Snippet: {output[:200].replace(chr(10), ' ')}...") # Print first 200 chars flattened
        
        if "COMPLETE" in output:
            print("Kernel COMPLETE!")
            print(output) # Print full output (logs)
            break
        elif "ERROR" in output:
            print("Kernel FAILURE!")
            print(output)
            break
        else:
            print("Kernel still running/queued. Waiting 30s...")
            time.sleep(30)
            
    print("\n[Step 4] Test Complete. Check output folder.")

if __name__ == "__main__":
    main()
