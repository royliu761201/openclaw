
import os
import torch
import json
import logging
import gc
import time
import uuid
from tqdm.auto import tqdm
from transformers import AutoTokenizer

from .config import CONFIG
from .engine import MedTimeEngine
from .evaluator import MedTimeEvaluator

# Optional Unsloth support
try:
    from unsloth import FastLanguageModel
    HAS_UNSLOTH = True
except ImportError:
    HAS_UNSLOTH = False

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# 0. Helpers
# -----------------------------------------------------------------------------
def _maybe_cleanup_cuda():
    """Safe GC + CUDA cache cleanup (won't crash on CPU-only)."""
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()



def build_inference_prompt(tokenizer, instruction, user_input):
    messages = [{"role": "system", "content": instruction}, {"role": "user", "content": user_input}]
    try:
        return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    except:
        return f"System: {instruction}\nUser: {user_input}\nAssistant:"

# -----------------------------------------------------------------------------
# 1. Inference Runner
# -----------------------------------------------------------------------------
class MedTimeInferenceRunner:
    """Standardized Inference and Post-processing"""
    
    def __init__(self, model, tokenizer, cfg):
        self.model = model
        self.tokenizer = tokenizer
        self.cfg = cfg
        self.gen_config = {
            "max_new_tokens": cfg.get("max_new_tokens", 1536),
            "use_cache": True,
            "do_sample": False,
            "pad_token_id": tokenizer.pad_token_id or tokenizer.eos_token_id,
        }

    def predict_batch(self, batch_ex, batch_start_idx=0):
        """Batched prediction with explicit padding management."""
        prompts = [build_inference_prompt(self.tokenizer, ex["instruction"], ex["input"]) for ex in batch_ex]
        
        original_padding_side = self.tokenizer.padding_side
        self.tokenizer.padding_side = "left"
        
        inputs = self.tokenizer(prompts, return_tensors="pt", padding=True).to(self.model.device)
        
        with torch.no_grad():
            outs = self.model.generate(**inputs, **self.gen_config)
            
        self.tokenizer.padding_side = original_padding_side
        
        _maybe_cleanup_cuda()
        
        batch_results = []
        for i, out in enumerate(outs):
            input_len = inputs.input_ids.shape[1]
            gen_text = self.tokenizer.decode(out[input_len:], skip_special_tokens=True)
            
            parsed_json = MedTimeEngine.Data.safe_json_extract(gen_text)
            
            if isinstance(parsed_json, list) and len(parsed_json) > 0:
                ex = batch_ex[i]
                user_input = ex["input"]
                meta_data = json.loads(ex["meta"]) if isinstance(ex["meta"], str) else ex["meta"]
                inner_meta = meta_data.get("meta_info", {}) if isinstance(meta_data, dict) else {}
                parsed_json = MedTimeEngine.PostProcess.safe_fix_timeline(parsed_json, user_input, inner_meta)
                
            id_key = self.cfg.get("id_key", "pid")
            record_id = batch_ex[i].get(id_key, f"unknown_{batch_start_idx + i}")
            
            if (batch_start_idx + i) < 5 or (batch_start_idx + i) % 100 == 0:
                logger.info(f"📝 Prediction {batch_start_idx+i+1} [{record_id}]: {str(parsed_json)[:100]}...")
                
            batch_results.append((record_id, parsed_json))
            
        return batch_results

# -----------------------------------------------------------------------------
# 2. Main Logic
# -----------------------------------------------------------------------------

def run_medtime_inference(model, tokenizer, formatting_func, data_bundle, cfg, run_name="debug", is_smoke=False):
    """Performs single-process inference."""
    # [SIMPLIFIED] Removed Accelerator dependency.
    # We assume model is already on correct device (via device_map="auto").
    
    # Enable Fast Kernels
    if HAS_UNSLOTH and not cfg.get("force_transformers", False):
        logger.info("⚡ Enabling FastLanguageModel Inference Optimizations...")
        FastLanguageModel.for_inference(model)
    
    model.eval()
    logger.info("🧪 Launching Inference (Single Process).")

    multi_summaries = []
    all_preds_map = {}
    test_keys = cfg.get("test_sets", [])

    for t_key in test_keys:
        logger.info(f"🔮 Batched Inference: {t_key}")
        test_ds = data_bundle[t_key]
        if is_smoke: test_ds = test_ds.select(range(min(2, len(test_ds))))

        _maybe_cleanup_cuda()

        preds = {}
        # Single-Process Logic
        runner = MedTimeInferenceRunner(model, tokenizer, cfg)
        inf_batch_size = cfg.get("inference_batch_size", CONFIG.inference_batch_size)
        
        for i in tqdm(range(0, len(test_ds), inf_batch_size), desc=f"Predicting {t_key}"):
            if (i // inf_batch_size) % 10 == 0: 
                _maybe_cleanup_cuda()
            
            batch_ex = [test_ds[idx] for idx in range(i, min(i + inf_batch_size, len(test_ds)))]
            batch_results = runner.predict_batch(batch_ex, i)
            for rid, p_json in batch_results:
                preds[rid] = p_json

        if preds:
            logger.info(f"✅ Processing {len(preds)} predictions...")
            id_key = cfg.get("id_key", "pid")
            gold_ref = []
            if "gold_info" in data_bundle:
                gold_ref = [{id_key: rid, "gold_obj": data_bundle["gold_info"][rid]["timeline"]}
                           for rid in preds.keys() if rid in data_bundle["gold_info"]]
            
            summary = MedTimeEvaluator.summarize(MedTimeEvaluator.calculate_all(gold_ref, preds)) if gold_ref else {"msg": "No gold"}
            summary.update({"run_name": run_name, "test_set": t_key, "family": cfg["family"]})
            
            if CONFIG.use_wandb:
                import wandb
                if wandb.run is None: 
                    from src.common.wandb_utils import strict_wandb_init
                    # We might not have full config here if stripped, using simplified dict
                    strict_wandb_init(project=CONFIG.wandb_project, name=run_name, config=cfg)
                
                wandb.log(summary)
            
            multi_summaries.append(summary)
            all_preds_map[t_key] = dict(preds)

    return multi_summaries, all_preds_map

