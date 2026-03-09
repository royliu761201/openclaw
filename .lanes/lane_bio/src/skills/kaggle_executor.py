import os
import asyncio
from typing import Dict, Optional, Any
from .base_skill import BaseSkill
import shutil
import json
from .kaggle_ops import kernel_ops, config_ops

class KaggleExecutor(BaseSkill):
    """
    Executes code on Kaggle Kernels via the Kaggle CLI.
    Requires ~/.kaggle/kaggle.json to be configured.
    
    Refactored to delegate to `kaggle_ops`.
    """
    def __init__(self, kernel_prefix: Optional[str] = None, config: Optional[Dict] = None):
        super().__init__(config)
        from core.config_manager import config_manager
        
        # Load defaults from settings.yaml
        self.kernel_prefix = kernel_prefix or config_manager.get("kaggle", {}).get("kernel_prefix", "researchbot")
        
    def verify(self) -> bool:
        """Check if kaggle CLI is installed."""
        return shutil.which("kaggle") is not None
        
    async def push_notebook(self, code: str, title: str, dataset_slugs: Optional[list] = None, secrets: Optional[Dict] = None, git_repo: Optional[str] = None, verify_only: bool = False) -> Dict[str, str]:
        """
        Pushes a notebook to Kaggle Kernels with Secret Injection.
        """
        print(f"[KaggleExecutor] Pushing kernel: {title}...")
        
        # 1. Create a workspace
        slug = title.lower().replace(" ", "-")[:40]
        # Sanitize slug
        slug = "".join([c for c in slug if c.isalnum() or c == "-"])
        
        work_dir = f".kaggle_builds/{slug}"
        os.makedirs(work_dir, exist_ok=True)
        
        # 2. Key Metadata & Notebook Generation (using Ops)
        config_ops.generate_metadata(
            os.path.join(work_dir, "kernel-metadata.json"), 
            self.kernel_prefix, 
            slug, 
            title, 
            dataset_slugs
        )
            
        init_code = config_ops.build_init_code(secrets, git_repo)
        notebook_content = config_ops.construct_notebook_json(init_code, code)
            
        with open(os.path.join(work_dir, "notebook.ipynb"), "w") as f:
            json.dump(notebook_content, f, indent=1)
            
        # 3. Push or Verify
        if verify_only:
             print(f"[KaggleExecutor] 🧪 Verify Only: Build created at {work_dir}")
             return {
                 "status": "Success",
                 "url": "local-verify-mode",
                 "logs": f"Build persisted at {work_dir}",
                 "build_path": work_dir
             }
        
        # Async Push via Ops
        result = await kernel_ops.push_kernel(slug, work_dir)
        if result["status"] == "Success":
             # Construct URL manually as it's not in CLI output usually
             result["url"] = f"https://kaggle.com/username/{self.kernel_prefix}-{slug}"
        
        return result

    async def monitor_kernel(self, slug: str) -> str:
        """
        id: e.g. username/researchbot-my-title
        Returns: 'running', 'complete', 'error', 'unknown'
        """
        return await kernel_ops.check_status(slug)

    async def get_kernel_output(self, slug: str, dest_dir: str) -> Dict[str, str]:
        """
        Downloads output files from a completed kernel.
        """
        return await kernel_ops.get_output(slug, dest_dir)

    async def get_resource_status(self) -> Dict[str, Any]:
        """
        Queries Kaggle for active kernel slots.
        """
        if not self.verify(): return {}
        
        res = await kernel_ops.list_running_kernels()
        
        if res.get("exit_code", 0) != 0:
            print(f"[Kaggle] Status Check Failed: {res.get('stderr')}")
            return {}
            
        # Parse CSV
        # ref,title,author,lastRunTime,totalVotes
        stdout = res.get("stdout", "")
        lines = stdout.strip().splitlines()
        # Header is usually first line
        running_count = max(0, len(lines) - 1)
        
        # Constraints
        limit = 2 # Standard Kaggle Limit per account
        
        return {
            "name": f"Kaggle (P100) - {running_count}/{limit} Active",
            "gpu": "NVIDIA Tesla P100",
            "running_count": running_count,
            "limit": limit,
            "vram": "16GB",
            "available": running_count < limit,
            "constraints": "Strict 12h limit, No Internet in comp (optional)."
        }

    async def download_results(self, remote_path: str, local_path: str):
        """
        Downloads results from Kaggle.
        """
        print(f"[KaggleExecutor] 📥 Pulling Results from Kernel '{remote_path}' to '{local_path}'")
        await self.get_kernel_output(remote_path, local_path)

