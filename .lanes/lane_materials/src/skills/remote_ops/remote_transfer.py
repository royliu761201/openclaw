
import os
import asyncio
from typing import Dict, Any

class RemoteTransfer:
    """
    Atomic Skill: Handles File Transfer (Push/Pull).
    Supports SCP and Tar-based directory transfers.
    """
    def __init__(self, config: Dict[str, Any], shell):
        self.config = config
        self.shell = shell # Used for pre/post commands (mkdir, tar)

    async def push_file(self, local_path: str, remote_path: str):
        """SCP file to remote"""
        host = self.config.get("host")
        port = self.config.get("port", 22)
        user = self.config.get("user")
        password = self.config.get("pass")
        
        try:
            import asyncssh
            async with asyncssh.connect(host, port=port, username=user, password=password, known_hosts=None) as conn:
                 await asyncssh.scp(local_path, (conn, remote_path))
            return
        except ImportError:
            # TODO: Implement CLI fallback if needed
            print("[RemoteTransfer] asyncssh not found for push.")
            pass
        except Exception as e:
            print(f"[RemoteTransfer] Push Failed: {e}")

    async def pull_directory(self, remote_path: str, local_path: str):
        """
        Pull directory using Tar strategy.
        """
        remote_path = remote_path.rstrip("/")
        parent_dir = os.path.dirname(remote_path)
        folder_name = os.path.basename(remote_path)
        tar_name = f"{folder_name}.tar.gz"
        remote_tar_path = f"{parent_dir}/{tar_name}"
        
        # 1. Remote Compress
        await self.shell.execute(f"tar -czf {remote_tar_path} -C {parent_dir} {folder_name}")
        
        # 2. Pull Tar
        local_tar_path = os.path.join(local_path, tar_name)
        
        host = self.config.get("host")
        port = self.config.get("port", 22)
        user = self.config.get("user")
        password = self.config.get("pass")
        
        try:
            import asyncssh
            async with asyncssh.connect(host, port=port, username=user, password=password, known_hosts=None) as conn:
                 await asyncssh.scp((conn, remote_tar_path), local_tar_path)
                 
                 # 3. Local Extract
                 import tarfile
                 if os.path.exists(local_tar_path):
                     with tarfile.open(local_tar_path, "r:gz") as tar:
                         tar.extractall(path=local_path)
                     os.remove(local_tar_path)
        except Exception as e:
            print(f"[RemoteTransfer] Pull Failed: {e}")
