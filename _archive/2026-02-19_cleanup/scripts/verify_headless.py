#!/usr/bin/env python3
import subprocess
import os
import sys
import json

# Define the skills to test
# Format: (Skill Name, Command List)
SKILLS_TO_TEST = [
    (
        "currency-exchange",
        ["./skills/currency-exchange/scripts/currency_tool.py", "get_rate", "--from", "USD", "--to", "CNY", "--amount", "1"]
    ),
    (
        "ssh",
        ["./skills/ssh/scripts/ssh_tool.py", "--help"]
    ),
    (
        "wandb",
        ["./skills/wandb/scripts/wandb_tool.py", "--help"]
    ),
    (
        "kaggle",
        ["./skills/kaggle/scripts/kaggle_tool.py", "--help"]
    ),
    (
        "academic-search",
        ["./skills/academic-search/scripts/search_arxiv.py", "--help"]
    ),
    (
        "exa-search",
        ["./skills/exa-search/scripts/exa_search.py", "--help"]
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
            timeout=15,
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
                # Print first non-empty line
                lines = [l for l in output.splitlines() if l.strip()]
                print(f"Output: {lines[0] if lines else '<no output>'}")
            return True
        else:
            print(f"❌ FAIL (Exit {result.returncode})")
            print(f"Stderr: {result.stderr}")
            if "ModuleNotFoundError" in result.stderr:
                 print("  -> Hint: Missing dependencies? Check requirements.txt")
            return False

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    print("=== OpenClaw CLI Skill Verification Suite ===")
    print(f"Working Directory: {os.getcwd()}")
    
    # Ensure scripts are executable
    for _, cmd in SKILLS_TO_TEST:
        script_path = cmd[0]
        if os.path.exists(script_path) and not os.access(script_path, os.X_OK):
             print(f"Warning: {script_path} not executable. Fixing...")
             os.system(f"chmod +x {script_path}")

    failed = False
    for name, cmd in SKILLS_TO_TEST:
        if not run_test(name, cmd):
            failed = True
            
    if failed:
        print("\nSome tests failed.")
        sys.exit(1)
    else:
        print("\n🎉 All CLI skills are operational!")
        sys.exit(0)
