import json
import logging
import os
import random
from typing import Dict, List
try:
    import gdown
except ImportError:
    gdown = None

from datasets import Dataset

from .config import CONFIG, ENV, GlobalConfig
from .engine import MedTimeEngine

logger = logging.getLogger(__name__)


from .validator import AnchoredEvent, Trajectory


def load_registry(key: str) -> Dict[str, Trajectory]:
    """Load registry from local data directory"""
    catalog = GlobalConfig.DATA_CATALOG.get(key)
    if not catalog:
        logger.warning(f"Task key {key} not found in DATA_CATALOG.")
        return {}

    path = ENV.data_dir / catalog.get("dir", "medtime") / catalog["local_path"]
    logger.info(f"🔍 Checking registry path: {path.absolute()}")

    # [JAN 24 PATCH] Disable GDrive sync to prevent blocking on server
    if not path.exists():
        logger.error(f"❌ Critical Error: Registry {key} missing at {path}. GDrive sync disabled for stability.")
        return {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            raw_db = json.load(f)

        db = {}
        for tid, data in raw_db.items():
            db[tid] = Trajectory.from_registry(tid, data)
        return db
    except Exception as e:
        logger.error(f"Failed to load registry {key}: {e}")
        return {}


def save_registry(key: str, db: Dict[str, Trajectory]):
    """Save registry back to local data directory"""
    catalog = GlobalConfig.DATA_CATALOG.get(key)
    if not catalog:
        return

    path = ENV.data_dir / catalog.get("dir", "medtime") / catalog["local_path"]
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        output = {tid: traj.to_registry() for tid, traj in db.items()}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        logger.info(f"💾 Registry {key} saved to {path}")
    except Exception as e:
        logger.error(f"Failed to save registry {key}: {e}")


def load_and_standardize_data(task_key: str):
    """
    Load data from registry and standardize for MedTime training.
    """
    logger.info(f"🚀 Loading and standardizing {task_key}...")
    db = load_registry(task_key)

    # Filter for Certified if needed, or just return all
    # For now, we return a list of simplified dicts for Dataset conversion
    standardized = []
    for tid, traj in db.items():
        # Standardize using engine if needed
        traj.vr_score = MedTimeEngine.Data.calculate_violation_rate(
            [n.to_dict() for n in traj.timeline]
        )

        standardized.append(
            {
                "pid": tid,
                "text": traj.text,
                "timeline": [n.to_dict() for n in traj.timeline],
                "vr_score": traj.vr_score,
                "meta": traj.meta,
            }
        )

    return standardized, db


def prepare_atomic_datasets(seed=42):
    """
    Build atomic datasets from registry (MedTime v22 Logic)
    """
    rng = random.Random(seed)
    # 1. Load Real Data
    med_raw, med_db = load_and_standardize_data("medtime")
    syn_raw, syn_db = load_and_standardize_data("synthetic")
    e3c_raw, e3c_db = load_and_standardize_data("e3c")


    # 2. Conversion helper
    def to_ds(raw_list, lang="CN"):
        ds_items = []
        for r in raw_list:
            # Extract basic fields
            pid = r["pid"]
            text = r["text"]
            tl = r["timeline"]
            
            # Map coords for GVP
            coords = [[n.get("start", -1), n.get("end", -1)] for n in tl]
            
            # Target output (Full MedTime Schema)
            gvp_label = []
            for n in tl:
                node = {
                    "trigger": n.get("trigger", ""),
                    "e": n["e"],
                    "t": n["t"],
                    "n": n.get("n", "P")
                }
                # Optional fields for reasoning and grounding
                if n.get("r"): node["r"] = n["r"]
                if n.get("context"): node["context"] = n["context"]
                gvp_label.append(node)
            
            # [FIX] Inject Anchor Date into Input for Time Resolution
            anchor_dt = MedTimeEngine.Temporal.parse_meta_date(r["meta"])
            anchor_str = f"[Ref: {anchor_dt.strftime('%Y-%m-%d')}] " if anchor_dt else ""
            final_input = anchor_str + text

            item = {
                "pid": pid,
                "instruction": GlobalConfig.SYSTEM_PROMPTS[lang],
                "input": final_input,
                "output": json.dumps(gvp_label, ensure_ascii=False, separators=(",", ":")),
                "coords": coords,
                "meta": json.dumps({"raw_timeline": tl, "meta_info": r["meta"]}, ensure_ascii=False, separators=(",", ":"))
            }
            ds_items.append(item)
        return Dataset.from_list(ds_items)

    # 3. Create Splits (Synthetic as primary training foundation)
    syn_list = list(syn_raw)
    rng.shuffle(syn_list)
    n_total = len(syn_list)
    n_train = int(n_total * 0.8)
    n_dev = int(n_total * 0.1)

    # 4. Create Bundle
    bundle = {
        "syn_train": to_ds(syn_list[:n_train], "CN"),
        "syn_dev": to_ds(syn_list[n_train:n_train+n_dev], "CN"),
        "syn_test": to_ds(syn_list[n_train+n_dev:], "CN"),
        
        "med_few": to_ds(med_raw[:GlobalConfig.SPLIT_PARAMS["med_few_shot_n"]], "CN"),
        "med_dev": to_ds(med_raw[GlobalConfig.SPLIT_PARAMS["med_few_shot_n"]:GlobalConfig.SPLIT_PARAMS["med_few_shot_n"]+GlobalConfig.SPLIT_PARAMS["med_val_n"]], "CN"),
        # [FIX] Data Leakage: Ensure test set excludes training and validation examples
        "med_test": to_ds(med_raw[GlobalConfig.SPLIT_PARAMS["med_few_shot_n"]+GlobalConfig.SPLIT_PARAMS["med_val_n"]:], "CN"),
        
        # [NEW] English Few-Shot Split (N=12) for Baseline Repair
        "e3c_few": to_ds(e3c_raw[:GlobalConfig.SPLIT_PARAMS["med_few_shot_n"]], "EN"),
        
        "e3c_train": to_ds(e3c_raw[:int(len(e3c_raw)*0.7)], "EN"),
        "e3c_dev": to_ds(e3c_raw[int(len(e3c_raw)*0.7):int(len(e3c_raw)*0.85)], "EN"),
        "e3c_test": to_ds(e3c_raw[int(len(e3c_raw)*0.85):], "EN"),



        "gold_info": {},
        "hard_ids": set()
    }

    # 5. Build Global Gold Info & Hard IDs
    for d_raw, p_key in [(med_raw, "cn"), (syn_raw, "cn"), (e3c_raw, "en")]:
        for r in d_raw:
            pid = r["pid"]
            bundle["gold_info"][pid] = {"timeline": r["timeline"]}
            
            # Identify Hard Cases from metadata (rectification_notes, audit_feedback)
            meta = r["meta"]
            fb = str(meta.get("audit_feedback", "")).lower()
            rn = str(meta.get("rectification_notes", "")).lower()
            
            if any(k in fb or k in rn for k in ["非线性", "倒叙", "修正", "logic", "error", "hallucination", "adversarial"]):
                bundle["hard_ids"].add(pid)

    logger.info(f"✅ Atomic datasets ready: {len(bundle['syn_train'])} Syn Train, {len(bundle['med_test'])} Med Test.")
    return bundle
