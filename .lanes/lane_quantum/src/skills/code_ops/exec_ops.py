import asyncio
import os
from typing import Dict, Optional, Tuple

"""
Atomic Execution Operations.
Pure functions for running subprocesses with timeouts.
"""

async def run_subprocess_code(python_exec: str, code: str, cwd: str, timeout: int) -> Dict[str, str]:
    """
    Runs python code string in a subprocess.
    """
    try:
        proc = await asyncio.create_subprocess_exec(
            python_exec, "-c", code,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            return {
                "stdout": stdout.decode(),
                "stderr": stderr.decode(),
                "exit_code": proc.returncode,
                "error": None
            }
        except asyncio.TimeoutError:
            try:
                proc.kill()
            except ProcessLookupError:
                pass
            return {
                "stdout": "",
                "stderr": f"Execution timed out after {timeout}s",
                "exit_code": -1,
                "error": "Timeout"
            }
            
    except Exception as e:
        return {
            "stdout": "",
            "stderr": str(e),
            "exit_code": -1,
            "error": str(e)
        }

async def run_subprocess_file(python_exec: str, filename: str, cwd: str, timeout: int) -> Dict[str, str]:
    """
    Runs a python file in a subprocess.
    """
    # Verify file exists
    if not os.path.exists(os.path.join(cwd, filename)):
         return {
            "stdout": "",
            "stderr": f"File not found: {filename}",
            "exit_code": -1,
            "error": "FileNotFound"
        }

    try:
        proc = await asyncio.create_subprocess_exec(
            python_exec, filename,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            return {
                "stdout": stdout.decode(),
                "stderr": stderr.decode(),
                "exit_code": proc.returncode,
                "error": None
            }
        except asyncio.TimeoutError:
             try:
                proc.kill()
             except ProcessLookupError:
                pass
             return {
                "stdout": "",
                "stderr": f"Execution timed out after {timeout}s",
                "exit_code": -1,
                "error": "Timeout"
            }
            
    except Exception as e:
        return {
            "stdout": "",
            "stderr": str(e),
            "exit_code": -1,
            "error": str(e)
        }

async def run_subprocess_command(cmd: str, cwd: str, timeout: int) -> Dict[str, str]:
    """
    Runs a shell command in a subprocess.
    """
    try:
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            return {
                "stdout": stdout.decode(),
                "stderr": stderr.decode(),
                "exit_code": proc.returncode,
                "error": None
            }
        except asyncio.TimeoutError:
            try:
                proc.kill()
            except ProcessLookupError:
                pass
            return {
                "stdout": "",
                "stderr": f"Execution timed out after {timeout}s",
                "exit_code": -1,
                "error": "Timeout"
            }
            
    except Exception as e:
        return {
            "stdout": "",
            "stderr": str(e),
            "exit_code": -1,
            "error": str(e)
        }
