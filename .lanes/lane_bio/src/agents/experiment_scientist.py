
import os
import re
import hashlib
import asyncio
from typing import Dict, Any, List, Optional
from .base_agent import BaseAgent
from config import ModelTier
from core.rich_logger import RichLogger

class ExperimentScientist(BaseAgent):
    """
    Dedicated Agent for conducting scientific experiments.
    Responsibilities:
    1. Code Generation (Fail-Fast, Scientific Rigor)
    2. Execution Routing (Local vs SSH vs Kaggle)
    3. Self-Healing (Environment & Code Repair)
    4. Data Synchronization
    """

    def __init__(self, model_client, skill_registry):
        super().__init__(name="ExperimentScientist", model_client=model_client, skill_registry=skill_registry)
        self.model_client = self.client # Alias for code compatibility
        self.code_executor = skill_registry.get_skill("CodeExecutor")
        self.ssh_executor = skill_registry.get_skill("SSHExecutor")
        self.kaggle_executor = skill_registry.get_skill("KaggleExecutor")
        self.env_manager = skill_registry.get_skill("EnvironmentManager")
        self.data_manager = skill_registry.get_skill("DataManager")
        self.wandb = skill_registry.get_skill("WandBObserver")
        # Universal Healer (Core Component)
        self.wandb = skill_registry.get_skill("WandBObserver")
        self.git_manager = None
        
        # New Ops Imports (Runtime)
        from skills import healer_ops, reflection_ops
        self.healer_ops = healer_ops
        self.reflection_ops = reflection_ops
        
    # Environment Knowledge Base
    ENV_SPECS = {
        "local": {
            "name": "Local Mac (MPS)",
            "gpu": "Apple M-Series (MPS)",
            "vram": "Unified Memory (Low/Medium)",
            "constraints": "Use 'mps' device if available. Keep batch sizes small. No CUDA."
        },
        "ssh": {
            "name": "Remote Cluster (L20)",
            "gpu": "NVIDIA L20",
            "vram": "24GB GDDR6",
            "cuda": "12.x",
            "constraints": "Maximize usage of 24GB VRAM. Use 'cuda'. Flash Attention supported."
        },
        "kaggle": {
            "name": "Kaggle Kernel (P100)",
            "gpu": "NVIDIA Tesla P100",
            "vram": "16GB",
            "constraints": "Strict 12h runtime limit. No internet for some comps (but valid here). Use 'cuda'. Old architecture (Volta)."
        }
    }

    async def conduct_experiment(self, 
                               topic: str, 
                               idea: str, 
                               human_feedback: str, 
                               git_manager,
                               autonomous_mode: bool = False) -> Dict[str, Any]:
        """
        Main entry point for conducting an experiment.
        """
        RichLogger.log_agent_start("ExperimentScientist", f"Topic: {topic}")
        
        try:
            # 1. Observability Init
            self.wandb.init_run(f"exp_{topic}", {"model": "Gemini", "agent": "ExperimentScientist"})
            
            # Updated Imports
            from schemas.experiment import ExperimentConfig, validationLevel
            from skills.experiment_runner import ExperimentRunner
            
            # 2. Data Preparation
            dataset_name = "mnist_dummy"
            
            # Smart Routing Decision
            provider, is_remote, is_kaggle = self._route_provider(autonomous_mode)

            # Resolve Environment Context
            if is_kaggle:
                env_type = "kaggle"
            elif is_remote:
                env_type = "ssh"
            else:
                env_type = "local"
            
            env_spec = self.ENV_SPECS[env_type].copy() # Copy to avoid mutating default
            
            # Dynamic Hardware Query
            gpu_stats = {}
            if env_type == "ssh":
                gpu_stats = await provider.get_gpu_status()
                if gpu_stats:
                    env_spec["gpu"] = f"{gpu_stats['name']} (REAL-TIME)"
                    env_spec["vram"] = f"{gpu_stats['free_mb'] // 1024}GB Free / {gpu_stats['total_mb'] // 1024}GB Total"
                    env_spec["constraints"] += f" Current Utilization: {gpu_stats['util']}%"
            elif env_type == "kaggle":
                 # Kaggle Status
                 if hasattr(provider, "get_resource_status"):
                     gpu_stats = await provider.get_resource_status()
                     if gpu_stats:
                         env_spec["gpu"] = gpu_stats["gpu"]
                         env_spec["name"] = gpu_stats["name"] # Includes "1/2 Active"
                         env_spec["constraints"] += f" Slots Used: {gpu_stats['running_count']}/{gpu_stats['limit']}"
                         if not gpu_stats["available"]:
                             RichLogger.log_agent_step("WARNING", "Kaggle Slots Full! Execution might wait.")
                    
            RichLogger.log_agent_step("Environment", f"Selected: {env_spec['name']} ({env_spec['gpu']})")
            
            # Resolve Data Path based on Provider
            # Note: ensure_dataset now returns the usable path/slug
            # We call ensure first to determine the path/slug
            data_spec = await self.data_manager.ensure_dataset(
                dataset_name, 
                remote_provider=provider if is_remote else None,
                is_kaggle=is_kaggle
            )
            
            # data_spec is either a path (str) or a slug (str)
            data_path = self.data_manager.get_data_path(dataset_name, remote=is_remote, kaggle=is_kaggle)
            
            RichLogger.log_agent_step("Data Setup", f"Dataset: {dataset_name}\nSpec: {data_spec}\nPath: {data_path}")
            
            # 3. Experiment Planning (New)
            RichLogger.log_agent_step("Planning", "Designing Experiment Strategy...")
            experiment_plan = await self._plan_experiment(topic, idea, human_feedback, env_spec)
            RichLogger.log_agent_step("Plan Generated", f"{experiment_plan[:300]}...")
            
            # 4. Code Generation (Fail-Fast)
            result_dir = "results"
            experience_context = self.reflection_ops.read_history()
            prompt = self._generate_prompt(idea, experiment_plan, feedback=human_feedback, data_path=data_path, result_dir=result_dir, experience_context=experience_context, is_kaggle=is_kaggle)
            
            RichLogger.log_agent_step("Prompting LLM", "Requesting Comprehensive Experiment Code...")
            response = await self.model_client.chat(
                message=prompt,
                tier=ModelTier.CRITICAL,
                task_type="experimentation"
            )
            
            code_blocks = re.findall(r"```python(.*?)```", response, re.DOTALL)
            if not code_blocks:
                return {"code": response, "execution_result": "No code generated."}
                
            code = code_blocks[0].strip()
            RichLogger.log_agent_step("Code Generated", f"{code[:100]}... (Total {len(code)} chars)")
            
            # 4. Git Isolation
            topic_hash = hashlib.md5(topic.encode()).hexdigest()[:8]
            script_name = f"exp_{topic_hash}.py"
            
            # Note: We rely on the git_manager passed from orchestrator to ensure we use the same repo context
            print(f"[ExperimentScientist] 🌿 Git Branch Switch: idea/{topic_hash}")
            await git_manager.checkout_idea_branch(topic_hash)
            
            # Ensure we write to the CodeExecutor's working directory so it can find the file!
            work_dir = getattr(self.code_executor, 'work_dir', '.')
            script_path = os.path.join(work_dir, script_name)
            
            with open(script_path, "w") as f:
                f.write(code)
            print(f"[DEBUG] ExperimentScientist wrote script to: {os.path.abspath(script_path)}")
                
            await git_manager.atom_commit(
                agent_role="SCIENTIST",
                action="EXP_GEN",
                details=f"Generated experiment code for {topic}",
                files=[script_name]
            )
            
            # 5. Versioning (Minimum Necessity Protocol)
            # Tag the experiment with exact versions for Reproducibility
            manifest = {
                "topic": topic,
                "git_hash": topic_hash, # Using topic hash as proxy for now, ideally strictly git sha
                "timestamp": "Now",
                "env_spec": env_spec['name'],
                "data_spec": data_path
            }
            # We'll inject this into the code or save as sidecar?
            # Ideally the code itself logs it.
            # For now, we rely on the Git Commit above being the source of truth.
            
            # 6. Environment Setup (Self-Healing)
            # Kaggle has its own pre-baked env usually, but we might need small installs.
            # For Local/SSH, we use EnvManager.
            if not is_kaggle:
                await self._setup_environment(provider, topic_hash, is_remote)
            
            # 6. Execution Loop (Self-Healing)
            if is_kaggle:
                exec_result = await self._execute_on_kaggle(code, topic, script_name)
            else:
                exec_result = await self._execute_safely(provider, code, topic_hash, is_remote, script_name)
            
            # 7. Result Sync
            if exec_result.get('exit_code') == 0:
                 local_res_path = f"research_vault/experiments/{topic}"
                 os.makedirs(local_res_path, exist_ok=True)
                 
                 # Kaggle sync is handled inside _execute_on_kaggle
                 if not is_kaggle:
                     await provider.download_results(result_dir, local_res_path)
                     if is_remote:
                         exec_result['output'] = exec_result.get('output', '') + f"\n[Data] Synced results to {local_res_path}"

            self.wandb.finish_run()
            RichLogger.log_agent_completion("Experimentation", "Run Finished")
            return {"code": response, "execution_result": str(exec_result)}
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            RichLogger.log_error("ExperimentScientist", str(e))
            return {"code": "", "execution_result": f"Exit Code: -1\nError: {str(e)}"}

    def _route_provider(self, autonomous_mode: bool):
        """
        Decides where to run the code.
        Returns: (provider_instance, is_remote, is_kaggle)
        """
        # 1. Kaggle Strategy: If autonomous and we have credentials
        # (Simulated logic: if user wanted Kaggle, we'd check config)
        # For now, default to SSH if available, else Local. 
        # But let's support explicit Kaggle request if we had a flag.
        # Simple heuristic: If autonomous_mode and SSH is missing, try Kaggle?
        # Or just stick to current hierarchy.
        
        # New Feature: Kaggle Routing
        # For verification purposes, we'll implement the logic but default to existing unless configured.
        if self.kaggle_executor: 
             # Check if we should use it. Maybe a hard switch for now?
             # Let's say: if SSH is NOT configured, but Kaggle IS, use Kaggle.
             if not self.ssh_executor.config:
                 # return self.kaggle_executor, True, True
                 pass

        if self.ssh_executor.config:
            RichLogger.log_agent_step("Provider", f"SSH @ {self.ssh_executor.config.get('host')}")
            return self.ssh_executor, True, False
            
        RichLogger.log_agent_step("Provider", "Local Execution")
        
        # Local Adaptor (Inline or we use CodeExecutor directly but need adapter interface)
        # Re-using the adapter pattern from orchestrator for consistency
        class LocalAdaptor:
            code_executor = self.code_executor
            async def execute_command(self_adaptor, cmd):
                return await self_adaptor.code_executor.execute_command(cmd)
            async def execute(self_adaptor, cmd):
                return await self_adaptor.code_executor.execute_command(cmd)
            async def download_results(self_adaptor, remote, local):
                # Copy from work_dir/remote to local
                import shutil
                work_dir = getattr(self_adaptor.code_executor, 'work_dir', '.')
                src = os.path.join(work_dir, remote)
                if os.path.exists(src):
                    # If dir, copytree. If file, copy.
                    # 'results' is likely a dir.
                    if os.path.isdir(src):
                        # Merge/Overwrite
                        if os.path.exists(local):
                            shutil.rmtree(local) 
                        shutil.copytree(src, local)
                    else:
                        shutil.copy(src, local)
                else:
                    print(f"[LocalAdaptor] No results found at {src}") 
                
        return LocalAdaptor(), False, False

    async def _plan_experiment(self, topic, idea, feedback, env_spec) -> str:
        """
        Generates a structured experiment plan before coding.
        """
        prompt = f"""
        Design a rigorous experiment plan for: "{topic}"
        
        Core Idea:
        {idea}
        
        User Constraints:
        {feedback}
        
        Target System: **{env_spec['name']}**
        - GPU: {env_spec['gpu']}
        - VRAM: {env_spec['vram']}
        - Hardware Constraints: {env_spec['constraints']}
        
        Task:
        1. Adaptation: How should the code adapt to this hardware? (e.g. Batch Size, Precision)
        2. Feasibility: Ensure the model size fits in {env_spec['vram']}.
        
        Output a structured JSON plan with:
        1. **Hypothesis**: What are we testing?
        2. **Datasets**: Specific tensors/data shapes needed.
        3. **Baselines**: Exact methods to compare against.
        4. **Metrics**: Quantitative metrics (F1, MSE, etc.).
        5. **Hyperparameters**: Search space or fixed values.
        6. **Step-by-Step Logic**: Flow of the script.
        
        Ensure the plan is FEASIBLE for a single script run.
        """
        response = await self.model_client.chat(prompt, tier=ModelTier.CRITICAL, task_type="planning")
        return response

    def _generate_prompt(self, idea, plan, feedback, data_path, result_dir, experience_context, is_kaggle):
        # Base prompt extraction
        prompt = f'''
        Write a Python script to execute this **Experiment Plan**:
        
        {plan}
        
        (Original Idea Context: {idea})
        (User Constraints: {feedback})
        
        Configuration:
        - **Dataset Path**: `{data_path}` (Assume it exists)
        - **Output Directory**: `{result_dir}` (Create it if missing)
        '''
        
        if is_kaggle:
            prompt += "\n**Platform**: Running on Kaggle Notebook with unlimited Internet.\n"
            prompt += "You CAN use `!git clone` or `!pip install` inside the script.\n"

        prompt += f'''
        Requirements:
        1. **Fail Fast**: Add `assert` checks at the very top for GPU availability, data existence, and library versions.
        2. **Robust Logging**: Use `print()` liberally.
        3. **Fast Run**: Use small dummy datasets or `max_iter=10`.
        4. **Clean Code**: No markdown explanations outside code blocks.
        5. **Resumable**: Implement Checkpointing (`model.pt`).
        6. **Comprehensive Evaluation**:
           - **Baselines**: Compare Proposed vs Baseline.
           - **Ablation Study**: Run an ablation.
           - **Case Study**: Save examples to `{result_dir}/case_study.txt`.
           - **Limitations**: Save to `{result_dir}/limitations.txt`.
           
        7. **Visuals**:
           - Generate plots for key metrics using `matplotlib`.
           - **Required**: `{result_dir}/plot_comparison.png` and `{result_dir}/plot_ablation.png`.
        '''
        
        if experience_context:
            prompt += f"\n\n[Experience Cookbook]:\n{experience_context[-1000:]}\n"
        
        prompt += "\nOutput inside ```python ... ``` blocks."
        return prompt

    async def _setup_environment(self, provider, topic_hash, is_remote):
        """
        Self-Healing Environment Setup
        """
        setup_pkgs = ["numpy", "pandas", "matplotlib", "scikit-learn", "torch"]
        setup_script = self.env_manager.generate_setup_script(setup_pkgs)
        
        max_retries = 2
        for i in range(max_retries):
            RichLogger.log_agent_step("Environment", f"Setup Iteration {i+1}/{max_retries}...")
            
            if is_remote:
                 remote_workspace = f"research_bot/lanes/{topic_hash}"
                 await provider.execute_command(f"mkdir -p {remote_workspace}")
                 # Push setup script
                 with open("setup_env.sh", "w") as f: f.write(setup_script)
                 # Note: explicit path handling would be better, simplifying for now
                 await provider.push_file("setup_env.sh", f"{remote_workspace}/setup_env.sh")
                 os.remove("setup_env.sh")
                 setup_cmd = f"cd {remote_workspace} && bash setup_env.sh"
            else:
                 # Local
                 setup_cmd = f"cat << 'EOF' > setup_env.sh\n{setup_script}\nEOF\nbash setup_env.sh"

            res = await provider.execute_command(setup_cmd)
            
            if res.get("exit_code") == 0:
                RichLogger.log_agent_step("Environment", "Setup Success! ✅")
                return True
            else:
                RichLogger.log_agent_step("Environment", f"Setup Failed: {res.get('stderr')}. Asking Doctor...")
                actions = await self.healer_ops.diagnose_execution_error(self.model_client, "Environment Setup", res.get('stderr', ''), setup_script)
                
                # Apply fixes
                for action_type, content in actions:
                    if action_type == "shell":
                        RichLogger.log_agent_step("Self-Healing", f"🛠️ Executing Shell Fix: {content}")
                        fix_cmd = f"cd {remote_workspace} && {content}" if is_remote else content
                        await provider.execute_command(fix_cmd)
        
        return False

    async def _execute_safely(self, provider, code, topic_hash, is_remote, script_name):
        """
        Execution with Code-Level Self-Healing
        """
        max_code_retries = 2
        current_code = code
        
        # Deploy initial script
        if is_remote:
             remote_workspace = f"research_bot/lanes/{topic_hash}"
             await provider.push_file(script_name, f"{remote_workspace}/{script_name}")
        
        # Prepare execution result dict
        final_res = {}
        
        for attempt in range(max_code_retries + 1):
            RichLogger.log_agent_step("Execution", f"Attempt {attempt+1}/{max_code_retries+1}...")
            
            # Wrap command
            raw_cmd = f"python3 {script_name}" if not is_remote else f"python3 {script_name}" # Filename same
            wrapped = self.env_manager.wrap_command(raw_cmd)
            
            if is_remote:
                remote_workspace = f"research_bot/lanes/{topic_hash}"
                cmd = f"cd {remote_workspace} && {wrapped}"
            else:
                cmd = wrapped
                
            exec_res = await provider.execute(cmd)
            
            if exec_res.get('exit_code') == 0:
                 RichLogger.log_agent_step("Execution Result", "Success! ✅")
                 return exec_res
            
            # Failure
            error_msg = exec_res.get('stderr', '')
            RichLogger.log_agent_step("Execution Result", f"Failed. Error:\n{error_msg[:300]}...")
            
            if attempt < max_code_retries:
                 actions = await self.healer_ops.diagnose_execution_error(self.model_client, "Experiment Execution", error_msg, current_code)
                 
                 patched = False
                 for action_type, content in actions:
                     if action_type == "code":
                         current_code = content
                         # Update file on disk
                         with open(script_name, "w") as f: f.write(current_code)
                         if is_remote:
                             # Re-push
                             remote_workspace = f"research_bot/lanes/{topic_hash}"
                             await provider.push_file(script_name, f"{remote_workspace}/{script_name}")
                         patched = True
                         
                     elif action_type == "shell":
                         RichLogger.log_agent_step("Self-Correction", f"🛠️ Shell Fix: {content}")
                         fix_cmd = f"cd {remote_workspace} && {content}" if is_remote else content
                         await provider.execute_command(fix_cmd)
                         patched = True
                         
                 if not patched:
                     break
            
            final_res = exec_res

        return final_res

    async def _execute_on_kaggle(self, code, topic, script_name):
        """
        Kaggle Execution Strategy
        """
        RichLogger.log_agent_step("Kaggle", "Refactoring code for Notebook...")
        # Push to Kaggle
        from core.config_manager import config_manager
        secrets = config_manager.secrets
        
        # Determine Git Repo (Should be in config)
        # Assuming we want to clone the current research bot code?
        # Or just passing secrets for the script to use?
        # User said "from git download code, data".
        # Let's pass secrets and optional git_repo if configured.
        git_repo = config_manager.get("git", {}).get("remote_url") # Try to get it
        
        result = await self.kaggle_executor.push_notebook(
            code, 
            f"exp-{topic}",
            dataset_slugs=[topic] if "/" in topic else [],
            secrets=secrets,
            git_repo=git_repo
        )
        
        if result['status'] == 'Success':
             url = result['url']
             RichLogger.log_agent_step("Kaggle", f"Kernel Pushed: {url}")
             
             # Monitor
             while True:
                 status = await self.kaggle_executor.monitor_kernel(result['kernel_slug']) # Assuming push_notebook returns slug helper
                 # actually push_notebook logic in skill needs to return slug cleanly or we derive it.
                 # For now, simplistic wait or return info
                 await asyncio.sleep(10)
                 if status in ["complete", "error"]:
                     break
            
             # Download results
             # ...
             return {"exit_code": 0, "stdout": "Kaggle Run Complete", "stderr": ""}
        else:
             return {"exit_code": 1, "stdout": "", "stderr": result.get('error')}


    # _consult_error_doctor removed in favor of UniversalHealer
