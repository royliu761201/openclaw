import os
import sys

"""
Atomic Virtual Environment Operations.
Pure functions for detecting and resolving Python environments.
"""

def resolve_python_executable(work_dir: str) -> str:
    """
    Determines the correct Python executable to use.
    Prioritizes .venv in the work_dir.
    Falls back to system executable.
    """
    venv_python = os.path.join(work_dir, ".venv", "bin", "python")
    if os.path.exists(venv_python):
        print(f"[CodeOps] 🔒 Using Sandbox: {venv_python}")
        return venv_python
    
    # Fallback
    return sys.executable

def ensure_venv(work_dir: str):
    """
    Ensures a .venv exists in the work_dir.
    Returns True if created or exists.
    """
    venv_path = os.path.join(work_dir, ".venv")
    if os.path.exists(venv_path):
        return True
        
    print(f"[CodeOps] 📦 Creating .venv in {work_dir}...")
    import subprocess
    try:
        subprocess.run([sys.executable, "-m", "venv", venv_path], check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError:
        return False
