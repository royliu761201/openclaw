import os
import json
import subprocess
import sys

SECRETS_PATH = os.environ.get("SECRETS_FILE_PATH", "/root/research_bot/secrets.json")


# Get the bin directory of the current python environment
BIN_DIR = os.path.dirname(sys.executable)
KAGGLE_BIN = os.path.join(BIN_DIR, "kaggle")
WANDB_BIN = os.path.join(BIN_DIR, "wandb")

def verify_kaggle_account(username, key):
    print(f"\n🔍 Verifying Kaggle Account: {username} ...")
    
    # Set environment variables for this specific check
    env = os.environ.copy()
    env["KAGGLE_USERNAME"] = username
    env["KAGGLE_KEY"] = key
    
    # Try listing competitions (quick network check)
    try:
        if not os.path.exists(KAGGLE_BIN):
            print(f"❌ Error: Kaggle binary not found at {KAGGLE_BIN}")
            return False

        # We invoke kaggle CLI using absolute path
        result = subprocess.run(
            [KAGGLE_BIN, "competitions", "list"],
            env=env,
            capture_output=True,
            text=True,
            timeout=15
        )
        
        if result.returncode == 0:
            print(f"✅ Success! Connected as {username}")
            return True
        else:
            print(f"❌ Failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def verify_wandb(key):
    print(f"\n🔍 Verifying W&B Integration ...")
    env = os.environ.copy()
    env["WANDB_API_KEY"] = key
    
    try:
        if not os.path.exists(WANDB_BIN):
            print(f"❌ Error: W&B binary not found at {WANDB_BIN}")
            return False

        result = subprocess.run(
            [WANDB_BIN, "login", "--relogin", key],
            env=env,
            capture_output=True,
            text=True,
            timeout=15
        )
        if result.returncode == 0:
            print("✅ Success! W&B Login Verified.")
            return True
        else:
            print(f"❌ Failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def main():
    if not os.path.exists(SECRETS_PATH):
        print(f"❌ Secrets file not found at {SECRETS_PATH}")
        sys.exit(1)
        
    with open(SECRETS_PATH, 'r') as f:
        secrets = json.load(f)

    # Verify W&B (New Requirement)
    wandb_key = secrets.get("wandb_api_key")
    if wandb_key:
        verify_wandb(wandb_key)
    else:
        print("❌ No 'wandb_api_key' in secrets.json")
        
    kaggle_creds = secrets.get("kaggle", {})
    
    if not kaggle_creds:
        print("❌ No 'kaggle' section in secrets.json")
        sys.exit(1)
        
    success_count = 0
    total_count = len(kaggle_creds)
    
    print("\n🌍 Checking Remote Proxy Configuration...")
    print(f"   all_proxy: {os.environ.get('all_proxy', 'Not Set')}")
    
    for user, key in kaggle_creds.items():
        if verify_kaggle_account(user, key):
            success_count += 1
            
    print(f"\n🎉 Verification Complete: {success_count}/{total_count} accounts valid.")
    
    if success_count == total_count:
        print("💡 Theory Confirmed: You can run parallel experiments across all accounts.")

if __name__ == "__main__":
    main()
