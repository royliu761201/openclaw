import os
import sys
import subprocess

# 1. Setup
print("=== [Kaggle] Setting up Evo-Distill Environment ===")
# In a real P100 run, we'd ensuring PyTorch Graph Geometric is present
# subprocess.check_call([sys.executable, "-m", "pip", "install", "torch_geometric"])

# 2. Execution
print("=== [Kaggle] Running Fixed-Point Simulation ===")
cmd = [sys.executable, "src/evo_distill/fixed_point_sim.py"]
ret = subprocess.call(cmd, cwd=os.getcwd()) # Ensure root cwd

if ret == 0:
    print("✅ Evo-Distill Experiment Success")
else:
    print("❌ Evo-Distill Experiment Failed")
