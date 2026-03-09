from enum import Enum
from pydantic import Field
from .base import PersistableModel

class validationLevel(str, Enum):
    T1_SMOKE = "smoke"   # 1 batch, check flow
    T2_PROXY = "proxy"   # small dataset, check convergence
    T3_FULL  = "full"    # full run

class ExperimentConfig(PersistableModel):
    """
    Configuration for a single experiment run.
    """
    idea_id: str
    task_id: str
    cmd: str
    env_name: str
    output_dir: str
    resume: bool = True
    validation_level: validationLevel = validationLevel.T3_FULL
