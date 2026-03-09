import json
import logging
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import numpy as np
import torch
import torch.nn as nn
from datasets import Dataset, concatenate_datasets
from tqdm.auto import tqdm
from transformers import (
    AutoModelForTokenClassification,
    AutoTokenizer,
    DataCollatorForTokenClassification,
    EarlyStoppingCallback,
    Trainer,
    TrainingArguments,
)

from .config import GlobalConfig
from .engine import MedTimeEngine
from .evaluator import MedTimeCallback, MedTimeEvaluator

logger = logging.getLogger(__name__)


# ==========================================
# 1. Rule-based Baseline
# ==========================================
def build_rule_based_timeline(sample: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Trigger-Pivot Extraction Logic:
    1. Scan all dates for Lighthouse Year
    2. Scan triggers
    3. Alignment: In-sentence > Preceding nearest > Anchor
    4. Year Correction
    """
    raw_text = sample.get("input")

    # Metadata & Lighthouse
    meta_raw = sample.get("meta", "{}")
    meta_full = json.loads(meta_raw) if isinstance(meta_raw, str) else meta_raw
    inner_meta = meta_full.get("meta_info", {})
    anchor_dt = MedTimeEngine.Temporal.parse_meta_date(inner_meta)

    raw_dts = MedTimeEngine.Temporal.extract_all_dates(raw_text, return_raw=True)
    all_dates_idx = [{"dt": d[1], "pos": d[2]} for d in raw_dts if isinstance(d, tuple)]

    doc_years = [d["dt"].year for d in all_dates_idx if d["dt"].year < 2024]
    lighthouse_year = (
        max(set(doc_years), key=doc_years.count)
        if doc_years
        else (anchor_dt.year if anchor_dt else 2019)
    )

    events = []
    sentences = MedTimeEngine.Text.split_sentences(raw_text)

    for idx, (s_start, s_end, sent) in enumerate(sentences):
        matched_trigger = None
        for trigger_cfg in MedTimeEngine.EVENT_TRIGGERS:
            match = trigger_cfg["pattern"].search(sent)
            if match:
                matched_trigger = match.group()
                break

        if matched_trigger:
            best_t_obj = None

            # Strategy A: In-sentence
            sent_dts = MedTimeEngine.Temporal.extract_all_dates(sent, return_raw=False)
            if sent_dts:
                best_t_obj = sent_dts[0]

            # Strategy B: Preceding nearest
            if not best_t_obj and all_dates_idx:
                preceding = [d for d in all_dates_idx if d["pos"] <= s_start]
                if preceding:
                    best_t_obj = max(preceding, key=lambda x: x["pos"])["dt"]

            # Strategy C: Relative
            if not best_t_obj and anchor_dt:
                rels = MedTimeEngine.Temporal.resolve_relative(sent, anchor_dt)
                if rels:
                    best_t_obj = rels[0]

            # Strategy D: Year Correction
            t_val = None
            if best_t_obj:
                if best_t_obj.year == 2024:
                    try:
                        best_t_obj = best_t_obj.replace(year=lighthouse_year)
                    except:
                        pass
                t_val = best_t_obj.date().isoformat()
            elif anchor_dt:
                t_val = anchor_dt.date().isoformat()

            is_interval = any(k in sent for k in MedTimeEngine.INTERVAL_KEYWORDS)

            events.append(
                {
                    "sort_key": (MedTimeEngine.Temporal.to_timestamp(t_val) or 0, idx),
                    "item": {
                        "trigger": matched_trigger,
                        "e": sent[:40].strip(),
                        "t": t_val,
                        "n": "I" if is_interval else "P",
                    },
                }
            )

    if not events:
        return [{"trigger": "None", "e": "No events detected", "t": None, "n": "P"}]

    events.sort(key=lambda x: x["sort_key"])
    return [e["item"] for e in events]


def run_rule_based_experiment(run_name: str, cfg: Dict[str, Any], data_bundle: Dict[str, Any]):
    logger.info(f"🚀 [Rule-based] Start: {run_name}")
    is_smoke = GlobalConfig.TRAIN_PARAMS.get("smoke_test", False)

    multi_summaries = []
    all_preds_map = {}

    test_keys = cfg.get("test_sets", [])
    for t_key in test_keys:
        test_ds = data_bundle[t_key]
        if is_smoke:
            test_ds = test_ds.select(range(min(2, len(test_ds))))

        preds = {
            ex["pid"]: build_rule_based_timeline(ex)
            for ex in tqdm(test_ds, desc=f"Rule Ext [{t_key}]")
        }
        all_preds_map[t_key] = preds

        gold_info = data_bundle["gold_info"]
        gold_ref = [{"pid": pid, "gold_obj": gold_info[pid]["timeline"]} for pid in preds.keys()]

        metrics_list = MedTimeEvaluator.calculate_all(gold_ref, preds)
        summary = MedTimeEvaluator.summarize(metrics_list)
        summary.update({"run_name": run_name, "test_set": t_key, "family": "rule_based"})
        multi_summaries.append(summary)

    return multi_summaries, all_preds_map


# ==========================================
# 2. IE-Span Baseline
# ==========================================
@dataclass
class IESpanConfig:
    lang: str = "zh"
    model_path: Optional[str] = None  # Added field
    max_seq_len: int = 512
    neg_ratio: float = 0.3
    batch_size: int = 16
    learning_rate: float = 2e-5
    max_steps: int = 1500
    warmup_ratio: float = 0.1
    weight_decay: float = 0.01
    logging_steps: int = 10
    eval_steps: int = 50
    early_stopping_patience: int = 3
    early_stopping_threshold: float = 0.001
    max_grad_norm: float = 1

    label2id = {"O": 0, "B-EVENT": 1, "I-EVENT": 2}
    id2label = {0: "O", 1: "B-EVENT", 2: "I-EVENT"}

    @property
    def backbone(self):
        # Priority: explicit model_path > hardcoded defaults
        if self.model_path:
            return self.model_path
            
        return (
            "hfl/chinese-roberta-wwm-ext-large"
            if self.lang == "zh" # Default to RoBERTa for Chinese
            else "microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext"
        )

    def update(self, config_dict):
        for key, value in config_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)
        return self


def compute_token_metrics(eval_preds):
    logits, labels = eval_preds
    predictions = np.argmax(logits, axis=-1)
    # Filter out ignored labels (-100)
    true_predictions = [
        p for pred, lab in zip(predictions, labels) for (p, l) in zip(pred, lab) if l != -100
    ]
    true_labels = [
        l for pred, lab in zip(predictions, labels) for (p, l) in zip(pred, lab) if l != -100
    ]

    tp = sum(1 for p, l in zip(true_predictions, true_labels) if l != 0 and p == l)
    fp = sum(1 for p, l in zip(true_predictions, true_labels) if l == 0 and p != 0)
    fn = sum(1 for p, l in zip(true_predictions, true_labels) if l != 0 and p == 0)

    p, r = tp / (tp + fp + 1e-6), tp / (tp + fn + 1e-6)
    return {"eval_token_f1": round(2 * p * r / (p + r + 1e-6), 4)}


class WeightedIESpanTrainer(Trainer):
    def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
        labels = inputs.get("labels")
        outputs = model(**inputs)
        # Class weights 1:5:5
        weights = torch.tensor([0.2727, 1.3636, 1.3636]).to(self.model.device)
        loss_fct = nn.CrossEntropyLoss(weight=weights)
        loss = loss_fct(outputs.get("logits").view(-1, 3), labels.view(-1))
        return (loss, outputs) if return_outputs else loss


class IESpanRunner:
    def __init__(self, cfg: IESpanConfig):
        self.cfg = cfg
        self.tokenizer = AutoTokenizer.from_pretrained(cfg.backbone)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = AutoModelForTokenClassification.from_pretrained(cfg.backbone, num_labels=3).to(
            self.device
        )

    def _prepare_bio_dataset(self, raw_dataset, name="Train"):
        is_smoke = GlobalConfig.TRAIN_PARAMS.get("smoke_test", False)
        target_ds = (
            raw_dataset.select(range(min(5, len(raw_dataset)))) if is_smoke else raw_dataset
        )

        chunked_samples = []
        for ex in tqdm(target_ds, desc=f"🧬 {name} Chunking"):
            text = ex["input"]
            try:
                gold_tl = json.loads(ex["meta"])["raw_timeline"]
            except:
                continue

            sentences = MedTimeEngine.Text.split_sentences(text)
            for s_start, s_end, s_text in sentences:
                if len(s_text) < 5:
                    continue
                char_labels = ["O"] * len(s_text)
                has_evt = False
                for item in gold_tl:
                    g_s, g_e = int(item.get("start", -1)), int(item.get("end", -1))
                    if s_start <= g_s < s_end:
                        rel_s, rel_e = g_s - s_start, min(g_e - s_start, len(s_text))
                        if rel_s < len(char_labels):
                            char_labels[rel_s] = "B-EVENT"
                            for i in range(rel_s + 1, rel_e):
                                char_labels[i] = "I-EVENT"
                            has_evt = True

                if not has_evt and np.random.rand() > self.cfg.neg_ratio:
                    continue

                enc = self.tokenizer(
                    s_text,
                    truncation=True,
                    max_length=self.cfg.max_seq_len,
                    return_offsets_mapping=True,
                )
                token_labels = [
                    (-100 if s == e else self.cfg.label2id.get(char_labels[s], 0))
                    for s, e in enc["offset_mapping"]
                ]
                chunked_samples.append(
                    {
                        "input_ids": enc.input_ids,
                        "attention_mask": enc.attention_mask,
                        "labels": token_labels,
                    }
                )

        return Dataset.from_list(chunked_samples)

    def _hybrid_pairing(self, span_txt, g_s, g_e, sent_txt, all_dates, anchor_dt):
        best_t_obj = None

        if anchor_dt:
            rels = MedTimeEngine.Temporal.resolve_relative(sent_txt, anchor_dt)
            if rels:
                best_t_obj = rels[0]

        if not best_t_obj and all_dates:
            preceding = [d for d in all_dates if d["pos"] <= g_s]
            if preceding:
                best_t_obj = max(preceding, key=lambda x: x["pos"])["dt"]
            else:
                best_t_obj = min(all_dates, key=lambda x: abs(x["pos"] - g_s))["dt"]

        final_t_str = None
        if best_t_obj:
            doc_years = [d["dt"].year for d in all_dates if d.get("dt") and d["dt"].year < 2024]
            lighthouse_year = (
                max(set(doc_years), key=doc_years.count)
                if doc_years
                else (anchor_dt.year if anchor_dt else 2019)
            )

            if best_t_obj.year == 2024:
                try:
                    best_t_obj = best_t_obj.replace(year=lighthouse_year)
                except:
                    pass

            final_t_str = best_t_obj.date().isoformat()

        if not final_t_str and anchor_dt:
            final_t_str = anchor_dt.date().isoformat()

        return {
            "trigger": span_txt[:20],
            "e": span_txt[:40],
            "t": final_t_str,
            "n": "P",
            "start": g_s,
            "end": g_e,
        }

    def run(self, train_raw, dev_raw, test_sets_map, gold_info, run_name="ie_experiment"):
        # A. Prepare
        train_ds = self._prepare_bio_dataset(train_raw, "Train")
        eval_ds = self._prepare_bio_dataset(dev_raw, "Dev")

        # B. Train
        # Force WandB Project (Redundant Safety)
        import wandb
        try:
             if wandb.run is None:
                 wandb.init(project="medtime", name=run_name, reinit=True)
        except:
             pass

        train_args = TrainingArguments(
            output_dir=os.path.join(GlobalConfig.EXP_ROOT, f"strong_ie_{self.cfg.lang}"),
            max_steps=self.cfg.max_steps,
            run_name=run_name,
            per_device_train_batch_size=self.cfg.batch_size,
            learning_rate=self.cfg.learning_rate,
            warmup_steps=int(self.cfg.max_steps * self.cfg.warmup_ratio),
            weight_decay=self.cfg.weight_decay,
            logging_steps=self.cfg.logging_steps,
            eval_strategy="steps",
            save_strategy="steps",
            eval_steps=self.cfg.eval_steps,
            save_steps=self.cfg.eval_steps,
            load_best_model_at_end=True,
            metric_for_best_model="eval_token_f1",
            greater_is_better=True,
            save_total_limit=1,  # HF protects Best, so 1 = Rolling Latest
            fp16=torch.cuda.is_available(),
            report_to="wandb" if GlobalConfig.TRAIN_PARAMS.get("use_wandb", True) else "none",
            max_grad_norm=self.cfg.max_grad_norm,
            remove_unused_columns=True,
        )

        trainer = WeightedIESpanTrainer(
            model=self.model,
            args=train_args,
            train_dataset=train_ds,
            eval_dataset=eval_ds,
            compute_metrics=compute_token_metrics,
            data_collator=DataCollatorForTokenClassification(self.tokenizer),
        )

        trainer.add_callback(
            EarlyStoppingCallback(
                early_stopping_patience=self.cfg.early_stopping_patience,
                early_stopping_threshold=self.cfg.early_stopping_threshold,
            )
        )
        trainer.add_callback(MedTimeCallback())



        if train_ds:
            from transformers.trainer_utils import get_last_checkpoint
            last_checkpoint = get_last_checkpoint(train_args.output_dir)
            if last_checkpoint is not None:
                logger.info(f"🔄 Checkpoint found at {last_checkpoint}. Resuming training...")
                trainer.train(resume_from_checkpoint=True)
            else:
                logger.info(f"🆕 No checkpoint found. Starting fresh training...")
                trainer.train()

        # C. Inference
        multi_summaries, all_preds_map = {}, {}
        # Force CPU for inference to avoid MPS "Placeholder storage" errors
        self.device = torch.device("cpu")
        self.model.to(self.device)
        self.model.eval()

        for t_key, test_ds in test_sets_map.items():
            preds = {}
            for ex in tqdm(test_ds, desc=f"Probing {t_key}"):
                full_text = ex["input"]
                meta_data = json.loads(ex["meta"])
                inner_meta = meta_data.get("meta_info", {})
                anchor_dt = MedTimeEngine.Temporal.parse_meta_date(inner_meta)

                raw_dts = MedTimeEngine.Temporal.extract_all_dates(full_text, return_raw=True)
                all_dates = [{"dt": d[1], "pos": d[2]} for d in raw_dts if isinstance(d, tuple)]

                case_tl = []
                sentences = MedTimeEngine.Text.split_sentences(full_text)

                for s_start, s_end, s_text in sentences:
                    inputs = self.tokenizer(
                        s_text,
                        truncation=True,
                        max_length=512,
                        return_offsets_mapping=True,
                        return_tensors="pt",
                    ).to(self.device)
                    offsets = inputs.pop("offset_mapping")[0].tolist()
                    with torch.no_grad():
                        logits = self.model(**inputs).logits

                    probs = torch.softmax(logits, dim=-1)[0].cpu().tolist()
                    curr_s = None
                    last_e = s_start

                    for i, p in enumerate(probs):
                        s_off, e_off = offsets[i]
                        if s_off == e_off:
                            continue

                        if p[1] > 0.4:  # B-EVENT
                            if curr_s is not None:
                                span_txt = full_text[curr_s:last_e]
                                case_tl.append(
                                    self._hybrid_pairing(
                                        span_txt, curr_s, last_e, s_text, all_dates, anchor_dt
                                    )
                                )
                            curr_s = s_start + s_off
                        last_e = s_start + e_off

                    if curr_s is not None:
                        span_txt = full_text[curr_s:last_e]
                        case_tl.append(
                            self._hybrid_pairing(
                                span_txt, curr_s, last_e, s_text, all_dates, anchor_dt
                            )
                        )

                preds[ex["pid"]] = (
                    case_tl if case_tl else [{"trigger": "None", "e": "None", "t": None, "n": "P"}]
                )

            all_preds_map[t_key] = preds

            gold_ref = [
                {"pid": pid, "gold_obj": gold_info[pid]["timeline"]} for pid in preds.keys()
            ]
            metrics_list = MedTimeEvaluator.calculate_all(gold_ref, preds)
            summary = MedTimeEvaluator.summarize(metrics_list)

            summary.update({"test_set": t_key, "family": "ie_span", "run_name": run_name})
            multi_summaries[t_key] = summary

        return list(multi_summaries.values()), all_preds_map


def run_ie_span_experiment(run_name, cfg, data_bundle):
    # Flush memory logic should be external or here?
    # The snippet used flush_memory() from global util.
    # We will assume caller handles major GC or we do it here.
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    if cfg.get("max_seq_len", 0) > 512:
        cfg["max_seq_len"] = 512

    ie_cfg = IESpanConfig(
        lang=cfg.get("lang", "zh"),
        model_path=cfg.get("model_path")  # Pass model_path explicitly
    )
    ie_cfg.update(cfg)

    if GlobalConfig.TRAIN_PARAMS.get("smoke_test", False):
        ie_cfg.max_steps = 5
        ie_cfg.eval_steps = 5
        ie_cfg.batch_size = 2
        ie_cfg.max_seq_len = 128
        logger.info("⚠️ Extreme Smoke Test: steps=5, bs=2, seq_len=128")

    runner = IESpanRunner(ie_cfg)

    train_ds = concatenate_datasets([data_bundle[k] for k in cfg["train_sets"]]).shuffle(seed=42)
    summaries, preds_map = runner.run(
        train_ds,
        data_bundle[cfg["dev_key"]],
        {tk: data_bundle[tk] for tk in cfg["test_sets"]},
        data_bundle["gold_info"],
        run_name=run_name,
    )
    for s in summaries:
        s["run_name"] = run_name
    return summaries, preds_map
