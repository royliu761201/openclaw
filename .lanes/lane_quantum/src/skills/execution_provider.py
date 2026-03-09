from abc import ABC, abstractmethod
from typing import Dict, Any

class ExecutionProvider(ABC):
    """
    Abstract Base Class for Code Execution.
    Decouples Orchestrator from specific execution backends (Local/SSH/Kaggle).
    """
    @abstractmethod
    async def execute(self, command: str) -> Dict[str, Any]:
        """
        Executes a shell command.
        Returns dict with keys: exit_code, stdout, stderr.
        """
        pass

    @abstractmethod
    async def upload_data(self, local_path: str, remote_path: str):
        pass

    @abstractmethod
    async def download_results(self, remote_path: str, local_path: str):
        pass

# Adapters would go here or in their respective files.
# For now, we define the Interface to enforce the contract.
