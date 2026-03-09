import os
import asyncio
from typing import Optional
from schemas.experiment import ExperimentConfig, validationLevel
from .base_skill import BaseSkill

class ExperimentRunner(BaseSkill):
    """
    Executes experiments with:
    1. Hierarchical Validation (T1 -> T2 -> T3)
    2. Resume Capabilities (Auto-load checkpoints)
    3. Fail-Fast Monitoring
    """
    def __init__(self, lab_manager):
        # lab_manager is likely EnvironmentManager or SSHExecutor
        self.lab = lab_manager

    async def run_experiment(self, config: ExperimentConfig):
        """
        Orchestrates the T1 -> T2 -> T3 flow if needed, or runs a specific level.
        """
        # 1. T1: Smoke Test (Always run unless skipped)
        if config.validation_level == validationLevel.T3_FULL:
            print(f"[Runner] Starting T1 Smoke Test for {config.task_id}...")
            success = await self._run_level(config, validationLevel.T1_SMOKE)
            if not success:
                print("[Runner] T1 Smoke Test FAILED. Aborting.")
                return False

        # 2. T2: Proxy (Intermediate)
        if config.validation_level == validationLevel.T3_FULL:
             print(f"[Runner] Starting T2 Proxy Test for {config.task_id}...")
             success = await self._run_level(config, validationLevel.T2_PROXY)
             if not success:
                 print("[Runner] T2 Proxy Test FAILED. Aborting.")
                 return False

        # 3. T3: Full Run
        print(f"[Runner] Starting Full Experiment for {config.task_id}...")
        return await self._run_level(config, validationLevel.T3_FULL)

    async def _run_level(self, config: ExperimentConfig, level: validationLevel) -> bool:
        """
        Runs the command with modified flags for the specific level.
        Assumes the underlying script accepts --smoke_test or --fast_dev_run flags.
        """
        cmd = config.cmd
        
        # Inject flags based on level
        if level == validationLevel.T1_SMOKE:
            # Assuming widely used Pytorch Lightning style or custom standard
            cmd += " --smoke_test --epochs 1 --batch_size 2"
        elif level == validationLevel.T2_PROXY:
            cmd += " --proxy_data --epochs 5"
        
        # Resume logic
        if config.resume and level == validationLevel.T3_FULL:
            last_ckpt = self._find_checkpoint(config.output_dir)
            if last_ckpt:
                cmd += f" --resume_from {last_ckpt}"
                print(f"[Runner] Resuming from {last_ckpt}")

        return await self._execute_safe(config.env_name, cmd)

    def _find_checkpoint(self, output_dir: str) -> Optional[str]:
        # Simple heuristic: find 'last.pth' or 'ckpt_*.pth'
        if not os.path.exists(output_dir):
            return None
        
        # Check specific names first
        last = os.path.join(output_dir, "last.pth")
        if os.path.exists(last):
            return last
            
        # Or sort by time
        files = [os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.endswith(".pth")]
        if not files:
            return None
        return max(files, key=os.path.getmtime)

    async def _execute_safe(self, env_name: str, cmd: str) -> bool:
        """
        Wraps execution with error catching and result validation.
        """
        print(f"[Runner] Executing: {cmd}")
        code, stdout, stderr = await self.lab.run_in_env(env_name, cmd)
        
        if code != 0:
            print(f"[Runner] Failed with code {code}.")
            # Here we would trigger the 'Analyze' loop (Gemini)
            return False
            
        return True
