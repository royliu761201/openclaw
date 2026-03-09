import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


# ============================================================
# 0. 序列化工具
# ============================================================
def _json_safe(obj):
    """
    递归处理配置对象，解决标准 json.dump 无法处理的问题。
    """
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, dict):
        return {str(k): _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_json_safe(v) for v in obj]
    if hasattr(obj, "item"):  # 处理 numpy.int64, torch.scalar 等
        return obj.item()
    if hasattr(obj, "tolist"):  # 处理 numpy.array 或 torch.tensor
        return obj.tolist()
    return obj


# ============================================================
# 1. 数据集规范定义 (Dataset Specification)
# ============================================================
@dataclass
class DatasetSpec:
    """
    定义一个数据集实体的属性。
    支持在一个实验中自由组合多个来源的数据集。
    """

    name: str  # 数据集标识符，如 "piccolo", "kvasir"
    split: str  # 数据切分，如 "train", "val", "test"
    modality: str = "wli"  # 初始模态，默认为白光成像 (White Light Imaging)
    # 扩展参数：可存放特定的采样权重、子文件夹路径等
    extra: Dict[str, Any] = field(default_factory=dict)


# ============================================================
# 2. 模型架构配置 (Model Architecture)
# ============================================================
@dataclass
class ModelConfig:
    """
    CoGD-Net 核心超参数。
    """

    arch: str = "cogd_sam2_v4"
    sam2_id: str = "facebook/sam2-hiera-large"  # 预训练 SAM2 权重 ID

    # CoGD 扩散核心超参 (论文 Section 4.4 - 4.5)
    cogd_dim: int = 256  # 扩散特征维度
    condition_dim: int = 6  # 临床先验向量维度 (Size, Modality, etc.)
    cogd_steps: int = 3  # 扩散迭代步数 T
    knn_k: int = 8  # 动态图邻居数 K

    use_lora: bool = True  # 是否对 SAM2 Encoder 开启 LoRA 微调
    use_graft: bool = True # 是否开启 CoGD 扩散嫁接模块 (False = Pure SAM2 Baseline)
    use_cond: bool = True  # 是否使用临床先验 (False = Ablation NoCond)
    use_privileged_distill: bool = True  # 是否开启 NBI 模态的特权信息蒸馏


# ============================================================
# 3. 训练策略配置 (Training Strategy)
# ============================================================
@dataclass
class TrainConfig:
    """
    控制模型如何学习。
    """

    # [阶段1 Epochs, 阶段2 Epochs, 阶段3 Epochs]
    stage_epochs: List[int] = field(default_factory=lambda: [5, 10, 15])

    lr: float = 1e-4  # 初始学习率
    batch_size: int = 4  # 每个 GPU 的 Batch Size
    grad_accumulate: int = 2  # 梯度累积

    modality_dropout: float = 0.2  # 随机丢弃 NBI/元数据比例

    # 损失函数权重 (论文 Section 4.8)
    lambda_align: float = 0.1  # 跨模态特征对齐权重 (Beta)
    gamma_tail: float = 0.5  # 长尾 Boost (Gamma)
    lambda_dice: float = 1.0  # Dice Loss 权重
    lambda_bce: float = 1.0  # BCE Loss 权重

    # 验证指标配置
    bf_tol: int = 2  # Boundary F1 Tolerance
    enable_hd95: bool = True  # 是否计算 HD95


# ============================================================
# 4. 全局实验总控 (Nexus Global Config)
# ============================================================
@dataclass
class NexusConfig:
    """
    实验顶层容器。
    """

    exp_id: str = "Baseline_CoGD_V4"
    description: str = "Standard multi-stage training with SAM2-Large"

    gdrive_id: str = "1phVi2_5XiXGGAOx6VNW6Nlba6qDFDlyB"
    # 🚀 一键烟雾测试 (Smoke Test)
    smoke_test: bool = False

    # 断点续传逻辑
    # "last": 自动寻找最新进度恢复; "best": 加载最优模型; None: 从头开始
    resume_from: Optional[str] = "last"

    # 组件注入
    model: ModelConfig = field(default_factory=ModelConfig)
    train: TrainConfig = field(default_factory=TrainConfig)

    # 数据集组合定义
    train_datasets: List[DatasetSpec] = field(default_factory=list)
    val_datasets: List[DatasetSpec] = field(default_factory=list)
    test_datasets: List[DatasetSpec] = field(default_factory=list)

    # 🚀 实验跟踪 (W&B)
    use_wandb: bool = True
    wandb_project: str = "CoGD-Nexus"

    # 运行时注入 (Runtime injection)
    project_root: Path = field(default_factory=lambda: Path("./experiments"))
    data_dir: Optional[Path] = None

    def __post_init__(self):
        """
        对象实例化后的自动处理：
        1. 映射物理路径。
        2. 自动创建实验文件夹结构。
        """
        # 每个实验拥有唯一的输出文件夹
        self.exp_dir = self.project_root / "results" / self.exp_id
        if not self.exp_dir.exists():
            # Avoid creating directories during simple init if strictly purely config,
            # but here it's part of the convenience. We can keep it but handle strictly.
            pass

    def init_workspace(self):
        """Explicit workspace initialization"""
        self.exp_dir = self.project_root / "results" / self.exp_id
        self.exp_dir.mkdir(parents=True, exist_ok=True)
        for d in ["checkpoints", "visualizations", "metrics"]:
            (self.exp_dir / d).mkdir(exist_ok=True)

    def save_manifest(self):
        """
        实验快照
        """
        self.init_workspace()  # Ensure dir exists
        path = self.exp_dir / "experiment_manifest.json"
        clean_dict = _json_safe(asdict(self))
        with open(path, "w", encoding="utf-8") as f:
            json.dump(clean_dict, f, indent=4, ensure_ascii=False)
        return path

# ============================================================
# 5. 实验矩阵 (Experiment Matrix)
# ============================================================
# Maps Experiment ID -> Configuration Overrides (Dict)
# This replaces the hardcoded logic in main.py
EXPERIMENT_MATRIX = {
    # --- Phase 1: In-Domain Baseline ---
    "E1_CoGD_InDomain": {
        "description": "Train on Kvasir+CVC, Test on Kvasir+CVC",
        "train_datasets": [DatasetSpec("kvasir", "train"), DatasetSpec("cvc", "train")],
        "test_datasets": [DatasetSpec("kvasir", "test"), DatasetSpec("cvc", "test")]
    },
    
    # --- Phase 2: Size-Stratified (PICCOLO) ---
    "E2_CoGD_PICCOLO": {
        "description": "Train on PICCOLO with pairs to prove small lesion recall",
        "train_datasets": [DatasetSpec("piccolo", "train", modality="pair")],
        "test_datasets": [DatasetSpec("piccolo", "test", modality="wli")]
    },
    
    # --- Phase 3: OOD Generalization ---
    "E3_CoGD_OOD_ETIS": {
        "description": "Test E1 model on ETIS-Larib (Zero-shot)",
        "train_datasets": [], # Inference only (usually resumed from E1)
        "test_datasets": [DatasetSpec("etis", "test")]
    },
    
    # --- Ablations ---
    "Ablation_NoGraft": {
        "description": "Baseline: No Graph Diffusion",
        "model": {"use_graft": False},
        "train_datasets": [DatasetSpec("kvasir", "train"), DatasetSpec("cvc", "train")],
        "test_datasets": [DatasetSpec("kvasir", "test"), DatasetSpec("cvc", "test")]
    },
    
    "Baseline_SAM2": {
        "description": "Baseline: Pure SAM2 (No Graft, No Cond)",
        "model": {"use_graft": False, "use_cond": False},
        "train_datasets": [DatasetSpec("kvasir", "train"), DatasetSpec("cvc", "train")],
        "test_datasets": [DatasetSpec("kvasir", "test"), DatasetSpec("cvc", "test")]
    },
    
    "ZeroShot_Kvasir": {
        "description": "Zero-Shot Inference on Kvasir",
        "model": {"use_graft": False, "use_cond": False},
        "train": {"stage_epochs": [0,0,0]}, # No training
        "train_datasets": [],
        "test_datasets": [DatasetSpec("kvasir", "test")]
    }
}
