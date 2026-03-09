from typing import Any, Dict, Optional
import random

class AccelerationEngine:
    """
    Implements the "Fail Fast, Move Fast" logic.
    1. Visual Early Stopping (Simulated for now, pending Vision API access)
    2. Fast Branching (Prototype generation)
    """

    def __init__(self, model_client: Any = None):
        self.model_client = model_client

    async def check_early_stop(self, metrics: Dict[str, float], epoch: int, max_epochs: int, curve_image_path: Optional[str] = None) -> bool:
        """
        Decides whether to kill the experiment based on metrics and visual curve analysis.
        Returns: True (STOP) or False (CONTINUE)
        """
        # 1. Heuristic Check (The "Plain" Stop)
        loss = metrics.get('loss')
        if loss is not None:
             if loss > 1000: # Exploding gradient
                 print(f"[AccelerationEngine] Early Stop: Loss explosion ({loss})")
                 return True
             # Check for flatline (simplified)
             # In real impl, we'd check a history buffer
        
        # 2. Visual Check (The "Gemini" Stop)
        if curve_image_path:
            print(f"[AccelerationEngine] 👁️ Analyzing visual curve at {curve_image_path}...")
            
            prompt = """
            Analyze this training loss curve.
            1. Is it converging?
            2. Is it oscillating wildly?
            3. Compared to a standard successful Log-Linear descent, does this look like a failure?
            
            If the success probability is < 10%, return STOP. Otherwise CONTINUE.
            """
            
            # Simulated Vision Call
            # decision = await self.model_client.analyze_vision(curve_image_path, prompt)
            
            # Mocking the visual decision
            import random
            if random.random() < 0.05:
                print(f"[AccelerationEngine] Visual Analysis verdict: STOP (Low convergence probability).")
                return True
            else:
                print(f"[AccelerationEngine] Visual Analysis verdict: CONTINUE.")

        return False

    def prototype_first(self, full_task_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Derives a T2 Proxy Task (Fast Prototype) from a Full Task.
        Scales down epochs and dataset size.
        """
        prototype = full_task_config.copy()
        
        # Scale down
        prototype['epochs'] = max(1, int(full_task_config.get('epochs', 10) * 0.1))
        prototype['batch_size'] = 8 # Small batch for safety
        prototype['dataset_mode'] = 'proxy' # Logic to handle this in data loader
        prototype['use_proxy_data'] = True
        prototype['task_id'] = f"{full_task_config.get('task_id', 'task')}_proxy"
        
        print(f"[AccelerationEngine] Generated Prototype Task: {prototype['task_id']}")
        return prototype

    def generate_branches(self, base_config: Dict[str, Any], strategies: list) -> list:
        """
        Generates parallel branches for hyperparameter search.
        strategies: [{'lr': 1e-3}, {'lr': 1e-4}]
        """
        branches = []
        for i, strat in enumerate(strategies):
            branch = base_config.copy()
            branch.update(strat)
            branch['task_id'] = f"{base_config.get('task_id')}_branch_{i}"
            branches.append(branch)
        return branches
