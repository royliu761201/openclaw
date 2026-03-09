import os
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, Optional

class ModelTier(Enum):
    CRITICAL = "tier_1"   # High Intelligence (Reasoning, Drafting)
    STANDARD = "tier_2"   # Balanced (Reviewing, Coding)
    ECONOMY = "tier_3"    # Cost Optimized (Status, Formatting)

@dataclass
class ModelConfig:
    provider: str
    id: str
    fallback: Optional[str] = None
    max_tokens: int = 8192

# User-Approved 3-Tier Strategy (Optimized Routing)
# User-Restricted Model Pool
MODEL_POOL: Dict[ModelTier, ModelConfig] = {
    ModelTier.CRITICAL: ModelConfig(
        provider="google",
        id="gemini-3-flash-preview", 
        fallback="gemini-2.5-flash-lite",
        max_tokens=1000000
    ),
    ModelTier.STANDARD: ModelConfig(
        provider="google",
        id="gemini-2.5-flash-lite", 
        fallback="gemini-1.5-flash",
        max_tokens=1000000 
    ),
    ModelTier.ECONOMY: ModelConfig(
        provider="google",
        id="gemini-1.5-flash", 
        fallback="gemini-1.5-flash",
        max_tokens=8192
    )
}


def get_model_config(tier: ModelTier) -> ModelConfig:
    return MODEL_POOL.get(tier, MODEL_POOL[ModelTier.STANDARD])

# Workspace Configuration
PAPER_WORKSPACE_DIR = os.getenv("PAPER_WORKSPACE_DIR", "papers")
