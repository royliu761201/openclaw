
from typing import Dict, List, Set, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F
from peft import LoraConfig, get_peft_model
from transformers import Sam2Model

# Import configuration
from src.cogd.config import NexusConfig


# ============================================================
# 1. 动态层探测器 (LoRA 兼容性工具)
# ============================================================
def find_lora_targets(model, include_4bit=False):
    import torch.nn as nn
    linear_types = [nn.Linear]
    targets = set()
    for name, module in model.named_modules():
        if isinstance(module, tuple(linear_types)):
            targets.add(name.split(".")[-1])
    return list(targets)

# ============================================================
# 2. CoGD 扩散模块 (论文 Section 4.4 - 4.5 核心实现)
# ============================================================
class CoGDModule(nn.Module):
    """
    Conditional Graph Diffusion Module.
    实现论文 Eq. 2: H_{t+1} = H_t - alpha_t(c) * L * H_t
    实现论文 Eq. 3: 基于 FiLM 的动态边缘门控 A_ij
    """
    def __init__(self, dim, condition_dim, k, steps):
        super().__init__()
        self.k = k
        self.steps = steps

        # 论文 4.4: 映射先验向量 c 到特征空间
        self.phi = nn.Sequential(
            nn.Linear(condition_dim, 64),
            nn.ReLU(),
            nn.Linear(64, dim)
        )

        # 论文 4.5: 动态步长控制 alpha_t(c)
        self.alpha_net = nn.Sequential(
            nn.Linear(dim, 1),
            nn.Sigmoid()
        )

        # 论文 Eq. 3: 边缘门控权重生成 (FiLM-style)
        self.edge_gating = nn.Sequential(
            nn.Linear(dim * 2 + dim, 1), # [hi, hj, phi(c)]
            nn.Sigmoid()
        )

    def forward(self, x, c_vec):
        """
        x: [B, C, H, W] - 潜在 Token 特征图
        c_vec: [B, 6] - 临床先验向量 (Size, Modality等)
        """
        B, C, H, W = x.shape
        N = H * W

        # 1. 构建 Token 节点 [B, N, C]
        h = x.view(B, C, N).permute(0, 2, 1).contiguous()

        # 2. 先验调制器
        phi_c = self.phi(c_vec) # [B, C]
        # alpha = self.alpha_net(phi_c).view(B, 1, 1) # [B, 1, 1] 
        # Wait, phi_c is [B, C], alpha_net expects dim=C -> [B, 1]. View to [B, 1, 1] is correct.
        alpha = self.alpha_net(phi_c).view(B, 1, 1)

        # 3. 动态特征图构建 (Feature kNN, k=8)
        # 0 手动 .to(device)，始终跟随输入 x
        dist = torch.cdist(h, h)
        _, indices = torch.topk(dist, k=self.k, dim=-1, largest=False)

        # 准备邻居索引
        b_idx = torch.arange(B, device=x.device).view(B, 1, 1).expand(B, N, self.k)

        # 4. 显式 Euler 扩散迭代 (论文 Eq. 2)
        for _ in range(self.steps):
            # 获取邻居特征 [B, N, K, C]
            h_nb = h[b_idx, indices]

            # 论文 Eq. 3: 计算各向异性边缘权重 (Conditioned Edge Gating)
            # 拼接 [hi, hj, phi_c]
            h_i = h.unsqueeze(2).expand(-1, -1, self.k, -1) # [B, N, K, C]
            phi_c_expanded = phi_c.view(B, 1, 1, C).expand(-1, N, self.k, -1)

            gate_input = torch.cat([h_i, h_nb, phi_c_expanded], dim=-1)
            g_ij = self.edge_gating(gate_input) # [B, N, K, 1]

            # 聚合邻居信息 (带门控的拉普拉斯算子简化)
            # H_nb_weighted = \sum (g_ij * h_j) / \sum g_ij
            weighted_nb = (g_ij * h_nb).sum(dim=2) / (g_ij.sum(dim=2) + 1e-6)

            # 步进更新: H = H + alpha * (Weighted_Neighbors - H)
            h = h + alpha * (weighted_nb - h)

        # 5. 还原特征图形状
        return h.permute(0, 2, 1).contiguous().view(B, C, H, W)

# ============================================================
# 3. NexusGraft 包装器 (SAM2 + CoGD)
# ============================================================
class NexusGraft(nn.Module):
    def __init__(self, cfg: NexusConfig):
        super().__init__()
        self.cfg = cfg
        # 实例化基础模型 SAM2
        self.sam = Sam2Model.from_pretrained(
            cfg.model.sam2_id
        )

        # 注入 LoRA (仅作用于 Vision Encoder)
        if cfg.model.use_lora:
            targets = find_lora_targets(self.sam.vision_encoder)
            lora_cfg = LoraConfig(
                r=16, lora_alpha=32, target_modules=targets,
                lora_dropout=0.05, bias="none"
            )
            self.sam.vision_encoder = get_peft_model(self.sam.vision_encoder, lora_cfg)

        # 嫁接 CoGD 扩散模块
        self.cogd = CoGDModule(
            dim=cfg.model.cogd_dim,
            condition_dim=cfg.model.condition_dim,
            k=cfg.model.knn_k,
            steps=cfg.model.cogd_steps
        )

    def forward(self, batch: Dict[str, torch.Tensor]):
        """
        弹性 Forward：从 batch 字典中提取输入，自动适配单/双模态。
        """
        x = batch['wli'] # 主输入始终为白光图像
        B, _, H, W = x.shape

        # A. 提取多尺度特征 (Encoder)
        features = self.sam.get_image_embeddings(x)

        # 适配不同版本的 SAM2 输出格式
        img_embed = features.image_embeddings if hasattr(features, "image_embeddings") else features[-1]
        high_res = features.high_res_features if hasattr(features, "high_res_features") else features[:2]

        # B. 弹性临床先验注入
        # 如果 batch 中没有先验（如测试基线），则初始化为 0
        c_vec = batch.get('condition', torch.zeros((B, self.cfg.model.condition_dim), device=x.device))
        
        # [ABLATION] NoCond: Force clinical priors to zero
        if not self.cfg.model.use_cond:
            c_vec = torch.zeros_like(c_vec)

        # C. 核心：CoGD 特征扩散强化 (Section 4.5)
        # [ABLATION] NoGraft: Skip CoGD module, pass through embeddings
        if self.cfg.model.use_graft:
            refined_embed = self.cogd(img_embed, c_vec)
        else:
            refined_embed = img_embed

        # D. 提示生成 (Prompt Encoder: 全图 Box 自动模式)
        # 使用 device=x.device 确保 0 搬运开销
        full_box = torch.tensor([[[0, 0, W, H]]], device=x.device).float().repeat(B, 1, 1)
        sparse_emb, dense_emb = self.sam.prompt_encoder(
            input_points=None, input_labels=None,
            input_boxes=full_box, input_masks=None
        )

        pos = self.sam.get_image_wide_positional_embeddings()[-1]
        if pos.dim() == 3:  # [C,H,W]
            pos = pos.unsqueeze(0).expand(B, -1, -1, -1).contiguous()
        elif pos.dim() == 4 and pos.shape[0] != B:
            raise RuntimeError(f"pos batch mismatch: pos={pos.shape}, B={B}")

        # E. 解码 Mask (Mask Decoder)
        decoder_out = self.sam.mask_decoder(
            image_embeddings=refined_embed,
            image_positional_embeddings=pos,
            sparse_prompt_embeddings=sparse_emb,
            dense_prompt_embeddings=dense_emb,
            high_resolution_features=high_res,
            multimask_output=False
        )

        # 提取并自动规范化 Mask 形状到 [B, 1, H, W]

        masks = decoder_out[0] if isinstance(decoder_out, tuple) else decoder_out.pred_masks

        # 统一缩减至 4D: [B, C, H, W]
        while masks.dim() > 4:
            masks = masks.squeeze(2) # 消除多余的候选维度
        if masks.dim() == 4 and masks.shape[1] > 1:
            masks = masks[:, :1, :, :] # 只取最高分候选
        if masks.dim() == 3:
            masks = masks.unsqueeze(1)

        # 现在 masks 稳定为 [B, 1, Hm, Wm]
        masks = F.interpolate(masks, size=(H, W), mode='bilinear', align_corners=False)
        masks = F.interpolate(masks, size=(H, W), mode='bilinear', align_corners=False)

        return masks, refined_embed
