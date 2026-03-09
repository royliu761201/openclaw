from typing import Dict, Any, Optional
import importlib.util
from .base_skill import BaseSkill

class WandBObserver(BaseSkill):
    """
    Observability Center using Weights & Biases.
    Mocked for environments without API keys, but ready for integration.
    """
    def __init__(self, project_name: str = "ResearchBot_Auto", active: bool = True, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.project_name = project_name
        self.active = active
        self.run = None

    def verify(self) -> bool:
        """Checks if wandb library is installed."""
        return importlib.util.find_spec("wandb") is not None
        
    def init_run(self, run_name: str, config: Dict[str, Any]):
        """
        Initializes a WandB run.
        """
        if not self.active: return
        
        print(f"[WandB] Initializing run: {run_name}")
        # import wandb
        # self.run = wandb.init(project=self.project_name, name=run_name, config=config, reinit=True)
        # Mock for now to avoid dependency crash if not installed
        self.run = "MockRun"

    def log_metrics(self, metrics: Dict[str, float]):
        """
        Logs a dictionary of metrics.
        """
        if not self.active or not self.run: return
        
        print(f"[WandB] 📈 Logging: {metrics}")
        # wandb.log(metrics)

    def finish_run(self):
        """
        Closes the run.
        """
        if not self.active: return
        print("[WandB] Finishing run.")
        # if self.run: self.run.finish()
