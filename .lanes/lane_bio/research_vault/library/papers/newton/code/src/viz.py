import torch
import numpy as np
import matplotlib.pyplot as plt
import argparse
from src.newton.model import NewtonTransformer, Config
from train_newton import load_data, patchify_target

def visualize_attention(args):
    # 1. Load Model
    cfg = Config()
    model = NewtonTransformer(cfg)
    
    # Check for saved model
    chk_path = f"{args.model_dir}/newton_v1.pt"
    try:
        model.load_state_dict(torch.load(chk_path, map_location="cpu"))
        print(f"✅ Loaded model from {chk_path}")
    except FileNotFoundError:
        print(f"⚠️ Model not found at {chk_path}, using random weights for demo.")
        
    model.eval()
    
    # 2. Hook Attention
    # We want the attention weights from the last decoder layer
    # Layer structure: model.transformer.layers[-1].self_attn
    attn_weights = {}
    def get_attn_hook(name):
        def hook(module, input, output):
            # output of MultiheadAttention is (attn_output, attn_output_weights) if need_weights=True
            # BUT nn.TransformerDecoderLayer calls it with need_weights=False by default usually.
            # However, we can't easily change the call signature inside the frozen layer class.
            # Workaround: We hook the 'Out' projection or just rely on the fact that we can't get it easily 
            # without modifying the model code or using a custom Transformer.
            
            # WAIT: PyTorch's MultiheadAttention forward returns (output, weights) 
            # ONLY IF need_weights=True. The TransformerDecoderLayer defaults to need_weights=False?
            # Actually, standard PyTorch TransformerDecoderLayer does NOT expose weights.
            pass 
        return hook

    # Manual Forward to extract weights simply by replacing the layer? 
    # Or just "simulate" the attention since we have the query/keys?
    # Let's do a Forward Pass and assume we can interpret the input-output simply for now
    # OR: Monkey patch the forward of the self_attn module?
    
    # Effective Strategy: Extract Embeddings (Q, K) and compute manually
    
    # 3. Load Sample Data
    data = np.load(args.data)
    idx = 0
    u = torch.from_numpy(data['u'][idx, 0]).float().unsqueeze(0) # [1, 64, 64]
    r = torch.from_numpy(data['r'][idx, 0]).float().unsqueeze(0) # [1, 64, 64]
    
    # 4. Forward & Manual Attention Calc
    with torch.no_grad():
        x = torch.stack([u, r], dim=1)
        emb = model.embedding(x) # [1, N, E]
        
        # Get Q, K, V from the last layer's self-attn
        layer = model.transformer.layers[-1]
        attn_module = layer.self_attn
        
        # Inputs to last layer (approximate as 'emb' for 1-layer, or run full)
        # For deeper models, we need the actual input to the last layer.
        features = emb
        for i, l in enumerate(model.transformer.layers[:-1]):
            features = l(features, features)
            
        # Now 'features' is input to last layer
        q = features
        k = features
        
        # Linear projections
        # PyTorch MHA packs q,k,v weights.
        # in_proj_weight: [3*E, E]
        qkv = torch.nn.functional.linear(features, attn_module.in_proj_weight, attn_module.in_proj_bias)
        Q, K, V = qkv.chunk(3, dim=-1)
        
        # Scale Dot Product Attention
        # dim: [B, N, Head, D_head]
        B, N, E = Q.shape
        scale = (E // cfg.n_head) ** -0.5
        
        # Simple view: Average over heads for viz
        scores = torch.matmul(Q, K.transpose(-2, -1)) * scale
        weights = torch.softmax(scores, dim=-1) # [B, N, N]
        
    # 5. Plot
    # Visualize Attention of the Center Token to all other tokens
    center_idx = N // 2 + int(np.sqrt(N)/2) # Approx center
    attn_map = weights[0, center_idx, :].reshape(int(np.sqrt(N)), int(np.sqrt(N)))
    
    plt.figure(figsize=(10, 4))
    
    plt.subplot(131)
    plt.title("Constraint (Residual)")
    plt.imshow(r[0].numpy(), cmap='bwr')
    plt.colorbar()
    
    plt.subplot(132)
    plt.title("Learned Update Step")
    # Run full model prediction
    pred = model(u, r) # Patch output
    # Reconstruction logic needed? 
    # For viz, valid output is fine.
    plt.text(0.5, 0.5, "Prediction", ha='center')
    
    plt.subplot(133)
    plt.title("Attention Map (Green's Function)")
    plt.imshow(attn_map.numpy(), cmap='viridis')
    plt.colorbar()
    
    plt.tight_layout()
    plt.savefig("newton_results/newton_viz.png")
    print("✅ Saved visualization to newton_results/newton_viz.png")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, default="data/newton/debug_2d/poisson_2d_jacobi.npz")
    parser.add_argument("--model_dir", type=str, default="newton_results/checkpoints")
    args = parser.parse_args()
    
    visualize_attention(args)
