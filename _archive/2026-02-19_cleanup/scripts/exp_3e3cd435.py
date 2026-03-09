import os
import sys
import subprocess

def run_experiment():
    print("🚀 Starting MedTime Proxy Verification via Agent Wrapper...")
    
    # We assume we are in the root of the repo (or project root).
    # The command provided by the user:
    cmd = f"{sys.executable} -m projects.medtime.main --task medtime_gvp_cn --proxy"
    
    # Ensure dependencies? (Assume environment is good or standard)
    
    print(f"Executing: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    
    if result.returncode != 0:
        print("Experiment Failed! Output:")
        print(result.stdout)
        print(result.stderr)
        raise RuntimeError(f"Experiment failed with code {result.returncode}")
        
    print("✅ Experiment Complete.")

if __name__ == "__main__":
    run_experiment()