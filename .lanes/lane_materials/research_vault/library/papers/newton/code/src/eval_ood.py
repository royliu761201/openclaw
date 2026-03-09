import torch
import torch.nn as nn
import numpy as np
import argparse
from torch.utils.data import DataLoader
from src.newton.model import NewtonTransformer, Config, ConfigLarge, Normalizer
from train_newton import load_data, patchify_target

def evaluate(args):
    dataset = load_data(args.data, dim=2)
    loader = DataLoader(dataset, batch_size=args.batch_size)
    
    # Load Norm Stats
    norm_path = f"{args.model_dir}/norm_stats.pt"
    try:
        stats = torch.load(norm_path, weights_only=False)
        norm_u = stats["u"]
        norm_r = stats["r"]
        norm_d = stats["d"]
        print(f"📊 Loaded Normalization Stats")
    except FileNotFoundError:
        print("⚠️ Norm stats not found! Results will be garbage.")
        return

    cfg = Config() if not args.large else ConfigLarge()
    
    # Model Selection
    if args.model == "newton":
        model = NewtonTransformer(cfg)
    elif args.model == "unet":
        from src.newton.baselines import UNet2D
        model = UNet2D()
    elif args.model == "fno":
        from src.newton.baselines import FNO2d
        model = FNO2d(modes1=12, modes2=12, width=32)
    else:
        raise ValueError(f"Unknown model: {args.model}")
    
    chk_path = f"{args.model_dir}/{args.model}_v1.pt"
    try:
        model.load_state_dict(torch.load(chk_path, map_location="cpu"))
    except FileNotFoundError:
        print(f"❌ Checkpoint not found: {chk_path}")
        return

    print(f"✅ Loaded {args.model} from {chk_path}")
    model.eval()
    
    criterion = nn.MSELoss()
    total_loss = 0
    steps = 0
    
    with torch.no_grad():
        for u, r, target in loader:
            # Normalize Input
            u_norm = norm_u.encode(u)
            r_norm = norm_r.encode(r)
            
            # Predict
            pred_norm = model(u_norm, r_norm)
            
            # Unnormalize Prediction (to compare in physical space? Or normalized space?)
            # Usually we compare in normalized space for Loss, but Physical for interpreted error.
            # Let's check MSE in Normalized space first (consistent with training loss).
            target_norm = norm_d.encode(target)
            target_patches = patchify_target(target_norm, cfg.patch_size, 2)
            
            loss = criterion(pred_norm, target_patches)
            total_loss += loss.item()
            steps += 1
            
    avg_loss = total_loss / steps
    print(f"🏆 OOD Evaluation ({args.model}): Norm MSE = {avg_loss:.6f}")
    
    # Baseline: Zero update in Norm Space
    # target_norm roughly N(0,1), so E[x^2] ~ 1.0
    print(f"   (Reference) Zero-Update Norm MSE: ~1.00")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, default="data/newton/ood/pacman_2d_jacobi.npz")
    parser.add_argument("--model_dir", type=str, default="newton_results/checkpoints")
    parser.add_argument("--model", type=str, default="newton", choices=["newton", "unet", "fno"])
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--large", action="store_true")
    args = parser.parse_args()
    
    evaluate(args)
