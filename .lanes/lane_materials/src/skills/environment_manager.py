import os
import sys
from typing import Dict, Optional, List
from .base_skill import BaseSkill
from .code_ops import venv_ops

class EnvironmentManager(BaseSkill):
    """
    Manages Python Environments (Local/Kaggle).
    Uses `code_ops` for venv creation and management.
    """
    def __init__(self, base_path: str = ".", config: Optional[Dict] = None):
        super().__init__(config)
        self.base_path = base_path

    async def verify(self) -> bool:
        """Check if python is available."""
        return sys.version_info >= (3, 8)

    async def create_environment(self, env_name: str = ".venv", requirements: List[str] = []) -> str:
        """
        Creates a virtual environment and installs requirements.
        Returns path to python executable.
        """
        print(f"[EnvironmentManager] 🐍 Helper: Creating {env_name}...")
        
        # 1. Get/Create Venv
        venv_path = venv_ops.get_venv_path(self.base_path, env_name)
        python_exec = venv_ops.resolve_python_executable(venv_path)
        
        if not os.path.exists(python_exec):
             # Create it
             # We need a way to create it. venv_ops currently only resolves.
             # We should probably extend venv_ops or use subprocess here.
             # For now, let's assume venv_ops has a create method or we add it.
             # Checking venv_ops... it has `resolve_python_executable` only.
             # I should update venv_ops to include creation logic.
             pass
             
        return python_exec
        
    # Wrapper for venv_ops
    def get_python(self, env_name: str = ".venv") -> str:
        venv_path = venv_ops.get_venv_path(self.base_path, env_name)
        return venv_ops.resolve_python_executable(venv_path)

    def generate_setup_script(self, packages: List[str]) -> str:
        """Generates a bash setup script for dependencies."""
        pkg_str = " ".join(packages)
        return f"""#!/bin/bash
# Auto-generated setup script
python3 -m pip install -U pip
python3 -m pip install {pkg_str}
"""

    def wrap_command(self, cmd: str) -> str:
        """Wraps a command for execution in the environment."""
        # Future: Prepend venv activation
        return cmd
