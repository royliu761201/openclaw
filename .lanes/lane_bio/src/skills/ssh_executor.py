import asyncio
import os
from typing import Dict, Optional, Any

from .execution_provider import ExecutionProvider
from .base_skill import BaseSkill
from .remote_ops.remote_shell import RemoteShell
from .remote_ops.remote_transfer import RemoteTransfer
from .remote_ops.hardware_monitor import HardwareMonitor

class SSHExecutor(BaseSkill, ExecutionProvider):
    """
    [Refactored Façade]
    Orchestrates atomic skills: RemoteShell, RemoteTransfer, HardwareMonitor.
    """
    def __init__(self, secrets_path: Optional[str] = None, config: Optional[Dict] = None):
        super().__init__(config)
        from core.config_manager import config_manager
        self.config = config_manager.secrets.get("remote", {})
        
        # Initialize Atomic Skills
        self.shell = RemoteShell(self.config)
        self.transfer = RemoteTransfer(self.config, self.shell)
        self.monitor = HardwareMonitor(self.shell)

    def verify(self) -> bool:
        """Check if we have remote config."""
        return bool(self.config)
    
    # Provider Interface
    async def execute(self, command: str) -> Dict[str, str]:
        return await self.execute_command(command)
        
    async def upload_data(self, local_path: str, remote_path: str):
        return await self.push_file(local_path, remote_path)

    async def download_results(self, remote_path: str, local_path: str):
        return await self.pull_directory(remote_path, local_path)

    # Legacy / Façade Methods
    async def execute_command(self, command: str, timeout: int = 3600) -> Dict[str, str]:
        return await self.shell.execute(command, timeout)

    async def push_file(self, local_path: str, remote_path: str):
        return await self.transfer.push_file(local_path, remote_path)
    
    async def pull_directory(self, remote_path: str, local_path: str):
        return await self.transfer.pull_directory(remote_path, local_path)
        
    async def get_gpu_status(self) -> Dict[str, Any]:
        return await self.monitor.get_gpu_status()
        
    # Keep legacy complex logic (install_package) here or move it?
    # For now, keep it simple or implement as needed. 
    # If the user needs offline install, we should port it to a new EnvProvisioner skill eventually.
    # Currently just stubs to satisfy potential callers or remove if unused.
    # The reflection didn't mandate porting *everything* now, just atomizing execution/transfer.
    # We will omit install_package_offline/relay_model_download for now as they are complex 
    # and likely belong in EnvProvisioner (Phase 2 refactor).

