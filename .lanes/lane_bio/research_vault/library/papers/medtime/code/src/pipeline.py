import json
import logging
import os
import random
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from tqdm.auto import tqdm

from .config import CONFIG, GlobalConfig
from .data import save_registry
from .engine import MedTimeEngine
from .llm import UnifiedLLMClient
from .validator import AnchoredEvent, ClinicalValidator, Trajectory

logger = logging.getLogger(__name__)

# =============================================================================
# 1. 深度临床知识库 (Mega-KB)
# =============================================================================
MEGA_CLINICAL_KB = {
    "非小细胞肺癌": {
        "subtypes": ["肺腺癌 (cT2N2M0, IIIA期)", "肺鳞癌 (cT3N1M1, IV期)"],
        "discovery": ["体检CT发现磨玻璃结节(GGO)", "持续干咳伴痰中带血", "胸痛伴活动后气促"],
        "imaging": ["胸部增强CT", "头颅增强MRI", "全身PET-CT"],
        "markers": [
            {"n": "EGFR 19del", "d": "奥希替尼", "ae": "痤疮样皮疹", "lab": "CEA"},
            {"n": "ALK 融合", "d": "阿来替尼", "ae": "转氨酶升高", "lab": "CEA"},
        ],
        "lab_range": {"name": "CEA", "high": "80-120 ng/mL", "normal": "2.5-4.0 ng/mL"},
    },
    "肝细胞癌": {
        "subtypes": ["结节型HCC (BCLC B期)", "弥漫型HCC伴门脉癌栓 (BCLC C期)"],
        "discovery": ["乙肝背景定期复查发现占位", "右上腹隐痛伴皮肤黄染", "纳差、腹胀伴消瘦"],
        "imaging": ["肝脏普美显MRI", "上腹部四相CT", "肝动脉造影(DSA)"],
        "markers": [
            {"n": "AFP显著升高", "d": "仑伐替尼", "ae": "手足皮肤反应(HFS)", "lab": "AFP"},
            {"n": "PIVKA-II异常", "d": "信迪利单抗+贝伐珠单抗", "ae": "免疫性高血压", "lab": "AFP"},
        ],
        "lab_range": {"name": "AFP", "high": "1200-5000 ng/mL", "normal": "5.0-8.5 ng/mL"},
    },
    "胃腺癌": {
        "subtypes": ["胃窦部低分化腺癌", "印戒细胞癌"],
        "discovery": ["上腹部饱胀不设伴黑便", "进食梗阻感", "乏力伴重度贫血"],
        "imaging": ["超声胃镜(EUS)", "全腹部CT增强", "上消化道造影"],
        "markers": [
            {"n": "HER2 (3+)", "d": "曲妥珠单抗+SOX方案", "ae": "骨髓抑制", "lab": "CA72-4"},
            {"n": "MSI-H", "d": "帕博利珠单抗", "ae": "免疫性肠炎", "lab": "CA72-4"},
        ],
        "lab_range": {"name": "CA72-4", "high": "50-150 U/mL", "normal": "2.0-6.0 U/mL"},
    },
    "结直肠癌": {
        "subtypes": ["乙状结肠中分化腺癌 (pT3N1M0, IIIB期)", "直肠腺癌伴肝转移 (cT4N2M1, IV期)"],
        "discovery": ["大便习惯改变伴间断血便", "肠梗阻症状入院", "CEA升高体检发现"],
        "imaging": ["腹盆腔增强CT", "直肠MRI(高分辨)", "肠镜检查"],
        "markers": [
            {"n": "KRAS/NRAS/BRAF 全阴 (双原基因)", "d": "西妥昔单抗+mFOLFOX6", "ae": "皮疹", "lab": "CEA"},
            {"n": "MSI-H / dMMR", "d": "帕博利珠单抗", "ae": "免疫性结肠炎", "lab": "CEA"},
        ],
        "lab_range": {"name": "CEA", "high": "40-90 ng/mL", "normal": "2.5-5.0 ng/mL"},
    },
    "乳腺癌": {
        "subtypes": ["浸润性导管癌 (HER2阳性型)", "三阴性乳腺癌 (TNBC)", "腔面A型乳腺癌"],
        "discovery": ["无意中发现乳腺无痛性肿块", "腋窝淋巴结肿大", "钼靶体检发现微小钙化"],
        "imaging": ["乳腺远红外检查", "乳腺增强MRI", "乳房及腋窝彩超"],
        "markers": [
            {"n": "HER2 (3+)", "d": "曲妥珠单抗+帕妥珠单抗+多西他赛", "ae": "心脏毒性", "lab": "CA-153"},
            {"n": "ER(90%+) PR(80%+)", "d": "他莫昔芬", "ae": "子宫内膜增厚", "lab": "CA-153"},
        ],
        "lab_range": {"name": "CA-153", "high": "100-300 U/mL", "normal": "0-25 U/mL"},
    },
    "胰腺癌": {
        "subtypes": ["胰头导管腺癌", "胰体尾部占位"],
        "discovery": ["上腹部束带感痛伴皮肤发黄", "新发糖尿病及消瘦", "背部放射性疼痛"],
        "imaging": ["薄层胰腺CT平扫+增强", "MRCP（磁共振胰胆管造影）"],
        "markers": [
            {"n": "CA19-9极高", "d": "吉西他滨+白蛋白紫杉醇(AG)", "ae": "骨髓抑制", "lab": "CA19-9"},
            {"n": "BRCA突变", "d": "奥拉帕利", "ae": "贫血", "lab": "CA19-9"},
        ],
        "lab_range": {"name": "CA19-9", "high": "12000-45000 U/mL", "normal": "0-37 U/mL"},
    },
}


class SkeletonFactory:
    """High-density clinical skeleton generator"""

    @staticmethod
    def generate_random_lifecycle(idx: int) -> Dict:
        random.seed(GlobalConfig.SEED + idx)
        disease = random.choice(list(MEGA_CLINICAL_KB.keys()))
        kb = MEGA_CLINICAL_KB[disease]
        
        # Stochastic Time Base
        base_year = 2018 + (idx % 7)
        base_dt = datetime(base_year, (idx % 12) + 1, (idx % 28) + 1)

        m = random.choice(kb["markers"])
        lab = kb["lab_range"]
        sub = random.choice(kb["subtypes"])
        img = random.choice(kb["imaging"])

        # Decide if this is a "Survivor" or "Progressor" path
        path_type = random.choice(["Stable", "Progression"])
        
        full_steps = {
            "S1": {
                "e": f"【发现】{random.choice(kb['discovery'])}。{img}提示占位，{lab['name']}基线值为{lab['high']}。",
                "t": base_dt.strftime("%Y-%m-%d"),
                "n": "P",
            },
            "S2": {
                "e": f"【确诊】行活检病理示：{sub}。分子检测提示：{m['n']}。",
                "t": (base_dt + timedelta(days=random.randint(5, 12))).strftime("%Y-%m-%d"),
                "n": "P",
            },
            "S3": {
                "e": f"【首线】排除禁忌后，开启“{m['d']}”方案治疗。",
                "t": [
                    (base_dt + timedelta(days=random.randint(14, 21))).strftime("%Y-%m-%d"),
                    (base_dt + timedelta(days=random.randint(45, 60))).strftime("%Y-%m-%d"),
                ],
                "n": "I",
            },
        }

        if path_type == "Progression":
            # Add a second line or recurrence
            prog_date = base_dt + timedelta(days=random.randint(200, 400))
            full_steps["S4"] = {
                "e": f"【进展】随访期间复查{img}发现原发灶增大或新发转移。{lab['name']}回升至{lab['high']}。",
                "t": prog_date.strftime("%Y-%m-%d"),
                "n": "P",
            }
            full_steps["S5"] = {
                "e": f"【后续】调整治疗策略，考虑启动二线方案。",
                "t": (prog_date + timedelta(days=7)).strftime("%Y-%m-%d"),
                "n": "P",
            }

        return full_steps


class MedTimePipeline:
    def __init__(self, model_key: str = "gemini-2.5"):
        self.client = UnifiedLLMClient(model_key)
        self.validator = ClinicalValidator()

    def _get_prompts(self, task: str, lang: str = "CN"):
        specs = GlobalConfig.BILINGUAL_SPECS.get(lang, {})
        tpl = GlobalConfig.TASK_TEMPLATES.get(task, {}).get(lang, "")
        return tpl, specs

    def annotate_batch(
        self,
        db: Dict[str, Trajectory],
        registry_key: Optional[str] = None,
        lang: str = "CN",
        force_relabel: bool = False,
    ):
        """
        Batch annotation pipeline with Breakpoint Resume (断点续传).
        Skips already processed items unless force_relabel is True.
        """
        tpl, specs = self._get_prompts("PRODUCE", lang)

        # 1. Skip logic: Find pending IDs
        all_ids = list(db.keys())
        pending_ids = [tid for tid in all_ids if force_relabel or db[tid].status == "PENDING"]

        if not pending_ids:
            logger.info("✅ All items already processed. Skipping annotation.")
            return

        logger.info(f"⏳ Annotating {len(pending_ids)} pending cases...")

        # 2. Batch Processing
        batch_size = 1 # Reduced to 1 (Atomic) to strictly avoid 8k limit
        for i in tqdm(range(0, len(pending_ids), batch_size), desc="Annotating"):
            batch_ids = pending_ids[i : i + batch_size]
            batch = [db[tid] for tid in batch_ids]

            payload_blocks = []
            for t in batch:
                # [ID: ...] | [Base Date: ...] injection
                b_date = t.meta.get("base_date") or t.meta.get("publication_date") or "Unknown"
                payload_blocks.append(
                    f"### [ID: {t.id}] | [Base Date: {b_date}]\nText: {t.text}\n[审计反馈]: {t.audit_feedback or '初次执行'}"
                )

            payload = "\n\n---\n\n".join(payload_blocks)

            sys_prompt = (
                tpl.format(
                    batch_size=len(batch),
                    taxonomy=specs["taxonomy"],
                    p_i=specs["p_i"],
                    reasoning=specs["reasoning"],
                    grounding=specs["grounding"],
                    payload="",
                )
                .split("[待处理内容]")[0]
                .strip()
            )

            _, answer = self.client.request(sys_prompt, payload)
            results = MedTimeEngine.Data.safe_json_extract(answer)

            if not isinstance(results, dict):
                logger.warning(f"⚠️ Batch failed to parse ({batch_ids}). Retrying patients individually...")
                # FALLBACK: Try each patient one-by-one
                for t in batch:
                    # Single Patient Payload
                    b_date = t.meta.get("base_date") or t.meta.get("publication_date") or "Unknown"
                    indiv_payload = f"### [ID: {t.id}] | [Base Date: {b_date}]\nText: {t.text}\n[审计反馈]: {t.audit_feedback or '初次执行'}"
                    
                    sys_prompt_indiv = (
                        tpl.format(
                            batch_size=1,
                            taxonomy=specs["taxonomy"],
                            p_i=specs["p_i"],
                            reasoning=specs["reasoning"],
                            grounding=specs["grounding"],
                            payload="",
                        )
                        .split("[待处理内容]")[0]
                        .strip()
                    )
                    
                    _, indiv_answer = self.client.request(sys_prompt_indiv, indiv_payload)
                    indiv_res = MedTimeEngine.Data.safe_json_extract(indiv_answer)
                    
                    if isinstance(indiv_res, dict):
                        # The response might be {PID: [...]} or just [...]
                        raw_data = indiv_res.get(t.id) or indiv_res.get("timeline") or indiv_res
                        if isinstance(raw_data, list):
                           self._process_patient_result(t, raw_data)
                        elif isinstance(raw_data, dict) and t.id in raw_data:
                           self._process_patient_result(t, raw_data[t.id])
                    else:
                        logger.error(f"❌ Individual retry failed for {t.id}")
                
                if registry_key:
                    save_registry(registry_key, db)
                continue

            for t in batch:
                if t.id in results:
                    res = results[t.id]
                    # Robust Flattening (handle nested categories or timeline key)
                    nodes_raw = []
                    if isinstance(res, dict) and not any(k in res for k in ["e", "t", "n"]):
                        for cat, items in res.items():
                            if isinstance(items, list):
                                for item in items:
                                    if "e" not in item:
                                        item["e"] = cat
                                    nodes_raw.append(item)
                    elif isinstance(res, dict):
                        nodes_raw = res.get("timeline", [])
                    elif isinstance(res, list):
                        nodes_raw = res

                    self._process_patient_result(t, nodes_raw)

            # 3. Checkpoint Save (断点续传关键)
            if registry_key:
                save_registry(registry_key, db)

    def _process_patient_result(self, t: Trajectory, nodes_raw: List[Dict]):
        """Helper to process nodes into AnchoredEvents and update trajectory"""
        import inspect
        valid_keys = set(inspect.signature(AnchoredEvent).parameters.keys())

        events = []
        for node in nodes_raw:
            if isinstance(node, dict) and ("e" in node and "t" in node):
                # Filter out unexpected keys like 'val' that might cause TypeError
                filtered_node = {k: v for k, v in node.items() if k in valid_keys}
                try:
                    events.append(AnchoredEvent(**filtered_node))
                except Exception as e:
                    logger.warning(f"⚠️ Failed to init AnchoredEvent: {e}, Node: {node}")

        # Auto-Anchoring
        valid_events = []
        for ev in events:
            if ev.anchor_to_text(t.text):
                valid_events.append(ev)

        t.timeline = valid_events
        t.status = "AUDIT_PENDING"
        t.vr_score = ClinicalValidator.calculate_violation_rate(t.timeline)

    def synthesize_data(
        self,
        count: int,
        db: Dict[str, Trajectory],
        registry_key: Optional[str] = None,
        batch_size: int = 1, # Reduced to 1 (Atomic)
        lang: str = "CN",
    ) -> Dict[str, Trajectory]:
        """
        Synthetic data production with Multi-Sample Batching (批量合成).
        """
        tpl, specs = self._get_prompts("SYNTHESIS", lang)

        # 1. Determine starting point
        existing_syn_ids = [tid for tid in db.keys() if tid.startswith("SYN_")]
        max_idx = -1
        for tid in existing_syn_ids:
            try:
                max_idx = max(max_idx, int(tid.replace("SYN_", "")))
            except:
                pass

        start_idx = max_idx + 1
        num_to_gen = count - len(existing_syn_ids)

        if num_to_gen <= 0:
            logger.info("✅ Synthetic quota met.")
            return db

        logger.info(f"🧬 Synthesizing {num_to_gen} cases in batches of {batch_size}...")

        # 2. Batch loop
        for i in tqdm(range(start_idx, start_idx + num_to_gen, batch_size), desc="Synthesizing"):
            current_batch_ids = []
            skeletons = {}
            for j in range(i, min(i + batch_size, start_idx + num_to_gen)):
                tid = f"SYN_{j:04d}"
                skeleton = SkeletonFactory.generate_random_lifecycle(j)
                # Capture the base_date from S1 for meta-info consistency
                skeleton["_meta_anchor"] = skeleton["S1"]["t"]
                skeletons[tid] = skeleton
                current_batch_ids.append(tid)

            payload = json.dumps(skeletons, ensure_ascii=False)

            sys_prompt = (
                tpl.format(
                    batch_size=len(current_batch_ids),
                    payload="",
                )
                .strip()
            )

            _, answer = self.client.request(sys_prompt, payload)

            # --- Defense 1: Truncation Check ---
            clean_answer = answer.strip().strip("`").strip()
            is_truncated = not (clean_answer.endswith("}") or clean_answer.endswith("]"))
            if is_truncated:
                logger.error(
                    f"⚠️ Truncation detected for batch starting {i}. Attempting recovery..."
                )
                # In real scenario, we could retry with batch_size=1 here
                continue

            results = MedTimeEngine.Data.safe_json_extract(answer)
            if not isinstance(results, dict):
                logger.error(f"❌ Synthesis batch failed to parse JSON: {current_batch_ids}")
                continue

            import inspect

            valid_keys = set(inspect.signature(AnchoredEvent).parameters.keys())

            for tid in current_batch_ids:
                if tid in results:
                    data = results[tid]
                    text = MedTimeEngine.Text.clean_medical_text(data.get("text", ""))
                    raw_timeline = data.get("timeline", [])

                    # --- Defense 2: Empty/Short Text Check ---
                    if len(text) < 50:
                        logger.warning(
                            f"⚠️ SYN Case {tid} is too short ({len(text)} chars), likely failed generation."
                        )
                        continue

                    # --- Defense 2.1: Robust Event Init ---
                    events = []
                    for node in raw_timeline:
                        if isinstance(node, dict) and ("e" in node or "trigger" in node):
                            filtered_node = {k: v for k, v in node.items() if k in valid_keys}
                            events.append(AnchoredEvent(**filtered_node))

                    # --- Defense 3: Strict Anchoring (Mandatory) ---
                    valid_events = []
                    for ev in events:
                        # Synchronize cleaning to avoid anchoring failure due to header stripping
                        ev.context = MedTimeEngine.Text.clean_medical_text(ev.context)
                        ev.trigger = MedTimeEngine.Text.clean_medical_text(ev.trigger)
                        
                        success = ev.anchor_to_text(text)
                        if not success:
                            logger.info(f"🔍 DEBUG Grounding Failure for {tid}:")
                            logger.info(f"   Context: '{ev.context}'")
                            logger.info(f"   Text Sample (100): '{text[:100]}...'")
                        
                        if success:
                            valid_events.append(ev)

                    # If recall is too low compared to requested skeleton, reject
                    if len(valid_events) < 2:
                        logger.warning(
                            f"⚠️ SYN Case {tid} failed grounding (Recall {len(valid_events)}/{len(events)}). Rejected."
                        )
                        if events:
                            logger.debug(f"   First Event Context: {events[0].context}")
                            logger.debug(f"   Sample Text (50): {text[:50]}...")
                        continue

                    # --- Defense 4: Logical Consistency Gating ---
                    vr = ClinicalValidator.calculate_violation_rate(valid_events)
                    if vr > 0.4:  # Allow small noise, but not total mess
                        logger.warning(
                            f"⚠️ SYN Case {tid} has high Violation Rate ({vr:.2f}). Rejected."
                        )
                        continue

                    db[tid] = Trajectory(
                        id=tid,
                        text=text,
                        meta={
                            "disease": "Synthetic",
                            "audit_notes": data.get("audit_notes", "Implicit Fix"), # Default fallback
                            "base_date": skeletons[tid].get("_meta_anchor"),
                        },
                        timeline=valid_events,
                        status="CERTIFIED",
                        vr_score=vr,
                    )

            # 3. Save after each batch
            if registry_key:
                save_registry(registry_key, db)

        return db

    def audit_batch(
        self, db: Dict[str, Trajectory], registry_key: Optional[str] = None, lang: str = "CN"
    ):
        """
        Automated Auditor Pipeline with Breakpoint Resume.
        Only audits items that are AUDIT_PENDING.
        """
        tpl, specs = self._get_prompts("AUDIT", lang)

        pending_ids = [tid for tid in db.keys() if db[tid].status == "AUDIT_PENDING"]
        if not pending_ids:
            logger.info("✅ No items awaiting audit.")
            return

        logger.info(f"🔎 Auditing {len(pending_ids)} cases...")

        batch_size = 10
        for i in tqdm(range(0, len(pending_ids), batch_size), desc="Auditing"):
            batch_ids = pending_ids[i : i + batch_size]
            batch = [db[tid] for tid in batch_ids]

            payload_data = {t.id: [ev.to_dict() for ev in t.timeline] for t in batch}
            payload = json.dumps(payload_data, ensure_ascii=False)

            # Prepare system prompt (fill placeholders but remove payload section)
            cleanup_kw = "[数据批次]" if "[数据批次]" in tpl else "[Rubric]"
            sys_prompt = tpl.format(
                batch_size=len(batch_ids),
                audit=specs["audit"],
                payload=""
            ).split(cleanup_kw)[0].strip()

            _, answer = self.client.request(sys_prompt, payload)
            results = MedTimeEngine.Data.safe_json_extract(answer)

            if not isinstance(results, dict):
                logger.error(f"❌ Batch failed to parse: {batch_ids}")
                continue

            for t in batch:
                if t.id in results:
                    audit_res = results[t.id]
                    t.score = audit_res.get("score", 0)
                    t.audit_feedback = audit_res.get("feedback", "")
                    t.status = audit_res.get("status", "CERTIFIED" if t.score >= 80 else "FAILED")

            if registry_key:
                save_registry(registry_key, db)

    def refine_temporal_batch(
        self, db: Dict[str, Trajectory], registry_key: Optional[str] = None, lang: str = "CN"
    ):
        """
        LLM-based Temporal Refinement. 
        Target nodes with fuzzy dates (e.g. -XX, Unknown, Relative).
        """
        tpl, specs = self._get_prompts("REFINE_TEMPORAL", lang)
        iso_p = re.compile(r"^\d{4}-\d{2}(-\d{2})?$")

        # 1. Identify patients needing refinement
        target_ids = []
        for tid, t in db.items():
            needs_refinement = False
            for ev in t.timeline:
                dates = ev.t if isinstance(ev.t, list) else [ev.t]
                for d in dates:
                    if d and (not isinstance(d, str) or not iso_p.match(d)):
                        needs_refinement = True
                        break
                if needs_refinement: break
            if needs_refinement:
                target_ids.append(tid)

        if not target_ids:
            logger.info("✅ No fuzzy dates found. Skipping temporal refinement.")
            return

        logger.info(f"⏳ Refining temporal data for {len(target_ids)} cases...")

        # 2. Batch Processing
        batch_size = 5
        for i in tqdm(range(0, len(target_ids), batch_size), desc="Refining Time"):
            batch_ids = target_ids[i : i + batch_size]
            batch = [db[tid] for tid in batch_ids]

            payload_blocks = []
            for t in batch:
                b_date = t.meta.get("base_date") or t.meta.get("publication_date") or "Unknown"
                tl_data = [ev.to_dict() for ev in t.timeline]
                payload_blocks.append(
                    f"### [ID: {t.id}] | [Base Date: {b_date}]\n[Current Timeline]: {json.dumps(tl_data, ensure_ascii=False)}"
                )

            payload = "\n\n---\n\n".join(payload_blocks)
            cleanup_kw = "[待处理内容]" if "[待处理内容]" in tpl else "[Task]"
            sys_prompt = tpl.format(
                batch_size=len(batch),
                payload="",
            ).split(cleanup_kw)[0].strip()

            _, answer = self.client.request(sys_prompt, payload)
            results = MedTimeEngine.Data.safe_json_extract(answer)

            if not isinstance(results, dict):
                logger.warning(f"⚠️ Refinement batch failed to parse ({batch_ids}). Retrying patients individually...")
                for t in batch:
                    b_date = t.meta.get("base_date") or t.meta.get("publication_date") or "Unknown"
                    tl_data = [ev.to_dict() for ev in t.timeline]
                    indiv_payload = f"### [ID: {t.id}] | [Base Date: {b_date}]\n[Current Timeline]: {json.dumps(tl_data, ensure_ascii=False)}"
                    
                    cleanup_kw = "[待处理内容]" if "[待处理内容]" in tpl else "[Task]"
                    sys_prompt_indiv = tpl.format(
                        batch_size=1, 
                        payload=""
                    ).split(cleanup_kw)[0].strip()
                    _, indiv_answer = self.client.request(sys_prompt_indiv, indiv_payload)
                    indiv_res = MedTimeEngine.Data.safe_json_extract(indiv_answer)
                    
                    if isinstance(indiv_res, dict):
                        raw_data = indiv_res.get(t.id) or indiv_res.get("timeline") or indiv_res
                        if isinstance(raw_data, list):
                            self._process_refinement_result(t, raw_data)
                    else:
                        logger.error(f"❌ Individual refinement failed for {t.id}")
                
                if registry_key:
                    save_registry(registry_key, db)
                continue

            for t in batch:
                if t.id in results:
                    batch_res = results[t.id]
                    if isinstance(batch_res, list):
                        self._process_refinement_result(t, batch_res)
            
            if registry_key:
                save_registry(registry_key, db)

    def _process_refinement_result(self, t: Trajectory, batch_res: List[Dict]):
        """Helper to process refined nodes into AnchoredEvents."""
        import inspect

        valid_keys = set(inspect.signature(AnchoredEvent).parameters.keys())
        new_events = []
        for node in batch_res:
            if isinstance(node, dict) and ("e" in node and "t" in node):
                filtered_node = {k: v for k, v in node.items() if k in valid_keys}
                try:
                    ev = AnchoredEvent(**filtered_node)
                    if ev.anchor_to_text(t.text):
                        new_events.append(ev)
                except Exception as e:
                    logger.warning(f"⚠️ Failed to init refined event: {e}, Node: {node}")

        if len(new_events) >= len(t.timeline) - 2:
            t.timeline = new_events
            t.vr_score = ClinicalValidator.calculate_violation_rate(t.timeline)


