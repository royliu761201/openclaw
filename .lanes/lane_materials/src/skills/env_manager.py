import os
import subprocess
import yaml
import asyncio
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class EnvironmentSpec:
    name: str
    python_version: str = "3.10"
    dependencies: List[str] = None
    channels: List[str] = None

    def to_yaml(self) -> str:
        data = {
            "name": self.name,
            "channels": self.channels or ["conda-forge", "defaults"],
            "dependencies": [f"python={self.python_version}"] + (self.dependencies or [])
        }
        return yaml.dump(data)

class EnvManager:
    """
    Manages lightweight Conda environments via Micromamba (or Conda fallback).
    Supports 'Environment as Code' via YAML declarations.
    """
    def __init__(self, base_path: str = "envs"):
        self.base_path = base_path
        self.binary = self._detect_binary()
        os.makedirs(base_path, exist_ok=True)

    def _detect_binary(self) -> str:
        # Simple detection logic
        import shutil
        if shutil.which("micromamba"):
            return "micromamba"
        if shutil.which("conda"):
            return "conda"
        # Fallback/Mock for environment where neither is installed (e.g. CI/Dev)
        print("[EnvManager] Warning: Neither micromamba nor conda found. Using 'mock' mode.")
        return "mock"

    async def create_env(self, spec: EnvironmentSpec, force: bool = False) -> bool:
        """Creates or updates a conda environment from spec."""
        yaml_path = os.path.join(self.base_path, f"{spec.name}.yml")
        
        # 1. Write YAML (Environment as Code)
        with open(yaml_path, "w") as f:
            f.write(spec.to_yaml())

        if self.binary == "mock":
            print(f"[EnvManager] [MOCK] Created env {spec.name} from {yaml_path}")
            return True

        # 2. Construct Command
        # micromamba create -f env.yml -y
        cmd = [self.binary, "create", "-f", yaml_path, "-y"]
        if force:
            # Note: mamba might not have force, usually we remove and recreate or use install
            # For simplicity, let's treat force as "remove then create"
            await self.remove_env(spec.name)
        
        print(f"[EnvManager] Building environment {spec.name}...")
        return await self._run_command(cmd)

    async def run_in_env(self, env_name: str, command: str) -> tuple[int, str, str]:
        """
        Runs a shell command inside the specified environment.
        Uses `micromamba run -n {name} {command}` to avoid activation issues.
        """
        if self.binary == "mock":
            print(f"[EnvManager] [MOCK] Running in {env_name}: {command}")
            return 0, "Mock Output", ""

        # Construct: micromamba run -n env_name command
        # Note: command might be a complex string, so we might need to shell=False and split, 
        # or structure it carefully. 
        # For robustness, we treat 'command' as a string and pass it to runner
        full_cmd = [self.binary, "run", "-n", env_name] + command.split()
        
        process = await asyncio.create_subprocess_exec(
            *full_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        return process.returncode, stdout.decode(), stderr.decode()

    async def remove_env(self, env_name: str):
        if self.binary == "mock":
            return
        cmd = [self.binary, "env", "remove", "-n", env_name, "-y"]
        await self._run_command(cmd)

    async def _run_command(self, cmd: List[str]) -> bool:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            print(f"[EnvManager] Error executing {' '.join(cmd)}:\n{stderr.decode()}")
            return False
        return True

    async def self_heal(self, spec: EnvironmentSpec, error_log: str) -> bool:
        """
        Analyzes error log for missing dependencies and updates the environment.
        Uses regex heuristics for common Python errors, falling back to LLM for complex ones.
        """
        import re
        
        # 1. Regex Heuristic for ModuleNotFoundError
        match = re.search(r"ModuleNotFoundError: No module named '([^']+)'", error_log)
        if match:
            missing_module = match.group(1)
            print(f"[EnvManager] Heuristic detected missing module: {missing_module}")
            
            # Add to spec dependencies if not present
            if spec.dependencies is None:
                spec.dependencies = []
            
            # Simple mapping for common mismatches (sklearn -> scikit-learn)
            # This could be expanded or offloaded to LLM
            pkg_map = {
                "sklearn": "scikit-learn",
                "cv2": "opencv",
                "PIL": "pillow"
            }
            pkg_name = pkg_map.get(missing_module, missing_module)
            
            if pkg_name not in spec.dependencies:
                spec.dependencies.append(pkg_name)
                print(f"[EnvManager] Adding {pkg_name} to environment spec and updating...")
                return await self.create_env(spec, force=False) # create_env handles update effectively in conda
        
        print("[EnvManager] No heuristic fix found. (LLM Analysis would trigger here)")
        return False
