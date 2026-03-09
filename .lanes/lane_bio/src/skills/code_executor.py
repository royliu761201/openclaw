import asyncio
import os
from typing import Dict, Optional

from .base_skill import BaseSkill
from .code_ops import venv_ops, exec_ops

class CodeExecutor(BaseSkill):
    """
    Executes Python code locally via subprocess.
    Refactored to use atomic `code_ops`.
    """
    def __init__(self, timeout: int = 30, work_dir: str = ".", config: Optional[Dict] = None):
        super().__init__(config)
        self.timeout = config.get("timeout", timeout) if config else timeout
        self.work_dir = os.path.abspath(work_dir)
        
        # Ensure venv exists if we are in strict mode (optional)
        # venv_ops.ensure_venv(self.work_dir)

    def verify(self) -> bool:
        """Check if python is available."""
        exe = venv_ops.resolve_python_executable(self.work_dir)
        return os.path.exists(exe)

    async def execute_python(self, code: str) -> Dict[str, str]:
        """
        Runs Python code string in a subprocess.
        """
        python_exec = venv_ops.resolve_python_executable(self.work_dir)
        print(f"[CodeExecutor] Executing code (timeout={self.timeout}s)...")
        
        return await exec_ops.run_subprocess_code(python_exec, code, self.work_dir, self.timeout)

    async def execute_file(self, filename: str) -> Dict[str, str]:
        """
        Runs a Python file.
        """
        python_exec = venv_ops.resolve_python_executable(self.work_dir)
        print(f"[CodeExecutor] Running file {filename}...")
        
        return await exec_ops.run_subprocess_file(python_exec, filename, self.work_dir, self.timeout)

    async def execute_command(self, cmd: str) -> Dict[str, str]:
        """
        Runs a shell command.
        """
        print(f"[CodeExecutor] Executing shell: {cmd}...")
        return await exec_ops.run_subprocess_command(cmd, self.work_dir, self.timeout)
