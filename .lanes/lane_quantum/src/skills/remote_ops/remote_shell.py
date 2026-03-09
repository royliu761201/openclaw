
import asyncio
import os
from typing import Dict, Optional, Any

class RemoteShell:
    """
    Atomic Skill: Executes commands via SSH.
    Handles Connection, Auth, and Timeouts.
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
    async def execute(self, command: str, timeout: int = 3600) -> Dict[str, Any]:
        """
        Runs a command via SSH (asyncssh or CLI fallback).
        """
        host = self.config.get("host")
        port = self.config.get("port", 22)
        user = self.config.get("user")
        password = self.config.get("pass")
        key_path = self.config.get("key_path")
        
        # 1. API Login (asyncssh)
        try:
            import asyncssh
            async with asyncssh.connect(host, port=port, username=user, password=password, known_hosts=None) as conn:
                result = await asyncio.wait_for(conn.run(command), timeout=timeout)
                return {
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "exit_code": result.exit_status
                }
        except ImportError:
            pass # Fallback
        except asyncio.TimeoutError:
            print(f"[RemoteShell] ⏳ Execution Timed Out ({timeout}s).")
            # In a real atomic world, we might call a separate cleanup skill, 
            # but for now we return error. Caller handles cleanup.
            return {"error": "Execution Timed Out", "exit_code": 124}
        except Exception as e:
            print(f"[RemoteShell] API Login Failed: {e}. Falling back to CLI...")

        # 2. CLI Fallback (System SSH)
        ssh_cmd = ["ssh", "-p", str(port), "-o", "StrictHostKeyChecking=no"]
        if key_path and os.path.exists(key_path):
            ssh_cmd.extend(["-i", key_path])
        ssh_cmd.append(f"{user}@{host}")
        ssh_cmd.append(command)
        
        try:
            process = await asyncio.create_subprocess_exec(
                *ssh_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            return {
                "stdout": stdout.decode(),
                "stderr": stderr.decode(),
                "exit_code": process.returncode
            }
        except asyncio.TimeoutError:
             print(f"[RemoteShell] ⏳ CLI Execution Timed Out.")
             try: process.kill()
             except: pass
             return {"error": "Execution Timed Out", "exit_code": 124}
        except Exception as e:
            return {"error": str(e)}
