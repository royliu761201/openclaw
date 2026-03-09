import json
import logging
import os
import sys
import time
print(f"DEBUG EVALUATOR LOADING FROM: {__file__}")
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
print(f"DEBUG NUMPY: {np}")



from rapidfuzz import fuzz
from transformers import TrainerCallback

from .config import ENV, GlobalConfig
from .engine import MedTimeEngine

logger = logging.getLogger(__name__)





class MedTimeCallback(TrainerCallback):
    """Optimized Callback for Metrics Cache and Plotting"""

    def __init__(self):
        super().__init__()
        self.plot_id = None
        self.metrics_cache = {}

    def on_train_begin(self, args, state, control, **kwargs):
        self.plot_id = f"plot_{args.run_name}_{int(time.time())}"
        print(f"🚀 Experiment Start: {args.run_name} | Max Steps: {state.max_steps}")

    def on_evaluate(self, args, state, control, metrics=None, **kwargs):
        """Log main evaluation metrics to W&B and print summary"""
        if metrics:
            target_metrics = {
                "eval/Temporal_F1": metrics.get("eval_Temporal_F1"),
                "eval/Trigger_F1": metrics.get("eval_Trigger_F1"),
                "eval/MAE_Days": metrics.get("eval_MAE_Days"),
                "eval/CMC": metrics.get("eval_CMC"),
                "eval/TED": metrics.get("eval_TED"),
            }
            # Remove None values
            target_metrics = {k: v for k, v in target_metrics.items() if v is not None}

            if target_metrics:
                logger.info(f"📊 Eval Metrics: {target_metrics}")
                if args.report_to and "wandb" in args.report_to:
                    import wandb

                    wandb.log(target_metrics, step=state.global_step)

    def on_log(self, args, state, control, logs=None, **kwargs):
        # 1. Cache specific metrics
        target_keys = ["mse_loss", "topo_loss", "ground_loss", "lm_loss", "latent_vr"]
        for k in target_keys:
            if k in logs:
                self.metrics_cache[k] = logs[k]

        # 2. Print and visualize
        if ("loss" in logs or "mse_loss" in logs) and state.global_step > 0:
            step = state.global_step
            loss = logs.get("loss") or logs.get(
                "mse_loss", 0
            )  # Fallback if only custom loss logged

            mse = self.metrics_cache.get("mse_loss", 0)
            topo = self.metrics_cache.get("topo_loss", 0)
            ground = self.metrics_cache.get("ground_loss", 0)
            lm = self.metrics_cache.get("lm_loss", 0)
            vr = self.metrics_cache.get("latent_vr", 0)

            report_msg = (
                f"Step {step:4d}/{state.max_steps} | "
                f"Total: {loss:.4f} | "
                f"MSE: {mse:.4f} | "
                f"Topo: {topo:.4f} | "
                f"Ground: {ground:.4f} | "
                f"LM: {lm:.4f} | "
                f"VR: {vr:.4f}"
            )

            logger.info(f"[TRAIN] {report_msg}")


class MedTimeEvaluator:
    @classmethod
    def calculate_node_similarity(cls, gold_node, pred_node):
        """
        3D Alignment Algorithm:
        1. Physical: Coordinate overlapping
        2. Trigger: Core term matching
        3. Semantic: Description fuzzy matching
        """
        # --- Dim 1: Physical Overlap ---
        g_s, g_e = gold_node.get("start", -1), gold_node.get("end", -1)
        p_s, p_e = pred_node.get("start", -1), pred_node.get("end", -1)

        if g_s != -1 and p_s != -1:
            overlap = max(0, min(g_e, p_e) - max(g_s, p_s))
            if overlap > 0:
                return 1.0

        # --- Dim 2: Trigger Match ---
        g_trig = str(gold_node.get("trigger", "")).strip().lower()
        p_trig = str(pred_node.get("trigger", "")).strip().lower()

        if g_trig and p_trig:
            if g_trig == p_trig or g_trig in p_trig or p_trig in g_trig:
                return 0.95

        # --- Dim 3: Semantic Fuzzy Match ---
        return fuzz.partial_ratio(gold_node.get("e", ""), pred_node.get("e", "")) / 100.0

    @classmethod
    def evaluate_single(cls, gold_timeline, pred_timeline):
        g_clean = MedTimeEngine.Data.auto_fix_timeline(gold_timeline)
        p_clean = MedTimeEngine.Data.auto_fix_timeline(pred_timeline)

        if not p_clean:
            return {
                "Temporal_F1": 0.0,
                "Trigger_F1": 0.0,
                "MAE_Days": 90.0,
                "Violation_Rate": 0.0,
                "TED": 1.0,
                "count": 1,
            }

        # --- 1. Trigger Match ---
        tp_trig = 0
        gold_matched_trig = [False] * len(g_clean)
        for p_item in p_clean:
            for g_idx, g_item in enumerate(g_clean):
                if not gold_matched_trig[g_idx]:
                    if cls.calculate_node_similarity(g_item, p_item) >= 0.8:
                        tp_trig += 1
                        gold_matched_trig[g_idx] = True
                        break

        # --- 2. Temporal Match ---
        tp_temp = 0
        mae_errors = []
        gold_matched_temp = [False] * len(g_clean)
        for p_item in p_clean:
            best_sim, best_idx = 0, -1
            for g_idx, g_item in enumerate(g_clean):
                if not gold_matched_temp[g_idx]:
                    sim = cls.calculate_node_similarity(g_item, p_item)
                    if sim > 0.3 and sim > best_sim:
                        best_sim, best_idx = sim, g_idx

            if best_idx != -1:
                ts_g = MedTimeEngine.Temporal.to_timestamp(g_clean[best_idx].get("t"))
                ts_p = MedTimeEngine.Temporal.to_timestamp(p_item.get("t"))
                if ts_g == ts_p:
                    tp_temp += 1
                    gold_matched_temp[best_idx] = True
                if ts_g and ts_p:
                    # Convert seconds to days
                    mae_errors.append(abs(ts_g - ts_p) / 86400.0)


        def f1_func(tp, plen, glen):
            p = tp / plen if plen > 0 else 0
            r = tp / glen if glen > 0 else 0
            return 2 * p * r / (p + r + 1e-6)

        ted_score = cls.calculate_ted(g_clean, p_clean)

        return {
            "Temporal_F1": round(f1_func(tp_temp, len(p_clean), len(g_clean)), 4),
            "Trigger_F1": round(f1_func(tp_trig, len(p_clean), len(g_clean)), 4),
            "MAE_Days": round(np.mean(mae_errors) if mae_errors else 90.0, 2),
            "CMC": round(MedTimeEngine.Data.calculate_cmc(p_clean), 4),
            "TED": round(ted_score, 4),
            "count": 1,
        }

    @staticmethod
    def calculate_ted(gold: List[Dict], pred: List[Dict]) -> float:
        """
        Weighted Timeline Edit Distance (TED)
        Cost = Semantic_Dist + Log_Time_Penalty
        """
        if not gold and not pred:
            return 0.0
        if not gold:
            return 1.0
        if not pred:
            return 1.0

        n, m = len(gold), len(pred)
        dp = [[0.0] * (m + 1) for _ in range(n + 1)]
        for i in range(n + 1):
            dp[i][0] = float(i)
        for j in range(m + 1):
            dp[0][j] = float(j)

        for i in range(1, n + 1):
            for j in range(1, m + 1):
                g_item, p_item = gold[i - 1], pred[j - 1]
                
                # 1. Semantic Distance (0~1)
                # "确诊" vs "诊断" -> sim=0.9 -> dist=0.1
                sim_text = fuzz.partial_ratio(g_item.get("e", ""), p_item.get("e", "")) / 100.0
                dist_text = 1.0 - sim_text
                
                # 2. Time Penalty (Log Scale)
                # Diff=0 -> 0; Diff=365 -> log(366) ~ 5.9
                t_g = MedTimeEngine.Temporal.to_timestamp(g_item.get("t"))
                t_p = MedTimeEngine.Temporal.to_timestamp(p_item.get("t"))
                
                dist_time = 1.0 # Default penalty if one is missing
                if t_g is not None and t_p is not None:
                    # Normalize: log(1 + days) / log(1 + 365*10) to keep roughly 0~1 range for reasonable errors
                    diff_days = abs(t_g - t_p)
                    dist_time = np.log1p(diff_days) / np.log1p(3650) 
                    dist_time = min(1.0, dist_time)

                # Weighted Cost
                # Alpha (Text): 0.6, Beta (Time): 0.4
                cost = 0.6 * dist_text + 0.4 * dist_time
                
                dp[i][j] = min(dp[i - 1][j] + 1,       # Deletion
                               dp[i][j - 1] + 1,       # Insertion
                               dp[i - 1][j - 1] + cost) # Substitution

        return dp[n][m] / max(n, m)

    @staticmethod
    def summarize(results_list):
        if not results_list:
            return {}
        df = pd.DataFrame(results_list)
        # Select numeric columns for mean
        summary = {
            "Temporal_F1": df["Temporal_F1"].mean(),
            "Trigger_F1": df["Trigger_F1"].mean(),
            "MAE_Days": df["MAE_Days"].mean(),
            "CMC": df["CMC"].mean(),
            "TED": df["TED"].mean(),
            "count": len(df),
        }
        return {k: round(v, 4) for k, v in summary.items()}

    @classmethod
    def calculate_all(cls, gold_ref_list, preds_map):
        metrics = []
        for item in gold_ref_list:
            pid = item["pid"]
            gold_obj = item["gold_obj"]
            pred_obj = preds_map.get(pid, [])
            res = cls.evaluate_single(gold_obj, pred_obj)
            res["pid"] = pid
            metrics.append(res)
        return metrics



