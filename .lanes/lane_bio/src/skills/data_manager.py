import os
import asyncio
from typing import Dict, Any, Optional, List
from .base_skill import BaseSkill
from .execution_provider import ExecutionProvider
from .data_ops import transfer_ops, registry_ops

class DataManager(BaseSkill):
    """
    Manages dataset paths and ensures availability using atomic `data_ops`.
    Strategies:
    1. Local: Check Shared Hub -> Download (via ops).
    2. Remote (SSH): Check Remote -> Download Remote -> Push Local.
    3. Kaggle: Return Dataset Slug.
    """
    def __init__(self, base_path: str = ".", config: Optional[Dict] = None):
        super().__init__(config)
        from core.config_manager import config_manager
        
        # Load Registry from Config
        self.registry = config_manager.datasets
        
        # Initial paths from Config
        self.remote_root = config_manager.get("paths", {}).get("remote_root", "/tmp/data")
        self.local_root = os.path.join(base_path, config_manager.get("paths", {}).get("data_root", "data"))
        self.shared_root = os.path.join(base_path, config_manager.get("paths", {}).get("shared_vault", "research_vault/library/datasets"))
        
        os.makedirs(self.local_root, exist_ok=True)
        os.makedirs(self.shared_root, exist_ok=True)

    def verify(self) -> bool:
        """Check if data directories are writable."""
        return os.access(self.shared_root, os.W_OK)

    def get_data_path(self, dataset_name: str, remote: bool = False, kaggle: bool = False) -> str:
        """Returns the simplified path string for code injection."""
        if kaggle:
            return f"/kaggle/input/{dataset_name}"
        if remote:
            return os.path.join(self.remote_root, dataset_name)
            
        # Check Shared Hub first
        shared_path = os.path.join(self.shared_root, dataset_name)
        if os.path.exists(shared_path):
            return shared_path
            
        return os.path.join(self.local_root, dataset_name)

    async def ensure_dataset(self, 
                             dataset_name: str, 
                             remote_provider: Optional[ExecutionProvider] = None,
                             is_kaggle: bool = False,
                             download_url: Optional[str] = None) -> Any:
        """
        Ensures dataset exists in the target environment.
        """
        print(f"[DataManager] 📦 Ensuring Dataset: {dataset_name} (Remote: {bool(remote_provider)}, Kaggle: {is_kaggle})")

        # 1. KAGGLE
        if is_kaggle:
            return dataset_name 

        # 2. RESOLVE SOURCE
        if not download_url:
            meta = registry_ops.resolve_dataset_source(self.registry, dataset_name)
            if meta:
                download_url = meta["url"]
        
        local_path = os.path.join(self.shared_root, dataset_name)
        
        # 3. REMOTE STRATEGY
        if remote_provider:
            remote_path = os.path.join(self.remote_root, dataset_name)
            
            # Check Remote
            check_cmd = f"test -d {remote_path} && echo 'EXISTS'"
            res = await remote_provider.execute(check_cmd)
            
            if "EXISTS" in res.get("stdout", ""):
                 print(f"[DataManager] ✅ Dataset exists on Remote: {remote_path}")
                 return remote_path

            # Remote Download
            if download_url:
                print(f"[DataManager] ☁️ Attempting Remote Download from {download_url}...")
                archive_name = "data.zip"
                dl_cmd = f"mkdir -p {remote_path} && cd {remote_path} && wget -O {archive_name} {download_url} && unzip {archive_name} && rm {archive_name}"
                res = await remote_provider.execute_command(dl_cmd)
                if res.get("exit_code") == 0:
                    return remote_path
            
            # Fallback: Push Local
            if not os.path.exists(local_path):
                 await self._download_local(dataset_name, download_url, local_path)
            
            await remote_provider.push_directory(local_path, remote_path)
            return remote_path

        # 4. LOCAL ONLY
        if not os.path.exists(local_path):
             await self._download_local(dataset_name, download_url, local_path)
             
        return local_path

    async def _download_local(self, name: str, url: Optional[str], path: str):
        """Delegates to transfer_ops."""
        if not url:
            print(f"[DataManager] No URL provided for {name}. Creating DUMMY artifact.")
            transfer_ops.create_dummy_dataset(path)
            return

        print(f"[DataManager] ⬇️  Downloading {name} to {path}...")
        
        if "drive.google.com" in url:
            # We assume gdown logic is special, maybe should be in transfer_ops too?
            # For now, let's keep simple transfer ops generic.
            # If we really want gdown, we should move it to transfer_ops.
            # Let's trust standard download first.
            success = transfer_ops.download_and_extract(url, path)
        else:
            success = transfer_ops.download_and_extract(url, path)
            
        if not success:
             print(f"[DataManager] ❌ Download failed.")

