import torch
import torch.nn as nn
import math

class PatchEmbedding(nn.Module):
    def __init__(self, grid_size=64, patch_size=8, embed_dim=128, in_channels=2, dim=2):
        """
        Inputs: u (State), r (Residual)
        dim=1: [B, C, Grid]
        dim=2: [B, C, H, W]
        """
        super().__init__()
        self.dim = dim
        self.patch_size = patch_size
        self.grid_size = grid_size
        
        if dim == 1:
            self.num_patches = grid_size // patch_size
            self.proj = nn.Linear(in_channels * patch_size, embed_dim)
        else:
            self.num_patches_side = grid_size // patch_size
            self.num_patches = self.num_patches_side ** 2
            self.proj = nn.Linear(in_channels * patch_size * patch_size, embed_dim)
            
        self.pos_embed = nn.Parameter(torch.zeros(1, self.num_patches, embed_dim))

    def forward(self, x):
        B = x.shape[0]
        
        if self.dim == 1:
            # x: [B, C, Grid] -> [B, C, N, P]
            C, Grid = x.shape[1], x.shape[2]
            x = x.view(B, C, self.num_patches, self.patch_size)
            x = x.permute(0, 2, 1, 3).reshape(B, self.num_patches, -1)
        else:
            # x: [B, C, H, W]
            H, W = x.shape[2], x.shape[3]
            # Patchify 2D: [B, C, Nh, P, Nw, P]
            x = x.view(B, -1, self.num_patches_side, self.patch_size, self.num_patches_side, self.patch_size)
            # -> [B, Nh, Nw, C, P, P]
            x = x.permute(0, 2, 4, 1, 3, 5)
            # Flatten: [B, N, FlattenedPatch]
            x = x.reshape(B, self.num_patches, -1)
            
        x = self.proj(x)
        x = x + self.pos_embed
        return x

class LinearAttention(nn.Module):
    """
    Feature Map Linear Attention (Katharopoulos et al. 2020)
    O(N) Complexity.
    phi(x) = elu(x) + 1
    Two-way autoregressive or bidirectional usage.
    """
    def __init__(self, d_model, nhead, dropout=0.1):
        super().__init__()
        self.d_model = d_model
        self.nhead = nhead
        self.head_dim = d_model // nhead
        
        self.q_proj = nn.Linear(d_model, d_model)
        self.k_proj = nn.Linear(d_model, d_model)
        self.v_proj = nn.Linear(d_model, d_model)
        self.out_proj = nn.Linear(d_model, d_model)
        self.dropout = nn.Dropout(dropout)
        
    def feature_map(self, x):
        return F.elu(x) + 1.0

    def forward(self, q, k, v):
        B, N, C = q.shape
        q = self.q_proj(q).view(B, N, self.nhead, self.head_dim).transpose(1, 2)
        k = self.k_proj(k).view(B, N, self.nhead, self.head_dim).transpose(1, 2)
        v = self.v_proj(v).view(B, N, self.nhead, self.head_dim).transpose(1, 2)
        
        Q = self.feature_map(q)
        K = self.feature_map(k)
        
        # O(N) attention: (Q @ K^T) @ V -> Q @ (K^T @ V)
        # KV: [B, H, D, D]
        KV = torch.einsum("bhnd,bhne->bhde", K, v)
        
        # Z: [B, H, D] (Denominator)
        k_sum = K.sum(dim=2, keepdim=True)
        Z = 1.0 / (torch.einsum("bhnd,bhcd->bhn", Q, k_sum) + 1e-6)
        
        # Out
        out = torch.einsum("bhnd,bhde->bhne", Q, KV)
        out = out * Z.unsqueeze(-1)
        
        out = out.transpose(1, 2).reshape(B, N, C)
        return self.out_proj(out)

class EfficientAttentionLayer(nn.Module):
    def __init__(self, d_model, nhead, dim_feedforward=2048, dropout=0.1, linear=False):
        super().__init__()
        self.linear = linear
        if linear:
            self.self_attn = LinearAttention(d_model, nhead, dropout)
        else:
            self.self_attn = nn.MultiheadAttention(d_model, nhead, dropout=dropout, batch_first=True)
            
        self.linear1 = nn.Linear(d_model, dim_feedforward)
        self.dropout = nn.Dropout(dropout)
        self.linear2 = nn.Linear(dim_feedforward, d_model)

        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.dropout1 = nn.Dropout(dropout)
        self.dropout2 = nn.Dropout(dropout)
        self.activation = F.gelu

    def forward(self, src):
        src2 = self.norm1(src)
        if self.linear:
            src2 = self.self_attn(src2, src2, src2)
        else:
            # implicit self-attention
            src2, _ = self.self_attn(src2, src2, src2, need_weights=False)
            
        src = src + self.dropout1(src2)
        src2 = self.norm2(src)
        src2 = self.linear2(self.dropout(self.activation(self.linear1(src2))))
        src = src + self.dropout2(src2)
        return src

class NewtonTransformer(nn.Module):
    def __init__(self, config):
        super().__init__()
        self.config = config
        
        # Auto-detect dim based on patch calc logic or config
        dim = getattr(config, "dim", 2) 
        
        self.embedding = PatchEmbedding(
            grid_size=config.grid_size,
            patch_size=config.patch_size,
            embed_dim=config.n_embd,
            dim=dim
        )
        
        self.layers = nn.ModuleList([
            EfficientAttentionLayer(
                d_model=config.n_embd,
                nhead=config.n_head,
                dim_feedforward=4 * config.n_embd,
                dropout=config.dropout,
                linear=getattr(config, 'linear_attn', False)
            )
            for _ in range(config.n_layer)
        ])
        
        # Output Head
        if dim == 1:
            out_dim = config.patch_size
        else:
            out_dim = config.patch_size * config.patch_size
            
        self.head = nn.Linear(config.n_embd, out_dim)

    def forward(self, u, r):
        # u, r: [B, ...]
        x = torch.stack([u, r], dim=1) # [B, 2, ...]
        
        emb = self.embedding(x)
        out = emb
        for layer in self.layers:
            out = layer(out)
        return self.head(out)
        
class Config:
    grid_size = 64
    patch_size = 8
    n_embd = 128
    n_head = 4
    n_layer = 4
    dropout = 0.1
    dim = 2 # Default
    linear_attn = False

class ConfigLarge(Config):
    n_embd = 512
    n_head = 8
    n_layer = 8 # Deeper for operator composition
    dropout = 0.1
    linear_attn = True # Enable Linear Attention

class Normalizer:
    def __init__(self, tensor):
        if torch.is_tensor(tensor):
            self.mean = torch.mean(tensor)
            self.std = torch.std(tensor) + 1e-6
        else:
            # Handle loading from dict/state_dict if needed, 
            # though usually we pickle the object itself.
            self.mean = 0.0
            self.std = 1.0
    
    def encode(self, x):
        return (x - self.mean) / self.std
    
    def decode(self, x):
        return x * self.std + self.mean
