from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

@dataclass
class MaceConfig:
    # Model Architecture
    r_max: float = 6.0         # Cutoff radius
    num_interactions: int = 2  # Number of MP layers
    hidden_irreps: str = "128x0e + 32x1o" # Feature representation
    
    # Charge Consistency (CSC)
    use_charge: bool = True    # Enable QEq/Charge prediction
    charge_weight: float = 1.0 # Weight for charge loss
    
    # Training
    batch_size: int = 32
    max_epochs: int = 100
    lr: float = 1e-3
    energy_weight: float = 100.0
    forces_weight: float = 1000.0

@dataclass
class DataConfig:
    # Dataset
    data_path: Path = Path("data/energetic_cocrystals.xyz")
    train_ratio: float = 0.8
    val_ratio: float = 0.1
    
    # Atoms
    atomic_numbers: List[int] = field(default_factory=lambda: [1, 6, 7, 8]) # H, C, N, O

@dataclass
class CSCMaceproject:
    project_name: str = "CSC-MACE-Energetic"
    seed: int = 42
    device: str = "cuda"
    mace: MaceConfig = field(default_factory=MaceConfig)
    data: DataConfig = field(default_factory=DataConfig)
