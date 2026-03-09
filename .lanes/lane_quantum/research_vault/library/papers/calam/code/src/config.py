
import os
from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class CaLaMConfig:
    """
    CaLaM Global Configuration
    """
    # Model defaults
    base_model: str = "Qwen/Qwen2.5-14B-Instruct"
    max_new_tokens: int = 30
    
    # Steering
    steering_keywords: list = field(default_factory=lambda: [
        "hate", "stupid", "idiot", "kill", "ugly", 
        "shut", "fuck", "damn", "suck", "crap"
    ])
    
    risk_keywords: list = field(default_factory=lambda: [
        "stupid", "idiot", "kill", "hate", "ugly"
    ])
    
    # Tracking
    use_wandb: bool = True
    wandb_project: str = field(default_factory=lambda: os.getenv("WANDB_PROJECT", "calam"))

# ==========================================
# Experiment Matrix Registry
# ==========================================
EXPERIMENT_MATRIX = {
    # --- Vanilla Baselines ---
    "vanilla_rtp": {
        "method": "vanilla",
        "dataset": "rtp",
        "limit": 100,
        "desc": "Vanilla Baseline (RTP)",
    },
    "vanilla_mmlu": {
        "method": "vanilla",
        "dataset": "mmlu",
        "limit": 100,
        "desc": "Vanilla Baseline (MMLU)",
    },
    "vanilla_tqa": {
        "method": "vanilla",
        "dataset": "tqa",
        "limit": 100,
        "desc": "Vanilla Baseline (TruthfulQA)",
    },

    # --- Static Steering ---
    "static_rtp_alpha5": {
        "method": "static",
        "dataset": "rtp",
        "alpha": 5.0,
        "limit": 100,
        "desc": "Static Steering Alpha=5.0 (RTP)",
    },

    # --- CaLaM Dynamic Steering ---
    "calam_rtp_alpha2": {
        "method": "calam",
        "dataset": "rtp",
        "alpha": 2.0,
        "limit": 100,
        "desc": "CaLaM Alpha=2.0 (RTP)",
    },
    "calam_rtp_alpha5": {
        "method": "calam",
        "dataset": "rtp",
        "alpha": 5.0,
        "limit": 100,
        "desc": "CaLaM Alpha=5.0 (RTP)",
    },
    "calam_rtp_alpha10": {
        "method": "calam",
        "dataset": "rtp",
        "alpha": 10.0,
        "limit": 100,
        "desc": "CaLaM Alpha=10.0 (RTP)",
    },
    "calam_mmlu_alpha5": {
        "method": "calam",
        "dataset": "mmlu",
        "alpha": 5.0,
        "limit": 100,
        "desc": "CaLaM Alpha=5.0 (MMLU)",
    },
}
