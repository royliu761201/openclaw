import subprocess
import os
import sys
import json

# Define the skills to test
# Format: (Skill Name, Command List)
SKILLS_TO_TEST = [
    (
        "currency-exchange",
        ["python3", "skills/currency-exchange/scripts/currency_tool.py", "get_rate", "--from", "USD", "--to", "CNY", "--amount", "1"]
    ),
    (
        "ssh",
        ["python3", "skills/ssh/scripts/ssh_tool.py", "--help"]
    ),
    (
        "wandb",
        ["python3", "skills/wandb/scripts/wandb_tool.py", "--help"]
    ),
    (
        "kaggle",
        ["python3", "skills/kaggle/scripts/kaggle_tool.py", "--help"]
    ),
    (
        "web-search",
        ["python3", "skills/web-search/scripts/search.py", "--help"]
    )
]

def run_test(name, cmd):
    print(f"\n[TEST] {name}...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        # Run from workspace root
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=10,
            cwd=os.getcwd() 
        )
        
        if result.returncode == 0:
            print(f"✅ PASS")
            # Try to print first line of output or JSON
            output = result.stdout.strip()
            if output.startswith("{"):
                try:
                    j = json.loads(output)
                    print(f"Output: {json.dumps(j, indent=2)[:200]}...")
                except:
                    print(f"Output: {output[:100]}...")
            else:
                print(f"Output: {output.splitlines()[0] if output else '<no output>'}")
            return True
        else:
            print(f"❌ FAIL (Exit {result.returncode})")
            print(f"Stderr: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    print("=== OpenClaw CLI Skill Verification Suite ===")
    print(f"Working Directory: {os.getcwd()}")
    
    failed = False
    for name, cmd in SKILLS_TO_TEST:
        if not run_test(name, cmd):
            failed = True
            
    if failed:
        print("\nSome tests failed.")
        sys.exit(1)
    else:
        print("\nAll CLI skills is operational.")
        sys.exit(0)
