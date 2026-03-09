

import argparse
import logging
import os
import time
import json
import pandas as pd
from typing import List, Dict, Any

# [CRITICAL] Disable all Unsloth/HF telemetry to prevent timeouts in restricted environments
os.environ["UNSLOTH_USE_MODELSCOPE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["WANDB_SILENT"] = "true"

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from common.env import ProjectEnv, load_secret
from common.env import ProjectEnv, load_secret
from medtime.config import GlobalConfig, EXPERIMENT_MATRIX, CONFIG, ENV
from medtime.data import prepare_atomic_datasets
from medtime.data import prepare_atomic_datasets
from medtime.evaluator import flush_memory
from medtime.baselines import run_rule_based_experiment, run_ie_span_experiment
from medtime.baselines import run_rule_based_experiment, run_ie_span_experiment
# from medtime.model import run_llm_experiment  <-- Moved to local scope

# Setup Logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("MedTimeTrainer")

def _prepare_balanced_training_data(ATOMIC_DATA, logger):
    """
    Helper to apply augmentation and balancing to training data.
    Separated to keep the main orchestration loop cleaner.
    """
    # Advanced Data Augmentation V2
    def make_it_hard(sample, level=0.7):
        import random
        from medtime.engine import MedTimeEngine
        
        text = str(sample["input"])
        
        # 1. Nonlinear Shuffling (50%)
        if random.random() < 0.5:
            sents = MedTimeEngine.Text.split_sentences(text)
            if len(sents) > 4:
                middle = sents[1:-1]
                random.shuffle(middle)
                shuffled = [sents[0]] + middle + [sents[-1]]
                text = " ".join([s[2] for s in shuffled])
        
        # 3. Cross-Document Injection (20%)
        if random.random() < 0.2:
            cross_doc_phrases = ["【外院病历】诊断为：", "既往史：", "转入我院时记录：", "Previous admission note:"]
            text = random.choice(cross_doc_phrases) + " " + text
        
        # 4. Noise/Distractor Injection (40%)
        if random.random() < 0.4:
            distractors = [
                " 患者无药物过敏史。", " 家族史无特殊。", " 查体：心肺听诊无异常。", 
                " Patient denies smoking or alcohol.", " Vital signs stable."
            ]
            insert_pos = random.randint(0, len(text))
            text = text[:insert_pos] + " " + random.choice(distractors) + " " + text[insert_pos:]
        
        sample["input"] = text
        return sample

    if "syn_train" in ATOMIC_DATA:
        ATOMIC_DATA["syn_train"] = ATOMIC_DATA["syn_train"].map(lambda x: make_it_hard(x, level=0.5))
        logger.info("🔥 Injected Advanced Data Augmentation into Training Data.")

    if "med_few" in ATOMIC_DATA and len(ATOMIC_DATA["med_few"]) > 0:
        from datasets import concatenate_datasets
        syn_size = len(ATOMIC_DATA.get("syn_train", []))
        real_size = len(ATOMIC_DATA["med_few"])
        
        target_real_size = int(syn_size * 0.33)
        multiplier = max(1, target_real_size // real_size)
        
        logger.info(f"🚀 Balancing Real Data: Original={real_size}, Syn={syn_size}, Multiplier={multiplier}x")
        
        expanded_ds = concatenate_datasets([ATOMIC_DATA["med_few"]] * multiplier)
        ATOMIC_DATA["med_few_aug"] = expanded_ds.map(lambda x: make_it_hard(x, level=0.8))
        ATOMIC_DATA["med_few"] = concatenate_datasets([ATOMIC_DATA["med_few"], ATOMIC_DATA["med_few_aug"]])
        logger.info(f"✅ Training Mixture Balanced: New Real Count={len(ATOMIC_DATA['med_few'])}")
    
    return ATOMIC_DATA

def run_all_benchmarks(target_ids: List[str] = None):
    """
    Orchestrate the full experiment matrix.
    """
    # --- 1. Identify Scheduled Experiments ---
    logger.info(f"DEBUG: EXPERIMENT_MATRIX contains {len(EXPERIMENT_MATRIX)} entries.")
    logger.info(f"DEBUG: Keys: {list(EXPERIMENT_MATRIX.keys())}")
    
    GROUP_ALIASES = {
        "rules": [k for k, v in EXPERIMENT_MATRIX.items() if v["family"] == "rule_based"],
        "ie_span": [k for k, v in EXPERIMENT_MATRIX.items() if v["family"] == "ie_span"],
        "zero_shot": [k for k, v in EXPERIMENT_MATRIX.items() if v["family"] == "zero_shot"],
        "core": [k for k, v in EXPERIMENT_MATRIX.items() if v["family"] == "llm_medtime"],
        "sft": [k for k, v in EXPERIMENT_MATRIX.items() if v["family"] == "llm_sft"],
    }
    
    expanded_run_list = []
    if target_ids:
        for tid in target_ids:
            if tid in GROUP_ALIASES: expanded_run_list.extend(GROUP_ALIASES[tid])
            else: expanded_run_list.append(tid)
    else:
        expanded_run_list = list(EXPERIMENT_MATRIX.keys())

    # Check if ANY scheduled experiment requires training
    requires_training = any(
        not EXPERIMENT_MATRIX.get(eid, {}).get("inference_only", False) 
        for eid in expanded_run_list
    )

    # --- 2. Data Preparation ---
    logger.info("🔥 Initializing Atomic Datasets...")
    ATOMIC_DATA = prepare_atomic_datasets()
    
    if requires_training:
        ATOMIC_DATA = _prepare_balanced_training_data(ATOMIC_DATA, logger)
    else:
        logger.info("🔮 Mode: INFERENCE_ONLY. Skipping training data preparation.")

    # --- 3. Execution Loop ---
    all_summary_rows = []
    all_run_predictions = {}
    
    for eid in expanded_run_list:
        if eid not in EXPERIMENT_MATRIX:
            logger.warning(f"⚠️ Experiment ID {eid} not found in matrix. Skipping.")
            continue
            
        cfg = EXPERIMENT_MATRIX[eid]
        logger.info(f"\n{'#'*60}\n# 🚀 START EXPERIMENT: {eid}\n{'#'*60}")
        
        try:
            res_hint = cfg.get("preferred_resource", "gpu")
            model_slug = CONFIG.base_model.split("/")[-1]
            unique_run_name = f"{eid}_{model_slug}"
            
            logger.info(f"📋 Experiment Config: ID={eid}, RunName={unique_run_name}, Target={res_hint.upper()}")
            flush_memory()
            
            # Pass overrides to the run_llm_experiment
            if cfg["family"] in ["llm_sft", "llm_medtime", "zero_shot"]:
                # Inject CLI overrides into the experiment config
                if GlobalConfig.TRAIN_PARAMS.get("max_steps_override") is not None:
                    cfg["max_steps"] = GlobalConfig.TRAIN_PARAMS["max_steps_override"]
                if GlobalConfig.TRAIN_PARAMS.get("inference_only_override") is not None:
                    cfg["inference_only"] = GlobalConfig.TRAIN_PARAMS["inference_only_override"]
                if GlobalConfig.TRAIN_PARAMS.get("resume_training") is not None:
                    cfg["resume_from_checkpoint"] = GlobalConfig.TRAIN_PARAMS["resume_training"]
                if GlobalConfig.TRAIN_PARAMS.get("resume_training") is not None:
                    cfg["resume_from_checkpoint"] = GlobalConfig.TRAIN_PARAMS["resume_training"]
                
                from medtime.model import run_llm_experiment
                summaries, preds = run_llm_experiment(eid, cfg, ATOMIC_DATA)
            elif cfg["family"] == "rule_based":
                summaries, preds = run_rule_based_experiment(eid, cfg, ATOMIC_DATA)
            elif cfg["family"] == "ie_span":
                summaries, preds = run_ie_span_experiment(eid, cfg, ATOMIC_DATA)
            else:
                logger.warning(f"⚠️ Unknown family: {cfg['family']}")
                continue
                
            all_summary_rows.extend(summaries)
            all_run_predictions[eid] = preds
            
        except Exception as e:
            logger.error(f"❌ Experiment {eid} Failed: {e}", exc_info=True)
            sys.exit(1) # Fail Fast to prevent false "Done" status
            
        flush_memory()
        
    # --- Reporting ---
    if all_summary_rows:
        df_final = pd.DataFrame(all_summary_rows)
        # Safe sort: Prefer Temporal_F1, then eval_token_f1, then Trigger_F1
        sort_key = "Temporal_F1" if "Temporal_F1" in df_final.columns else ("eval_token_f1" if "eval_token_f1" in df_final.columns else df_final.columns[0])
        
        if "Temporal_F1" in df_final.columns:
            df_final = df_final.sort_values(by=["test_set", "Temporal_F1"], ascending=[True, False])
        else:
            df_final = df_final.sort_values(by=sort_key, ascending=False)
        csv_path = os.path.join(GlobalConfig.PROD_DIR, f"report_{timestamp}.csv")
        json_path = os.path.join(GlobalConfig.PROD_DIR, f"preds_{timestamp}.json")
        
        df_final.to_csv(csv_path, index=False)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(all_run_predictions, f, ensure_ascii=False, indent=2)
            
        print("\n" + "🏆" * 20 + " EXPERIMENT SUMMARY " + "🏆" * 20)
        print(df_final.to_string())
        logger.info(f"💾 Report saved to: {csv_path}")
    else:
        logger.warning("⚠️ No valid results collected.")

if __name__ == "__main__":
    # Load W&B Key if available
    wb_key = load_secret("WANDB_API_KEY")

    logger.info(f"📋 MedTime Pipeline V13 | Base Model: {CONFIG.base_model} | Seq Len: {CONFIG.max_seq_len}")
    logger.info(f"📊 Training Config: BS={CONFIG.batch_size}, GA={CONFIG.grad_accumulation}, LR={CONFIG.learning_rate}")
    
    if wb_key:
        os.environ["WANDB_API_KEY"] = wb_key
        logger.info("📡 W&B Key detected and loaded into environment.")

    parser = argparse.ArgumentParser(description="MedTime Training Orchestrator")
    parser.add_argument("--smoke_test", action="store_true", help="Run minimal smoke test (fast mode)")
    parser.add_argument("--no_wandb", action="store_true", help="Disable W&B logging")
    parser.add_argument("--model", type=str, help="Override base LLM (e.g. 'unsloth/llama-3-8b')")
    parser.add_argument("--run", "--run_id", type=str, nargs="+", help="Specific experiment IDs to run (e.g. medtime_gvp_cn)")
    parser.add_argument("--max_steps", type=int, help="Override max training steps")
    parser.add_argument("--save_steps", type=int, help="Override checkpoint saving intervals")
    parser.add_argument("--inference_only", action="store_true", help="Force inference only mode")
    parser.add_argument("--batch_size", type=int, help="Override training batch size")
    parser.add_argument("--grad_accum", type=int, help="Override gradient accumulation steps")
    parser.add_argument("--resume", action="store_true", help="Resume training from latest checkpoint")
    parser.add_argument("--data_dir", type=str, help="Override data directory")
    parser.add_argument("--output_dir", type=str, help="Override output directory")
    
    args = parser.parse_args()
    
    # Override Global Config for Smoke Test
    if args.smoke_test:
        logger.info("⚠️ SMOKE TEST ENABLED: Reducing steps and dataset size.")
        GlobalConfig.TRAIN_PARAMS["smoke_test"] = True
        
        # Mac/CPU Compatibility for Smoke Test
        import torch
        if not torch.cuda.is_available():
            from medtime.config import CONFIG
            logger.info("⚠️ No GPU detected. Swapping to 'gpt2' for Smoke Test (avoiding 4-bit quant errors).")
            CONFIG.base_model = "gpt2"
            CONFIG.max_seq_len = 1024 # GPT2 limit
            GlobalConfig.MAX_SEQ_LEN = 1024
        
    if args.model:
        logger.info(f"🔄 Overriding Base Model: {args.model}")
        CONFIG.base_model = args.model
        GlobalConfig.MODEL_CONFIG["name"] = args.model
        
    if args.no_wandb:
        logger.info("📡 W&B Logging Disabled.")
        os.environ["WANDB_MODE"] = "offline"
        CONFIG.use_wandb = False

    if args.max_steps is not None:
        logger.info(f"🔢 Overriding Max Steps: {args.max_steps}")
        GlobalConfig.TRAIN_PARAMS["max_steps_override"] = args.max_steps
        CONFIG.max_steps = args.max_steps

    if args.save_steps is not None:
        logger.info(f"🔢 Overriding Save Steps: {args.save_steps}")
        GlobalConfig.TRAIN_PARAMS["save_steps_override"] = args.save_steps

    if args.inference_only:
        logger.info("🔮 Overriding Mode: INFERENCE_ONLY")
        GlobalConfig.TRAIN_PARAMS["inference_only_override"] = True

    if args.batch_size:
        logger.info(f"🔢 Overriding Batch Size: {args.batch_size}")
        CONFIG.batch_size = args.batch_size
    if args.grad_accum:
        logger.info(f"🔢 Overriding Grad Accum: {args.grad_accum}")
        CONFIG.grad_accumulation = args.grad_accum

    if args.resume:
        logger.info("🔄 Resumption Enabled: Will look for latest checkpoints.")
        GlobalConfig.TRAIN_PARAMS["resume_training"] = True
    else:
        GlobalConfig.TRAIN_PARAMS["resume_training"] = False

    if args.data_dir:
        from pathlib import Path
        logger.info(f"📁 Overriding Data Directory: {args.data_dir}")
        ENV.data_dir = Path(args.data_dir)
    
    if args.output_dir:
        from pathlib import Path
        logger.info(f"📁 Overriding Output Directory: {args.output_dir}")
        ENV.output_dir = Path(args.output_dir)
        # Update derived paths
        GlobalConfig.PROD_DIR = str(ENV.output_dir)
        GlobalConfig.LOG_DIR = str(ENV.output_dir / "logs")
        GlobalConfig.EXP_ROOT = str(ENV.output_dir / "experiment_artifacts")

    run_all_benchmarks(args.run)
