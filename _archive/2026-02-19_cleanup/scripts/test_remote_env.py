import socket
import os
import sys

def check_step(name, status, details=""):
    icon = "✅" if status else "❌"
    print(f"{icon} {name}: {details}")

print("\n🔍 Remote Environment Self-Check\n" + "="*30)

# 1. Hostname
check_step("Host", True, socket.gethostname())

# 2. Python & Libraries
try:
    import torch
    import numpy
    check_step("Python", True, f"{sys.version.split()[0]} (torch={torch.__version__})")
except ImportError as e:
    check_step("Python", False, str(e))

# 3. GPU
if torch.cuda.is_available():
    devices = [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())]
    check_step("GPU", True, f"{len(devices)}x {devices[0]}")
else:
    check_step("GPU", False, "No CUDA devices found")

# 4. Data Lake
data_path = "/root/research_bot/data"
if os.path.exists(data_path):
    projects = [d for d in os.listdir(data_path) if os.path.isdir(os.path.join(data_path, d))]
    check_step("Data Lake", True, f"Found {len(projects)} projects ({', '.join(projects[:3])}...)")
else:
    check_step("Data Lake", False, "Path not found")

# 5. Git Identity
try:
    git_user = os.popen("git config user.name").read().strip()
    check_step("Git ID", True, git_user)
except:
    check_step("Git ID", False, "Failed to read config")

print("="*30 + "\n")
