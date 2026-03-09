

try:
    from unsloth import FastLanguageModel
    HAS_UNSLOTH = True
except ImportError:
    HAS_UNSLOTH = False

import os
import gc
import json
import logging
import contextlib
from typing import Dict, List

import torch
from datasets import concatenate_datasets
from peft import PeftModel
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

from .config import CONFIG, GlobalConfig
from .trainer import init_medtime_trainer
from .inference import run_medtime_inference

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# 0. Data Preparation & Collator
# -----------------------------------------------------------------------------
class MedTimeBilingualCollator:
    """Collator for handling bilingual token ranges and grounding targets."""
    def __init__(self, tokenizer):
        self.tokenizer = tokenizer

    def __call__(self, features):
        token_ranges = [f.pop("token_ranges", []) for f in features]
        labels = [f.pop("labels") for f in features] if "labels" in features[0] else None

        for f in features:
            for k in list(f.keys()):
                if isinstance(f[k], str):
                    f.pop(k)

        batch = self.tokenizer.pad(features, padding=True, return_tensors="pt")

        if labels is not None:
            max_len = batch["input_ids"].shape[1]
            padded_labels = []
            for l in labels:
                remainder = [-100] * (max_len - len(l))
                if getattr(self.tokenizer, "padding_side", "right") == "left":
                    padded_labels.append(remainder + l)
                else:
                    padded_labels.append(l + remainder)
            batch["labels"] = torch.tensor(padded_labels, dtype=torch.long)

        batch["token_ranges"] = token_ranges
        return batch

def _get_assistant_ids(tokenizer):
    """Detects assistant header tokens by comparing tokenized prompts."""
    # ... (Same as before, abbreviated for clarity, but I will include full logic if tool requires full block replacement, here I use partial replacement strategy or full file?)
    # The tool instruction says "Rewrite the file". Since I am cutting Accelerator from multiple places, full rewrite or large chunk might be best.
    # But _get_assistant_ids is untouched.
    # _prep_medtime_dataset is untouched.
    # So I will preserve them.
    # I will construct the ReplacementContent to start AFTER _prep_medtime_dataset ends.
    return tokenizer.encode("Assistant:", add_special_tokens=False)

# I will use StartLine/EndLine to target specific blocks.
# Block 1: Imports (Lines 18-20)
# Block 2: load_backbone_unified (Lines 188-291)
# Block 3: MedTimeModelFactory.load (Lines 296-331)
# Block 4: run_llm_experiment (Lines 350-435)

# Actually, I'll do it in one big chunk from line 188 downwards because they all use Accelerator.
# And imports at top.



# -----------------------------------------------------------------------------
# 0. Data Preparation & Collator
# -----------------------------------------------------------------------------
class MedTimeBilingualCollator:
    """Collator for handling bilingual token ranges and grounding targets."""
    def __init__(self, tokenizer):
        self.tokenizer = tokenizer

    def __call__(self, features):
        token_ranges = [f.pop("token_ranges", []) for f in features]
        labels = [f.pop("labels") for f in features] if "labels" in features[0] else None

        for f in features:
            for k in list(f.keys()):
                if isinstance(f[k], str):
                    f.pop(k)

        batch = self.tokenizer.pad(features, padding=True, return_tensors="pt")

        if labels is not None:
            max_len = batch["input_ids"].shape[1]
            padded_labels = []
            for l in labels:
                remainder = [-100] * (max_len - len(l))
                if getattr(self.tokenizer, "padding_side", "right") == "left":
                    padded_labels.append(remainder + l)
                else:
                    padded_labels.append(l + remainder)
            batch["labels"] = torch.tensor(padded_labels, dtype=torch.long)

        batch["token_ranges"] = token_ranges
        return batch

def _get_assistant_ids(tokenizer):
    """Detects assistant header tokens by comparing tokenized prompts."""
    test_msgs = [{"role": "user", "content": "H"}]
    try:
        with_gen = tokenizer.apply_chat_template(test_msgs, tokenize=False, add_generation_prompt=True)
        ids_with = tokenizer.encode(with_gen, add_special_tokens=False)
        without_gen = tokenizer.apply_chat_template(test_msgs, tokenize=False, add_generation_prompt=False)
        ids_without = tokenizer.encode(without_gen, add_special_tokens=False)
        
        prefix_len = 0
        for i in range(min(len(ids_with), len(ids_without))):
            if ids_with[i] == ids_without[i]:
                prefix_len = i + 1
            else:
                break
        
        header_ids = ids_with[prefix_len:]
        if len(header_ids) > 1:
            first_decoded = tokenizer.decode([header_ids[0]]).strip()
            if "Assistant" in first_decoded or "assistant" in first_decoded:
                return header_ids[:1]
        return header_ids
    except:
        return tokenizer.encode("Assistant:", add_special_tokens=False)

def _prep_medtime_dataset(cfg, data_bundle, tokenizer, formatting_func, max_seq_len, is_smoke):
    """Prepares and tokenizes training/eval datasets with manual label masking."""
    assistant_ids = _get_assistant_ids(tokenizer)
    
    def pre_tokenize_and_manual_mask(examples):
        texts = formatting_func(examples)
        tokenized = tokenizer(texts, truncation=True, max_length=max_seq_len, padding=False)
        all_ids = tokenized["input_ids"]
        all_labels, all_ranges = [], []

        for b_idx in range(len(all_ids)):
            ids = all_ids[b_idx]
            mask_idx = -1
            for i in range(len(ids) - len(assistant_ids) + 1):
                if ids[i : i + len(assistant_ids)] == assistant_ids:
                    mask_idx = i + len(assistant_ids)
                    break

            label = [-100] * len(ids)
            if mask_idx != -1:
                # Mask prompt: labels only for generated assistant response
                for j in range(mask_idx, len(ids)):
                    label[j] = ids[j]
            else:
                logger.warning(f"⚠️ Prompt Masking Failed for sample {b_idx}! 'assistant_ids' not found.")
            all_labels.append(label)

            full_t, inp_s, coords = texts[b_idx], examples["input"][b_idx], examples["coords"][b_idx]
            enc = tokenizer(full_t, truncation=True, max_length=max_seq_len, return_offsets_mapping=True, add_special_tokens=False)
            off = enc["offset_mapping"]
            p_off = full_t.find(inp_s)

            all_ranges.append([
                [idx for idx, (ts, te) in enumerate(off) if max(ts, p_off + s) < min(te, p_off + e)]
                for s, e in coords
            ])

        return {
            "input_ids": all_ids,
            "attention_mask": tokenized["attention_mask"],
            "labels": all_labels,
            "token_ranges": all_ranges,
        }

    train_sets = cfg.get("train_sets", [])
    valid_train_sets = []
    for k in train_sets:
        if k in data_bundle:
            if len(data_bundle[k]) > 0:
                valid_train_sets.append(k)

    raw_train_ds = None
    if valid_train_sets:
        logger.info(f"📚 Combining {len(valid_train_sets)} train sets: {valid_train_sets}")
        raw_train_ds = concatenate_datasets([data_bundle[k] for k in valid_train_sets]).shuffle(seed=42)
    elif cfg.get("max_steps", 0) > 0:
        logger.warning("⚠️ No valid train sets found, fallback to 'syn_train'")
        raw_train_ds = data_bundle.get("syn_train")

    if is_smoke and raw_train_ds:
        raw_train_ds = raw_train_ds.select(range(min(5, len(raw_train_ds))))

    train_ds = raw_train_ds.map(pre_tokenize_and_manual_mask, batched=True, remove_columns=raw_train_ds.column_names) if raw_train_ds and len(raw_train_ds) > 0 else None

    eval_ds = None
    if cfg.get("dev_key") and data_bundle.get(cfg["dev_key"]):
        r_eval = data_bundle[cfg["dev_key"]]
        if is_smoke: r_eval = r_eval.select(range(min(2, len(r_eval))))
        if len(r_eval) > 0:
            eval_ds = r_eval.map(pre_tokenize_and_manual_mask, batched=True, remove_columns=r_eval.column_names)

    return train_ds, eval_ds, raw_train_ds, MedTimeBilingualCollator(tokenizer)

def learn_and_fix_patterns(trainer, dataset, formatting_func):
    logger.info("🕵️ Auto-calibrating Token Patterns...")
    raw_sample = dataset[0]
    formatted_text = formatting_func({k: [v] for k, v in raw_sample.items()})[0]
    tk = getattr(trainer, "processing_class", trainer.tokenizer)
    ids = tk(formatted_text, add_special_tokens=False)["input_ids"]

    new_trig, new_t = [], []
    for length in range(1, 11):
        for i in range(len(ids) - length + 1):
            sub = ids[i : i + length]
            dec = tk.decode(sub).replace(" ", "")
            if dec in ['"trigger":"', 'trigger":"', '{"trigger":"', ',"trigger":"']:
                new_trig.append(list(sub))
            if dec in ['"t":"', 't":"', '{"t":"', ',"t":"']:
                new_t.append(list(sub))

    trainer.trig_patterns = [
        list(p) for p in {tuple(p) for p in (getattr(trainer, "trig_patterns", []) + new_trig)}
    ]
    trainer.t_patterns = [
        list(p) for p in {tuple(p) for p in (getattr(trainer, "t_patterns", []) + new_t)}
    ]
    logger.info(f"✅ Calibrated: {len(trainer.trig_patterns)} Trigger Patterns, {len(trainer.t_patterns)} Time Patterns.")


# -----------------------------------------------------------------------------
# 1. Model Loading
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# 1. Model Loading
# -----------------------------------------------------------------------------
def load_backbone_unified(model_name=None, max_seq_len=None, enable_lora=True, force_transformers=False):
    target_model = model_name if model_name else CONFIG.base_model
    target_len = max_seq_len if max_seq_len else CONFIG.max_seq_len

    source_desc = "Kaggle Cache" if "/kaggle/input/" in target_model else "HuggingFace/Hub"
    print(f"📡 Loading Model from [{source_desc}]: {target_model} | Len: {target_len}")
    
    # Determine device for Unsloth manual load
    local_rank = int(os.environ.get("LOCAL_RANK", 0))
    device = f"cuda:{local_rank}" if torch.cuda.is_available() else "cpu"

    if torch.cuda.is_available():
        if "P100" in torch.cuda.get_device_name(0):
             logger.info(f"⚠️ Detected P100: Forcing Transformers backend.")
             force_transformers = True

    if HAS_UNSLOTH and not force_transformers:
        logger.info(f"🚀 Loading via Unsloth (Rank {local_rank})")
        # Unsloth requires explicit loading
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=target_model, 
            max_seq_length=target_len, 
            load_in_4bit=True,
            device_map={"": local_rank}, # Unsloth specific mapping
            local_files_only=True # [FIX] Prevent Unsloth from pinging HF (Timeout)
        )
    else:
        logger.warning("⚠️ Unsloth not found or forced off. Fallback to Transformers + BitsAndBytes.")
        tokenizer = AutoTokenizer.from_pretrained(target_model, trust_remote_code=True)
        if hasattr(tokenizer, "pad_token") and tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        quant_config = None
        if torch.cuda.is_available():
            from transformers import BitsAndBytesConfig
            quant_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16,
                bnb_4bit_use_double_quant=True,
            )
        
        # [SIMPLIFICATION] Let Transformers handle placement
        model = AutoModelForCausalLM.from_pretrained(
            target_model, 
            trust_remote_code=True, 
            quantization_config=quant_config,
            torch_dtype=torch.bfloat16, 
            device_map="auto",
            low_cpu_mem_usage=True,
        )
        
        # Precision mismatch fixes
        if hasattr(model, "lm_head"): model.lm_head.to(torch.bfloat16)
        if hasattr(model, "model") and hasattr(model.model, "embed_tokens"):
            model.model.embed_tokens.to(torch.bfloat16)

        model = prepare_model_for_kbit_training(model)
        model.gradient_checkpointing_enable()

    def formatting_prompts_func(examples):
        texts = []
        for inst, inp, out in zip(examples["instruction"], examples["input"], examples["output"]):
            msgs = [
                {"role": "system", "content": inst},
                {"role": "user", "content": inp},
                {"role": "assistant", "content": out},
            ]
            try:
                if hasattr(tokenizer, "apply_chat_template"):
                    texts.append(tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=False))
                else:
                    raise Exception("No template")
            except:
                texts.append(f"System: {inst}\nUser: {inp}\nAssistant: {out}")
        return texts

    if enable_lora and HAS_UNSLOTH and not force_transformers:
        model = FastLanguageModel.get_peft_model(
            model,
            r=CONFIG.lora_r,
            lora_alpha=CONFIG.lora_alpha,
            lora_dropout=CONFIG.lora_dropout,
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
            bias="none",
            use_gradient_checkpointing="unsloth", 
            random_state=3407,
            use_rslora=False,
            loftq_config=None,
        )
    elif enable_lora:
        peft_config = LoraConfig(
            r=CONFIG.lora_r,
            lora_alpha=CONFIG.lora_alpha,
            lora_dropout=CONFIG.lora_dropout,
            bias="none",
            task_type="CAUSAL_LM",
        )
        model = get_peft_model(model, peft_config)
        model.config.use_cache = False 

    return model, tokenizer, formatting_prompts_func


class MedTimeModelFactory:
    """Unified Model Loading and Management"""
    @staticmethod
    def load(cfg, max_seq_len, force_transformers=False):
        inference_only = cfg.get("inference_only", False)
        base_model = cfg.get("base_model", CONFIG.base_model)
        max_steps = cfg.get("max_steps", GlobalConfig.TRAIN_PARAMS["max_steps"])
        
        if inference_only:
            ckpt_path = cfg.get('checkpoint_path', 'None')
            logger.info(f"🔄 Loading Inference-Only: {base_model} + {ckpt_path}")
            
            # No accelerator context needed usually for load
            if HAS_UNSLOTH and not force_transformers:
                local_rank = int(os.environ.get("LOCAL_RANK", 0))
                model, tokenizer = FastLanguageModel.from_pretrained(
                    model_name=base_model, max_seq_length=max_seq_len, dtype=None, load_in_4bit=True,
                    device_map={"": local_rank}, local_files_only=True
                )
            else:
                model = AutoModelForCausalLM.from_pretrained(base_model, load_in_4bit=True, torch_dtype=torch.bfloat16, device_map="auto")
                tokenizer = AutoTokenizer.from_pretrained(base_model)
                    
            if cfg.get('checkpoint_path'):
                model = PeftModel.from_pretrained(model, cfg['checkpoint_path'], is_trainable=False)
            
            return model, tokenizer, None
            
        model, tokenizer, formatting_func = load_backbone_unified(
            model_name=base_model,
            max_seq_len=max_seq_len,
            enable_lora=(max_steps > 0),
            force_transformers=force_transformers
        )
        return model, tokenizer, formatting_func

# -----------------------------------------------------------------------------
# 2. Main Entry Point
# -----------------------------------------------------------------------------
def safe_experiment_execution(func):
    import sys
    import traceback
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            msg = f"❌ FATAL ERROR in {func.__name__}: {str(e)}"
            sys.stderr.write(f"\n{msg}\n")
            logger.error(msg, exc_info=True)
            traceback.print_exc()
            sys.exit(1)
    return wrapper

@safe_experiment_execution
def run_llm_experiment(run_name, cfg, data_bundle):
    """
    Main entry point for an LLM experiment.
    Decouples Training and Inference logic to submodule calls.
    """
    os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
    
    # Accelerator instantiation removed - letting Trainer handle devices

    is_smoke = GlobalConfig.TRAIN_PARAMS.get("smoke_test", False)
    max_seq_len = cfg.get("max_seq_len", GlobalConfig.MAX_SEQ_LEN)
    max_steps = cfg.get("max_steps", GlobalConfig.TRAIN_PARAMS["max_steps"])
    if is_smoke: max_steps = min(max_steps, 5)

    output_dir = os.path.join(GlobalConfig.EXP_ROOT, run_name)
    model, tokenizer, formatting_func = None, None, None

    # 1. Training Phase
    is_inference_only = cfg.get("inference_only", False)
    if is_inference_only:
        logger.info("🔧 Inference Only Mode Active (Skipping Training)")
    elif max_steps > 0:
        model, tokenizer, formatting_func = MedTimeModelFactory.load(
            cfg, max_seq_len, force_transformers=False
        )
        
        train_ds, eval_ds, raw_train_ds, custom_collator = _prep_medtime_dataset(
            cfg, data_bundle, tokenizer, formatting_func, max_seq_len, is_smoke
        )

        logger.info("🔥 Starting Training Cycle...")
        trainer = init_medtime_trainer(
            model, tokenizer, train_ds, eval_ds, custom_collator, 
            run_name, output_dir, cfg
        )
        
        if cfg.get("family") == "llm_medtime":
            learn_and_fix_patterns(trainer, raw_train_ds, formatting_func)
        
        from transformers.trainer_utils import get_last_checkpoint
        last_checkpoint = get_last_checkpoint(output_dir)
        if last_checkpoint:
            logger.info(f"🔄 Resuming from {last_checkpoint}")
        
        trainer.train(resume_from_checkpoint=last_checkpoint)
        trainer.save_model(output_dir)
        tokenizer.save_pretrained(output_dir)
        
        del trainer
        import gc; gc.collect()
        import torch
        if torch.cuda.is_available(): torch.cuda.empty_cache()
        cfg['checkpoint_path'] = output_dir

    # 2. Inference Phase
    if model is None:
        model, tokenizer, formatting_func = MedTimeModelFactory.load(
            cfg, max_seq_len, force_transformers=False
        )

    logger.info("🧪 Launching Inference Engine...")
    results, predictions = run_medtime_inference(
        model, tokenizer, formatting_func, data_bundle, 
        cfg, run_name, is_smoke
    )

    if model is not None: del model
    if tokenizer is not None: del tokenizer
    gc.collect()
    if torch.cuda.is_available(): torch.cuda.empty_cache()
    

    # Single-Process Inference does not require Accelerator synchronization
    if torch.distributed.is_initialized():
        torch.distributed.barrier()
        
    return results, predictions
