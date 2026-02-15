
import os
import sys
import wandb
import time
from dotenv import load_dotenv

# Load env
load_dotenv()

WANDB_API_KEY = os.getenv("WANDB_API_KEY")

if not WANDB_API_KEY:
    print("Error: WANDB_API_KEY must be set in .env")
    sys.exit(1)

print(f"Found WANDB_API_KEY: {WANDB_API_KEY[:4]}...{WANDB_API_KEY[-4:]}")

try:
    print("Initializing W&B...")
    wandb.login(key=WANDB_API_KEY)
    
    run = wandb.init(
        project="openclaw-local-test",
        name="wandb-skill-verification",
        config={
            "env": "local-mac",
            "test_type": "manual"
        }
    )
    
    print(f"Run initialized: {run.name} ({run.id})")
    print("Logging metrics...")
    
    for i in range(5):
        val = i ** 2
        wandb.log({"test_metric": val, "step": i})
        print(f"Logged step {i}: {val}")
        time.sleep(0.5)
        
    print("Finishing run...")
    wandb.finish()
    print("W&B Test COMPLETE: SUCCESS")

except Exception as e:
    print(f"W&B Test FAILED: {e}")
    sys.exit(1)
