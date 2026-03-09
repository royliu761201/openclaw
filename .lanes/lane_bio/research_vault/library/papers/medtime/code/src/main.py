import os
# Force WandB Project Name (Override any defaults) before ANY other imports
os.environ["WANDB_PROJECT"] = "medtime"
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

import argparse
import logging
from .config import EXPERIMENT_MATRIX, GlobalConfig
from .data import prepare_atomic_datasets
from .baselines import run_ie_span_experiment, run_rule_based_experiment

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)
import pandas as pd
import json

def _save_artifacts(run_name, summaries, preds_map):
    # Ensure dir
    out_dir = os.path.join(GlobalConfig.PROD_DIR, "medtime_results")
    os.makedirs(out_dir, exist_ok=True)
    
    # Save Report
    if summaries:
        df = pd.DataFrame(summaries)
        csv_path = os.path.join(out_dir, f"report_{run_name}.csv")
        df.to_csv(csv_path, index=False)
        logger.info(f"📝 Saved Report: {csv_path}")
        try:
            print(df.to_string())
        except:
            pass

    # Save Preds
    if preds_map:
        # Wrap in run_name structure
        final_preds = {run_name: preds_map}
        json_path = os.path.join(out_dir, f"preds_{run_name}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(final_preds, f, ensure_ascii=False, indent=2)
        logger.info(f"💾 Saved Predictions: {json_path}")



def main():
    parser = argparse.ArgumentParser(description="MedTime Experiment Runner")
    parser.add_argument("--task", type=str, required=True, help="Experiment Task ID (from config.py)")
    parser.add_argument("--inference", action="store_true", help="Force Inference Only Mode")
    parser.add_argument("--checkpoint", type=str, default=None, help="Path to checkpoint for inference/resume")
    parser.add_argument("--model", type=str, default=None, help="Override base model path/name")
    parser.add_argument("--smoke", action="store_true", help="Run quick smoke test (N=2)")
    args = parser.parse_args()

    # 1. Validate Task
    if args.task not in EXPERIMENT_MATRIX:
        logger.error(f"❌ Task '{args.task}' not found in EXPERIMENT_MATRIX.")
        logger.info(f"Available Tasks: {list(EXPERIMENT_MATRIX.keys())}")
        raise ValueError(f"Task {args.task} not found.")

    cfg = EXPERIMENT_MATRIX[args.task].copy() # Copy to avoid mutation
    
    # [CLI OVERRIDES]
    if args.inference:
        logger.info("🔧 CLI Override: Inference Only Mode = True")
        cfg["inference_only"] = True
        cfg["max_steps"] = 0 # Disable training steps just in case
        
    if args.checkpoint:
        logger.info(f"🔧 CLI Override: Checkpoint Path = {args.checkpoint}")
        cfg["checkpoint_path"] = args.checkpoint
        # Also set resume_from_checkpoint just in case logic uses it
        cfg["resume_from_checkpoint"] = args.checkpoint

    if args.model:
        logger.info(f"🔧 CLI Override: Base Model = {args.model}")
        cfg["base_model"] = args.model

    # [OPTIMIZATION] Flight Manifest
    inference_mode = cfg.get("inference_only", False)
    if args.smoke:
        cfg["smoke_test"] = True
    is_smoke = cfg.get("smoke_test", GlobalConfig.TRAIN_PARAMS["smoke_test"])
    
    print("\n" + "="*60)
    print(f"✈️  MEDTIME FLIGHT MANIFEST: {args.task}")
    print("="*60)
    print(f"🔹 Task Family:   {cfg.get('family')}")
    print(f"🔹 Operation:     {'🔮 INFERENCE ONLY' if inference_mode else '🏋️ TRAINING + INFERENCE'}")
    print(f"🔹 Data Scale:    {'🔥 SMOKE TEST (N=2)' if is_smoke else '🌍 FULL SCALE'}")
    if is_smoke:
        print("    ⚠️  WARNING: SMOKE TEST IS ACTIVE. RESULTS WILL BE INVALID. ⚠️")
    print(f"🔹 Base Model:    {cfg.get('base_model', 'Default')}")
    print(f"🔹 Checkpoint:    {args.checkpoint if args.checkpoint else ('None (Training)' if not inference_mode else '❌ CRITICAL: MISSING')}")
    print("-" * 60)
    print(f"🔹 Env Config:    WANDB={os.getenv('WANDB_MODE', 'Unknown')} | PROJECT={os.getenv('WANDB_PROJECT', 'medtime')}")
    print("="*60 + "\n")

    logger.info(f"🚀 Initializing Task: {args.task}")

    # 2. Load Data
    logger.info("📚 Preparing Data Bundle...")
    data_bundle = prepare_atomic_datasets()

    # 3. Dispatch Execution
    import time
    timestamp = time.strftime("%m%d_%H%M")
    unique_run_name = f"{args.task}_{timestamp}"
    if is_smoke:
        unique_run_name += "_smoke"
    
    family = cfg.get("family", "unknown")

    if family == "ie_span":
        logger.info(f"🎯 Dispatching to [IE Span] Runner: {unique_run_name}")
        summaries, preds_map = run_ie_span_experiment(unique_run_name, cfg, data_bundle)
        _save_artifacts(unique_run_name, summaries, preds_map)
    
    elif family == "rule_based":
        logger.info(f"🎯 Dispatching to [Rule Based] Runner: {unique_run_name}")
        summaries, preds_map = run_rule_based_experiment(unique_run_name, cfg, data_bundle)
        _save_artifacts(unique_run_name, summaries, preds_map)
        
    elif family == "llm_sft" or family == "medtime_gvp" or family == "llm_medtime":
        logger.info(f"🎯 Dispatching to [MedTime GVP/LLM] Runner: {unique_run_name}")
        from .model import run_llm_experiment
        summaries, preds_map = run_llm_experiment(unique_run_name, cfg, data_bundle)
        _save_artifacts(unique_run_name, summaries, preds_map)


        
        _save_artifacts(unique_run_name, summaries, preds_map)
            
    else:
        logger.error(f"❌ Unknown Experiment Family: {family}")
        raise ValueError(f"Unknown family: {family}")

    logger.info(f"✅ Task {args.task} (Run: {unique_run_name}) Completed Successfully.")

if __name__ == "__main__":
    main()
