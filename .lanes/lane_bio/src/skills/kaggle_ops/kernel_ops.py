import os
import json
import asyncio
from typing import Dict, Any, Optional

"""
Atomic Kaggle Kernel Operations.
Delegates to `kaggle` CLI.
"""

async def push_kernel(slug: str, work_dir: str) -> Dict[str, Any]:
    """Pushes a kernel from a prepared work_dir."""
    cmd = ["kaggle", "kernels", "push", "-p", work_dir]
    
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
             return {
                 "status": "Success",
                 "logs": stdout.decode()
             }
        else:
             return {
                 "status": "Failure",
                 "error": stderr.decode()
             }
    except FileNotFoundError:
        return {"status": "Failure", "error": "Kaggle CLI not found."}

async def check_status(slug: str) -> str:
    """Returns: 'running', 'complete', 'error', 'unknown'."""
    cmd = ["kaggle", "kernels", "status", slug]
    
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    out_text = stdout.decode().lower()
    
    if "complete" in out_text: return "complete"
    if "running" in out_text: return "running"
    if "error" in out_text: return "error"
    return "unknown"

async def get_output(slug: str, dest_dir: str) -> Dict[str, str]:
    """Downloads kernel output."""
    os.makedirs(dest_dir, exist_ok=True)
    cmd = ["kaggle", "kernels", "output", slug, "-p", dest_dir]
    
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    
    if proc.returncode == 0:
        return {"status": "success", "path": dest_dir}
    else:
        return {"status": "failure", "error": stderr.decode()}

async def list_running_kernels() -> Dict[str, Any]:
    """Lists currently running kernels."""
    cmd = ["kaggle", "kernels", "list", "--mine", "--status", "running", "--csv"]
    
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        return {"stdout": stdout.decode(), "stderr": stderr.decode(), "exit_code": process.returncode}
    except Exception as e:
        return {"error": str(e)}
