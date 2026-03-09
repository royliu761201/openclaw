import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

from common.env import ProjectEnv, load_secret


# Helper for robust boolean parsing
def str_to_bool(val: Any) -> bool:
    """Robustly convert string/int to boolean (Safe Default: False)"""
    if isinstance(val, bool): return val
    if not val: return False
    return str(val).lower() in ("true", "1", "yes", "on", "y")

@dataclass
class MedTimeConfig:
    """
    MedTime Logic Model Configuration
    """

    # Keys / Secrets (Loaded from Env or Local File)
    google_api_key: Optional[str] = field(default_factory=lambda: load_secret("GOOGLE_API_KEY"))
    groq_api_key: Optional[str] = field(default_factory=lambda: load_secret("GROQ_API_KEY"))
    hf_token: Optional[str] = field(default_factory=lambda: load_secret("HF_TOKEN"))
    wandb_api_key: Optional[str] = field(default_factory=lambda: load_secret("WANDB_API_KEY"))

    # Model Architecture
    base_model: str = field(default_factory=lambda: (
        "/jhdx0003008/models/Qwen2.5-14B-Instruct" 
        if os.path.exists("/jhdx0003008/models/Qwen2.5-14B-Instruct") 
        else "Qwen/Qwen2.5-14B-Instruct"
    ))
    max_seq_len: int = 4096


    # Training Params
    learning_rate: float = 1e-4 # [STABILITY] Reduced for 32B stability
    batch_size: int = 4 # [MAX] Increased from 2 for better L20 utilization
    grad_accumulation: int = 4 # Effective BS = 16 (4x4)
    max_steps: int = 250 # More steps for the larger model
    inference_batch_size: int = 4 # [SAFE] Reduced from 8 for 32B stability
    max_drift_days: int = 365 

    # 🚀 实验跟踪 (W&B)
    use_wandb: bool = True
    wandb_project: str = field(default_factory=lambda: os.getenv("WANDB_PROJECT", "medtime"))

    # LoRA Params
    lora_r: int = 16
    lora_alpha: int = 16
    lora_dropout: float = 0.0

    # Staged Training (Curriculum)
    staged_training: bool = False
    warmup_epochs: int = 2
    final_lambda: float = 0.5 

    # Judge Params
    judge_model: str = "gemini-1.5-pro-latest" # User requested 'gemini-3', mapping to latest Pro
    judge_temperature: float = 0.0

    # [SAFETY] Explicitly Default to Production Mode (False)
    smoke_test: bool = field(default_factory=lambda: str_to_bool(os.getenv("SMOKE_TEST", "False")))
    inference_only: bool = field(default_factory=lambda: str_to_bool(os.getenv("INFERENCE_ONLY", "False")))


# Initialize Environment & Config
ENV = ProjectEnv.detect()
CONFIG = MedTimeConfig()


class GlobalConfig:
    """
    Central Configuration Hub
    """

    VERSION = "MedTime"
    SEED = 42  # For reproducible random generation

    # Path shortcuts
    PROD_DIR = str(ENV.output_dir)
    LOG_DIR = str(ENV.output_dir / "logs")
    EXP_ROOT = str(ENV.output_dir / "experiment_artifacts")

    # Constants
    MAX_SEQ_LEN = CONFIG.max_seq_len
    MODEL_CONFIG = {
        "name": CONFIG.base_model,
        "max_seq_len": CONFIG.max_seq_len,
        "load_in_4bit": True,
        "lora_r": CONFIG.lora_r,
        "lora_alpha": CONFIG.lora_alpha,
    }

    DATA_CATALOG = {
        "medtime": {
            "name": "MedTime-Real-CN",
            "drive_id": "1lcHpMJYkD7sS362ikZ6Md7jcuChTJsrz",
            "local_path": "registry_medtime_real.json",
            "pass_score": 90,
            "field_map": {
                "id": ["id"],
                "timeline": ["timeline"],
                "text": ["text"],
                "feedback": ["audit_feedback"],
            },
        },
        "synthetic": {
            "name": "MedTime-Synthetic",
            "drive_id": "1SKe2af65wluScXiOV0RZGZcC7IS_mrzh",
            "local_path": "registry_medtime_synthetic.json",
            "pass_score": 90,
            "field_map": {
                "id": ["id"],
                "timeline": ["timeline"],
                "text": ["text"],
                "feedback": ["audit_feedback"],
            },
        },
        "e3c": {
            "name": "MedTime-E3C-EN",
            "dir": "medtime",
            "drive_id": "1hAkZWU09OtPyskK2qnGAtp9GUDCo1rvf",
            "local_path": "registry_e3c_english.json",
            "pass_score": 90,
            "field_map": {
                "id": ["id"],
                "timeline": ["timeline"],
                "text": ["text"],
                "feedback": ["audit_feedback"],
            },
        },
    }


    LOGIC_KEYWORDS = {
        "correction": ["修正", "纠正", "识别并", "corrected", "logic error", "misapplied"],
        "nonlinear": ["非线性", "倒叙", "插叙", "nonlinear", "adversarial", "scrambled"],
    }

    SYSTEM_PROMPTS = {
        "CN": """# Role
你是一名肿瘤专科医生，负责阅读病程记录并抽取关键事件，整理为标准化的时间轴 JSON 数组。

# Output Format (ONLY JSON Array)
[
  {
    "trigger": "原文中的核心动词/名词，如'手术'、'化疗'、'复查'、'转移'",
    "e": "事件的简要描述，中文，20字以内",
    "t": "时间字段：'YYYY-MM-DD'、'YYYY-MM'、['开始时间','结束时间'] 或 null",
    "n": "类型标记：'P'(点事件) 或 'I'(区间事件)"
  }
]

# Constraints
1. 仅根据原文内容抽取，严禁杜撰任何未提及的事件或日期。
2. 事件必须严格按照时间顺序（从早到晚）排列。
3. 如果年份不详但文中提供“术后两周”等信息，请结合背景进行推算。
4. 无法确定任何时间信息时，"t" 设为 null。
5. 【绝对约束】：只输出合法的 JSON 数组，严禁输出任何解释、开场白或额外说明文字。""",
        "EN": """# Role
You are an oncology expert. Extract clinical events from narratives into a standardized timeline JSON array.

# Output Format (ONLY JSON Array)
[
  {
    "trigger": "Core clinical term from text, e.g., 'Surgery', 'CT', 'Biopsy'",
    "e": "Short description of the event in English, within 20 words",
    "t": "Time: 'YYYY-MM-DD', 'YYYY-MM', ['start_time','end_time'], or null",
    "n": "Type: 'P'(Point event) or 'I'(Interval event)"
  }
]

# Constraints
1. Extract based ONLY on the provided text. Do NOT hallucinate.
2. Events MUST be ordered chronologically from earliest to latest.
3. Use 'YYYY-MM' for incomplete dates and null if no time can be determined.
4. If only relative time is given (e.g., '2 weeks post-op'), infer the absolute date based on context.
5. 【Strict Constraint】: Output ONLY a valid JSON array. No preamble, no explanation, no extra text.""",
    }
    # --- 🎨 统一指令资产库与进化基因 ---
    BILINGUAL_SPECS = {
        "CN": {
            "taxonomy": "DX:诊断, TX:治疗, IX:评估, SX:进展",
            "p_i": "性质 n: 'P'(点/瞬时), 'I'(区间/过程)。时间 t: n=P为字符串'YYYY-MM-DD', n=I为列表['始', '止']。",
            "reasoning": "推理 r: 描述推导逻辑桥梁。支持：相对计算(入院+3d)、常规映射(3月中旬->03-15)、逻辑追溯、原文直录。",
            "grounding": "原文锚定约束: context 必须是原文【逐字摘录】(15-25字)。严禁改动任何标点。trigger 是核心临床词汇。",
            "audit": "1.文本锚定真实性(40%): 摘录是否逐字匹配？ 2.推理逻辑桥梁(30%): r是否能合理解释t？ 3.属性事实精度(30%)",
        },
        "EN": {
            "taxonomy": "DX: Diagnosis, TX: Treatment, IX: Assessment, SX: Progression",
            "p_i": "Nature 'n': 'P' (Point), 'I' (Interval). Time 't': n=P is string, n=I is list.",
            "reasoning": "Reasoning 'r': Logical bridge. Supports: Relative math, Convention, Traceback, Direct record.",
            "grounding": "Verbatim Grounding: context MUST be a 100% literal snippet from raw text (15-25 words). trigger is the core clinical term. No paraphrasing.",
            "audit": "1.Grounding(40%) 2.Logic(30%) 3.Fidelity(30%)",
        },
    }

    TASK_TEMPLATES = {
        "PRODUCE": {
            "CN": """你是一位顶级的肿瘤临床数据审计专家。
[任务] 为以下 {batch_size} 个病例重构 P-I 时间轴。你必须参考【审计反馈】针对性修正之前的错误。
[规范] {taxonomy} | {p_i} | {reasoning}
[锚定] {grounding}
[输出格式] 严格 JSON 字典，PID 为键:
{{ "PID": [ {{ "e": "描述", "t": "时间", "n": "P/I", "r": "推理过程", "trigger": "核心词", "context": "原文一致摘录" }} ] }}
[待处理内容]
{payload}""",
            "EN": """You are an Expert clinical data auditor. 
[Task] Reconstruct P-I Timelines for {batch_size} cases. 
[Specs] {taxonomy} | {p_i} | {reasoning}
[Grounding] {grounding}
[Format] Strict JSON object with PIDs as keys:
{{ "PID": [ {{ "e": "Description", "t": "Time", "n": "P/I", "r": "Reasoning", "trigger": "Core Term", "context": "Verbatim Snippet" }} ] }}
[Payload]
{payload}""",
        },
        "SYNTHESIS": {
            "CN": """你是一位精通肿瘤临床逻辑的首席医师。
[任务] 基于 {batch_size} 份【逻辑骨架】, 扩写为全量非线性临床病历，并提取时间轴。

[核心指令]
1. **隐式纠偏**: 若骨架有逻辑错误（如日期倒置），直接在扩写时修正，**无需**输出修正说明。
2. **文体仿真**: 随机采用“出院小结”、“查房记录”或“会诊单”风格。
3. **高阶叙事**: 强制使用倒叙/插叙（如先写当前疗效，再回顾确诊）。
4. **全量召回**: 提取病历中所有时间节点（含你修正或补全的）。

[提取规范]
- `e`: 精炼医学事件（如：开始二线化疗）。
- `context`: 【逐字摘录】包含 trigger 的原文句子（15-25字），严禁改动。
- `trigger`: 必须包含在 context 内。

[输出格式] 严格 JSON 字典, PID 为键。
{{
  "PID": {{
    "text": "生成的完整、非线性临床文本...",
    "timeline": [ {{ "e": "...", "t": "YYYY-MM-DD", "n": "P/I", "trigger": "...", "context": "..." }} ]
  }}
}}

[待处理载荷]
{payload}""",
            "EN": """You are a Senior Oncologist.
[Task] Synthesize {batch_size} high-fidelity, non-linear clinical reports based on skeletons.

[Core Instructions]
1. **Implicit Fix**: Correct any skeleton errors (e.g., date reversals) directly in the text. Do NOT output notes.
2. **Style**: Use Discharge Summaries or Consultation Notes.
3. **Narrative**: Use flashbacks/non-linear flow.
4. **Recall**: Extract ALL temporal events mentioned in your text.

[Extraction Specs]
- `e`: Concise event summary.
- `context`: Verbatim snippet from text (15-25 words).
- `trigger`: Must be inside context.

[Format] Strict JSON with PIDs as keys.
{{
  "PID": {{
    "text": "Generated clinical text...",
    "timeline": [ {{ "e": "...", "t": "YYYY-MM-DD", "n": "P/I", "trigger": "...", "context": "..." }} ]
  }}
}}
{payload}""",
        },
        "AUDIT": {
            "CN": """你是一位严苛的科研审计员。批量评分 (0-100)。
[审计准则] {audit}
[输出格式] 严格 JSON 字典，PID 为键:
{{ "PID": {{ "score": 0-100, "feedback": "描述错误点", "status": "CERTIFIED/FAILED" }} }}
[数据批次]
{payload}""",
            "EN": """You are a rigorous auditor. Score {batch_size} cases.
[Rubric] {audit}
[Output] JSON with PIDs as keys.
{payload}""",
        },
        "REFINE_TEMPORAL": {
            "CN": """你是一位临床数据标准化平衡专家。
[任务] 为以下 {batch_size} 个病例规格化时间轴。
[核心目标] 将模糊或相对的时间(如 '2021-10-XX', '现', '未知', '1周前') 转化为标准 ISO 格式 (YYYY-MM-DD 或 YYYY-MM)。

[逻辑准则]
1. **硬约束 (Base Date)**: 你必须参考每个病例提供的 `[Base Date: YYYY-MM-DD]` 进行推导。
2. **中值补全**: 若只有年份月份(如 2021-10-XX)，在无其他证据时补全为 15 日。
3. **时序保序**: 补全后的日期必须保持临床逻辑上的先后顺序，严禁发生穿越。
4. **语义解析**: "现" 通常对应 Base Date 的月份或具体日期。"前" 需根据 Base Date 进行减法演算。

[输出格式] 严格 JSON 字典，PID 为键，返回**全量且规格化后**的时间轴:
{{ "PID": [ {{ "e": "描述", "t": "YYYY-MM-DD", "n": "P/I", "r": "由于[基准日期]+[逻辑]..." }} ] }}
[待处理内容]
{payload}""",
            "EN": """You are a Clinical Data Standardization Expert.
[Task] Standardize fuzzy/relative dates (e.g., '2021-10-XX', 'Now', 'Unknown', '1w ago') into ISO formats (YYYY-MM-DD).
[Rules] Use [Base Date] as anchor. Ensure chronological sequence. Use midpoint for -XX dates.
[Format] Strict JSON object with PIDs as keys, returning updated timelines:
{{ "PID": [ {{ "e": "Description", "t": "YYYY-MM-DD", "n": "P/I", "r": "Reasoning based on [Base Date]..." }} ] }}
[Payload]
{payload}""",
        },
        "EVOLVE": {
            "CN": """你是一位精通临床 NLP 的提示词架构师。请分析失败案例，进化生产与审计指令。

[当前生产指令] {current_produce_tpl}
[当前审计准则] {current_audit_spec}
[失败案例报告] {payload}

[进化核心逻辑]
1. **Python 语法协议（最高优先级）**：
   - 生成的 `new_produce_tpl` 必须兼容 `.format()` 调用。
   - **转义规则**：JSON 结构示例中的所有 `{` 和 `}` 必须写成 `{{` 和 `}}`。
   - **保护占位符**：`{batch_size}`, `{payload}`, `{taxonomy}`, `{p_i}`, `{reasoning}`, `{grounding}` 必须保持**单括号**，禁止转义或修改。
2. **逻辑增强策略**：
   - **物理锚定**：针对文本不匹配，强化“逐字切片（Verbatim Slice）”和“零改动”要求。
   - **时间推演**：针对日期错误，强制要求在 `r` 中输出计算公式（如 [记录日]-3d）。
   - **粒度对齐**：严禁“脑补”日期精度（如 11月 严禁补全为 11-01）。
3. **审计加压**：
   - 进化 `new_audit_spec`，对“索引偏移”和“逻辑倒置”设置一票否决权。

[输出格式] 严格 JSON：
{{
  "new_produce_tpl": "更新后的全量生产指令...",
  "new_audit_spec": "更新后的全量审计准则..."
}}""",
            "EN": """You are a Lead Prompt Architect. Analyze failures to evolve the Clinical NLP instructions.

[Failure Context]
{payload}

[Mandatory Syntax Protocol]
The `new_produce_tpl` must be valid for Python's `.format()`:
1. **Escaping**: Use `{{` and `}}` for all JSON keys/structure examples.
2. **Placeholders**: Keep `{batch_size}`, `{payload}`, `{taxonomy}`, `{p_i}`, `{reasoning}`, and `{grounding}` in **single braces**. Do NOT modify or escape them.

[Evolution Focus]
1. **Verbatim Fidelity**: Enforce zero-tolerance for character/punctuation drift in `context`.
2. **Temporal Traceability**: Require explicit math in `r` (e.g., BaseDate + 5d).
3. **Granularity Integrity**: Strictly prohibit \"padding\" vague dates (e.g., Nov -> 11-01 is forbidden).
4. **Audit Rigor**: Penalize recurring errors (offset drift, date borrowing) more severely.

[Output]
Return a strict JSON object with keys \"new_produce_tpl\" and \"new_audit_spec\".""",
        },
    }

    TRAIN_PARAMS = {
        "learning_rate": 2e-4,
        "batch_size": 2,
        "grad_accum": 4,
        "max_steps": 30,
        "smoke_test": str_to_bool(os.getenv("SMOKE_TEST", "False")),
        "alpha_cons": 0.3,
        "lambda_logic": 0.1,
        "beta_ground": 0.2,
    }

    EVAL_PARAMS = {"fuzzy_threshold": 0.3, "mae_max_days": 900.0, "val_sample_size": 20}

    SPLIT_PARAMS = {
        "syn_ratios": (0.8, 0.1, 0.1),
        "e3c_ratios": (0.6, 0.2, 0.2),
        "med_few_shot_n": 12,  # Increased from 6 per user request
        "med_val_n": 5,        # Added real validation set
    }


# ==========================================
# Experiment Matrix Registry
# ==========================================
EXPERIMENT_MATRIX = {
    # --- [A] Rule-based Baselines ---
    "baseline_rule_cn": {
        "family": "rule_based",
        "test_sets": ["med_test", "syn_test"],
        "preferred_resource": "cpu",
        "desc": "CN Rule Baseline (Real + Synthetic)",
    },
    # --- [DEBUG] Parallel Inference ---
    "debug_parallel_t4": {
        "family": "debug",
        "test_sets": [],
        "preferred_resource": "t4",
        "script_name": "src/debug/parallel_inference_isolated.py", # Custom script support
        "desc": "Debug: Isolated Parallel Inference (File-Based Sync)",
    },
    "baseline_rule_en": {
        "family": "rule_based",
        "test_sets": ["e3c_test"],
        "max_steps": 400,
        "preferred_resource": "cpu",
        "desc": "EN Rule Baseline (E3C)",
    },
    # --- [B] LLM Zero-shot ---
    "llm_zeroshot_cn": {
        "family": "llm_sft",
        "max_steps": 0,
        "test_sets": ["med_test", "syn_test"],
        "desc": "Llama-3 CN Zero-shot",
    },
    "llm_zeroshot_en": {
        "family": "llm_sft",
        "max_steps": 0,
        "test_sets": ["e3c_test"],
        "desc": "Llama-3 EN Zero-shot",
    },
    # --- [C] Rule-based Baselines ---
    "rule_based_cn": {
        "family": "rule_based",
        "test_sets": ["med_test"],
        "desc": "CN Rule-based (Pattern Matching)",
    },
    "rule_based_en": {
        "family": "rule_based",
        "test_sets": ["e3c_test"],
        "desc": "EN Rule-based (Pattern Matching)",
    },
    # --- [D] IE-Span Baselines ---
    "ie_span_cn": {
        "family": "ie_span",
        "lang": "zh",
        "train_sets": ["syn_train", "med_few"],
        "test_sets": ["med_test", "syn_test"],
        "dev_key": "syn_dev",
        "max_steps": 1500,
        "early_stopping_patience": 5,
        "early_stopping_threshold": 0.0005,
        "preferred_resource": "p100",
        "desc": "CN IE-Span (RoBERTa-Large Offline)",
        "model_path": "/jhdx0003008/models/chinese-roberta-wwm-ext-large",
    },
    "ie_span_en": {
        "family": "ie_span",
        "lang": "en",
        "train_sets": ["e3c_train"],
        "test_sets": ["e3c_test"],
        "dev_key": "e3c_dev",
        "early_stopping_patience": 5,
        "early_stopping_threshold": 0.0005,
        "logging_steps": 5,
        "max_steps": 1000,
        "learning_rate": 3e-5,
        "preferred_resource": "p100",
        "desc": "EN IE-Span (PubMedBERT)",
    },
    "ie_span_local": {
        "family": "ie_span",
        "train_sets": ["e3c_train"],
        "dev_key": "e3c_dev",
        "test_sets": ["e3c_test"],
        "max_steps": 1000,
        "early_stopping_patience": 5,
        "logging_steps": 10,
        "learning_rate": 3e-5,
        "preferred_resource": "gpu",
        "desc": "EN IE-Span (PubMedBERT Offline)",
        # Use locally synced model
        "model_path": "/root/projects/ai4s/temp_models/PubMedBERT",
    },
    # --- [E] Zero-shot Baselines ---
    "zero_shot_cn": {
        "family": "zero_shot",
        "test_sets": ["med_test"],
        "max_steps": 0,
        "desc": "CN Zero-shot (Base Model)",
    },
    "zero_shot_en": {
        "family": "zero_shot",
        "test_sets": ["e3c_test"],
        "max_steps": 0,
        "desc": "EN Zero-shot (Base Model)",
    },
    # --- [F] LLM SFT Baselines ---
    "llm_sft_cn": {
        "family": "llm_sft",
        "train_sets": ["syn_train", "med_few"],
        "dev_key": "syn_dev",
        "test_sets": ["med_test", "syn_test"],
        "max_steps": 150,
        "preferred_resource": "p100",
        "desc": "CN Standard LoRA-SFT (Baseline)",
    },
    "llm_sft_en": {
        "family": "llm_sft",
        "train_sets": ["e3c_train"],
        "dev_key": "e3c_dev",
        "test_sets": ["e3c_test"],
        "max_steps": 80,
        "preferred_resource": "p100",
        "desc": "EN Standard LoRA-SFT",
    },
    # --- [G] MedTime-GVP Core ---
    "medtime_gvp_cn": {
        "family": "llm_medtime",
        "train_sets": ["syn_train", "med_few"],
        "dev_key": "syn_dev",
        "test_sets": ["med_test", "syn_test"],
        "max_steps": 200,
        "inference_only": False,
        "preferred_resource": "t4",
        "desc": "MedTime-GVP CN Core (Proposed)",
    },
    "medtime_gvp_en": {
        "family": "llm_medtime",
        "train_sets": ["e3c_train"],
        "dev_key": "e3c_dev",
        "test_sets": ["e3c_test"],
        "max_steps": 200, 
        "inference_only": False,
        "preferred_resource": "gpu_4", # Explicitly set to GPU 4
        "batch_size": 1, # [OOM-Fix] Reduced from Default 4
        "grad_accumulation": 16, # Compensate for BS=1
        "alpha_cons": 0.3,
        "lambda_logic": 0.1,
        "beta_ground": 0.2,
        "desc": "MedTime-GVP EN Core (Proposed)",
    },
    "rule_cn": {
        "family": "rule_based",
        "test_sets": ["med_test"],
        "lang": "cn",
        "desc": "Rule-Based Baseline (CN)"
    },
    "rule_en": {
        "family": "rule_based",
        "test_sets": ["e3c_test"],
        "lang": "en",
        "desc": "Rule-Based Baseline (EN)"
    },
    "medtime_few_shot_cn": {
        "family": "llm_medtime",
        "train_sets": ["med_few"], # ONLY Real Data
        "dev_key": "med_dev",
        "test_sets": ["med_test"],
        "lang": "cn",
        "desc": "Few-Shot Real Data Only"
    },
    "medtime_few_shot_syn": {
        "family": "llm_medtime",
        "train_sets": ["med_few"], # Real Few-Shot Transfer
        "dev_key": "med_dev",
        "test_sets": ["syn_test"], # Target Synthetic
        "max_steps": 50,
        "learning_rate": 5e-5,
        "batch_size": 1,
        "grad_accum": 4,
        "inference_only": False,
        "desc": "Real Few-Shot Transfer to Synthetic",
    },
    # [Replication] Formal entry for the ad-hoc "real_few_shot_v2" experiment
    "medtime_few_shot_real": {
        "family": "llm_medtime",
        "train_sets": ["med_few"],
        "dev_key": "med_dev",
        "test_sets": ["med_test"],
        "max_steps": 50,
        "learning_rate": 5e-5,
        "batch_size": 2,
        "grad_accum": 2,
        "inference_only": False, # Switchable via CLI
        "desc": "Real Few-Shot V2 Replication (Fixed Config)",
    },

    "medtime_few_shot_real_14b": {
        "family": "llm_medtime",
        "train_sets": ["med_few"],
        "dev_key": "med_dev",
        "test_sets": ["med_test"],
        "max_steps": 50,
        "learning_rate": 5e-5,
        "batch_size": 2,
        "grad_accum": 2,
        "inference_only": False,
        "base_model": "/jhdx0003008/models/Qwen2.5-14B-Instruct",
        "desc": "Real Few-Shot (14B Model)",
    },


    "cross_lingual_en_to_cn": {
        "family": "llm_medtime",
        "train_sets": ["e3c_train"],
        "dev_key": "e3c_dev",
        "test_sets": ["med_test"],
        "max_steps": 80, # [Reduced] From 150
        "alpha_cons": 0.3,
        "lambda_logic": 0.1,
        "desc": "Cross-lingual (EN -> CN)",
    },
    "ablation_no_topo": {
        "family": "llm_medtime",
        "train_sets": ["syn_train", "med_few"],
        "dev_key": "syn_dev",
        "test_sets": ["med_test"],
        "max_steps": 150,
        "alpha_cons": 0.3,
        "lambda_logic": 0.0,
        "desc": "Ablation: No Topology",
    },
    "ablation_no_align": {
        "family": "llm_medtime",
        "train_sets": ["syn_train", "med_few"],
        "dev_key": "syn_dev",
        "test_sets": ["med_test"],
        "max_steps": 150,
        "alpha_cons": 0.0,
        "lambda_logic": 0.1,
        "beta_ground": 0.2,
        "desc": "Ablation: No Alignment",
    },
    "ablation_no_ground": {
        "family": "llm_medtime",
        "train_sets": ["syn_train", "med_few"],
        "dev_key": "syn_dev",
        "test_sets": ["med_test"],
        "max_steps": 150,
        "alpha_cons": 0.3,
        "lambda_logic": 0.1,
        "beta_ground": 0.0,
        "desc": "Ablation: No Grounding",
    },
    "medtime_gvp_pure_syn_cn": {
        "family": "llm_medtime",
        "train_sets": ["syn_train"], # PURE SYNTHETIC (Zero-Shot Transfer to Real)
        "dev_key": "syn_dev",
        "test_sets": ["med_test"],
        "max_steps": 150,
        "desc": "Ablation: Pure Synthetic Training (No Mixed Real Data)",
    },
    "ablation_no_ver": {
        "family": "llm_medtime",
        "train_sets": ["syn_train", "med_few"],
        "dev_key": "syn_dev",
        "test_sets": ["med_test"],
        "max_steps": 150,
        "alpha_cons": 0.3,
        "lambda_logic": 0.1,
        "force_verifier_on": True, # <--- Disables gating, forces Logic Loss always on
        "desc": "Ablation: No Verifier (Force Logic)",
    },
    # --- [H] English Ablations (E3C) ---
    "medtime_few_shot_en": {
        "family": "llm_medtime",
        "train_sets": ["e3c_few"], # Targeted Few-Shot Set
        "dev_key": "e3c_dev",
        "test_sets": ["e3c_test"],
        "max_steps": 100, # Increased from 50 for English verbosity
        "preferred_resource": "gpu_4",
        "batch_size": 1,
        "grad_accumulation": 16,
        "desc": "EN Few-Shot Baseline (Repairing SFT Hallucination)",
    },
    "medtime_few_shot_en_no_topo": {
        "family": "llm_medtime",
        "train_sets": ["e3c_few"],
        "dev_key": "e3c_dev",
        "test_sets": ["e3c_test"],
        "max_steps": 100,
        "preferred_resource": "gpu_4",
        "batch_size": 2,
        "grad_accumulation": 8,
        "lambda_logic": 0.0, # NO Topology
        "desc": "Ablation EN Few-Shot: No Topology",
    },
    "medtime_few_shot_en_no_align": {
        "family": "llm_medtime",
        "train_sets": ["e3c_few"],
        "dev_key": "e3c_dev",
        "test_sets": ["e3c_test"],
        "max_steps": 100,
        "preferred_resource": "gpu_4",
        "batch_size": 2,
        "grad_accumulation": 8,
        "alpha_cons": 0.0, # NO Alignment
        "lambda_logic": 0.1,
        "beta_ground": 0.2,
        "desc": "Ablation EN Few-Shot: No Alignment",
    },
    # --- [J] CN Few-Shot Ablations ---
    "medtime_few_shot_cn_no_topo": {
        "family": "llm_medtime",
        "train_sets": ["med_few"],
        "dev_key": "med_dev",
        "test_sets": ["med_test"],
        "max_steps": 150,
        "lambda_logic": 0.0, # NO Topology
        "desc": "Ablation CN Few-Shot: No Topology",
    },
    "medtime_few_shot_cn_no_align": {
        "family": "llm_medtime",
        "train_sets": ["med_few"],
        "dev_key": "med_dev",
        "test_sets": ["med_test"],
        "max_steps": 150,
        "alpha_cons": 0.0, # NO Alignment
        "lambda_logic": 0.1, 
        "beta_ground": 0.2,
        "desc": "Ablation CN Few-Shot: No Alignment",
    },
    "ablation_no_topo_en": {
        "family": "llm_medtime",
        "train_sets": ["e3c_train"],
        "dev_key": "e3c_dev",
        "test_sets": ["e3c_test"],
        "max_steps": 200,
        "preferred_resource": "gpu_4",
        "batch_size": 1,
        "grad_accumulation": 16,
        "alpha_cons": 0.3,
        "lambda_logic": 0.0, # NO Topology/Logic Loss
        "desc": "Ablation EN: No Topology",
    },
    "ablation_no_align_en": {
        "family": "llm_medtime",
        "train_sets": ["e3c_train"],
        "dev_key": "e3c_dev",
        "test_sets": ["e3c_test"],
        "max_steps": 200,
        "preferred_resource": "gpu_4",
        "batch_size": 1,
        "grad_accumulation": 16,
        "alpha_cons": 0.0, # NO Alignment Loss
        "lambda_logic": 0.1,
        "beta_ground": 0.2,
        "desc": "Ablation EN: No Alignment",
    },
    # --- [I] CoGD Vision Tasks ---
    "E1_CoGD_InDomain": {
        "family": "vision_cogd",
        "script_name": "train_cogd.py",
        "preferred_resource": "p100",
        "desc": "CoGD In-Domain Baseline (Kvasir+CVC)",
    },

}

# ==========================================
# 🚀 Dynamic Experiment Loader
# ==========================================
import json
import glob

def _load_experiment_configs():
    """
    Auto-load extra experiments from src/medtime/experiments/*.json
    This allows adding new experiments without modifying config.py directly.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    exp_dir = os.path.join(current_dir, "experiments")
    
    if os.path.exists(exp_dir):
        config_files = glob.glob(os.path.join(exp_dir, "*.json"))
        for fpath in config_files:
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        # Validate and merge
                        count = 0
                        for k, v in data.items():
                            if k not in EXPERIMENT_MATRIX:
                                EXPERIMENT_MATRIX[k] = v
                                count += 1
                        if count > 0:
                            if os.getenv("MEDTIME_VERBOSE"):
                                print(f"🧩 Loaded {count} experiments from {os.path.basename(fpath)}")
            except Exception as e:
                print(f"⚠️ Failed to load experiment config {fpath}: {e}")

# Execute Loader
_load_experiment_configs()
