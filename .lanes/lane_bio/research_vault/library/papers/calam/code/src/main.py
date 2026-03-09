
import argparse
import os
import json
import torch
import numpy as np
from transformers import AutoTokenizer, AutoModelForCausalLM
import logging
import sys

from .config import EXPERIMENT_MATRIX, CaLaMConfig
import wandb
from .data import RealToxicityPrompts, TruthfulQA, MMLUDataset
from .evaluator import evaluate_model

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="CaLaM Experiment Runner")
    parser.add_argument("--task", type=str, required=True, help="Task ID from EXPERIMENT_MATRIX")
    parser.add_argument("--model", type=str, default=None, help="Override base model")
    args = parser.parse_args()

    # 1. Validate Task
    if args.task not in EXPERIMENT_MATRIX:
        logger.error(f"❌ Task '{args.task}' not found in EXPERIMENT_MATRIX.")
        logger.info(f"Available Tasks: {list(EXPERIMENT_MATRIX.keys())}")
        raise ValueError(f"Task {args.task} not found.")

    exp_cfg = EXPERIMENT_MATRIX[args.task].copy()
    
    # Overrides
    if args.model:
        exp_cfg["base_model"] = args.model
    else:
        exp_cfg["base_model"] = CaLaMConfig.base_model # Default from global config

    logger.info(f"🚀 Initializing Task: {args.task}")
    logger.info(f"   Desc: {exp_cfg['desc']}")
    logger.info(f"   Model: {exp_cfg['base_model']}")

    # 2. Load Model
    logger.info("Loading Model & Tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(exp_cfg["base_model"], trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        
    model = AutoModelForCausalLM.from_pretrained(
        exp_cfg["base_model"], 
        device_map="auto", 
        trust_remote_code=True,
        torch_dtype=torch.float16
    )

    # 3. Load Dataset
    dataset_name = exp_cfg.get("dataset", "rtp")
    limit = exp_cfg.get("limit", 50)
    logger.info(f"Loading Dataset: {dataset_name} (Limit={limit})...")
    
    if dataset_name == 'rtp':
        dataset = RealToxicityPrompts(limit=limit)
    elif dataset_name == 'tqa':
        dataset = TruthfulQA(limit=limit)
    elif dataset_name == 'mmlu':
        dataset = MMLUDataset(limit=limit)
    else:
        raise ValueError(f"Unknown dataset: {dataset_name}")

    # 4. Resume Logic & WandB
    out_dir = "calam_results"
    os.makedirs(out_dir, exist_ok=True)
    output_file = os.path.join(out_dir, f"{args.task}.json")
    
    existing_results = []
    if os.path.exists(output_file):
        try:
            with open(output_file, 'r') as f:
                existing_results = json.load(f)
            logger.info(f"🔄 Resuming from {len(existing_results)} existing results in {output_file}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to load existing results (starting fresh): {e}")

    # WandB Init
    global_cfg = CaLaMConfig()
    run_name = args.task # Define run_name for wandb
    if global_cfg.use_wandb:
        try:
            from src.common.wandb_utils import strict_wandb_init
            strict_wandb_init(
                project=global_cfg.wandb_project,
                name=run_name,
                config=global_cfg.__dict__,
                mode="online"
            )
        except ImportError:
            # Fallback if running standalone without src path setup? 
            # Should not happen in deployed enc
            import wandb
            wandb.init(project=global_cfg.wandb_project, name=run_name, config=global_cfg.to_dict())
        except Exception as e:
            logger.error(f"❌ CRITICAL: WandB Init Failed: {e}")
            sys.exit(1) # Strict Exit

    # 5. Run Evaluation
    logger.info("Starting Evaluation...")
    results = evaluate_model(model, tokenizer, dataset, exp_cfg, existing_results=existing_results, output_file=output_file)

    # 5. Save Results
    logger.info(f"✅ Completed. Total results: {len(results)}")
    
    # Simple Stats
    if results:
        avg_tox = np.mean([r.get('toxicity', 0) for r in results])
        print(f"Average Toxicity: {avg_tox:.4f}")
        if dataset_name == 'mmlu':
            acc = np.mean([r.get('correct', 0) for r in results])
            print(f"MMLU Accuracy: {acc:.4f}")

if __name__ == "__main__":
    main()
