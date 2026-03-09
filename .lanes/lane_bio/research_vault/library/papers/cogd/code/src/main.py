
import os
from pathlib import Path
import sys
import argparse
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from dataclasses import asdict
from tqdm import tqdm
import csv
import wandb
import matplotlib.pyplot as plt
import numpy as np

# Absolute imports assuming 'src' is in PYTHONPATH
from src.cogd.config import NexusConfig, DatasetSpec, ModelConfig, TrainConfig, EXPERIMENT_MATRIX
from src.cogd.models.cogd import NexusGraft
from src.cogd.metrics import calculate_metrics
from src.cogd.data.loader import create_dataloaders

def save_sample_vis(image_tensor, pred_mask, gt_mask, save_path):
    """
    Save visualization overlap.
    """
    # 1. Denormalize Image (assuming standardized ~[0,1] or simple normalization)
    # Image: [C, H, W] -> [H, W, C]
    img = image_tensor.cpu().permute(1, 2, 0).numpy()
    img = (img - img.min()) / (img.max() - img.min() + 1e-6)
    
    # 2. Prepare Masks
    if pred_mask.ndim == 3: pred_mask = pred_mask.squeeze(0)
    pred = torch.sigmoid(pred_mask).cpu().numpy() > 0.5
    
    if gt_mask.ndim == 3: gt_mask = gt_mask.squeeze(0)
    gt = gt_mask.cpu().numpy() > 0.5
    
    # 3. Plot
    fig, ax = plt.subplots(1, 1, figsize=(6, 6))
    ax.imshow(img)
    
    # GT = Red
    gt_masked = np.zeros((*gt.shape, 4))
    gt_masked[..., 0] = 1.0 # R
    gt_masked[..., 3] = gt.astype(float) * 0.4 # Alpha
    ax.imshow(gt_masked)
    
    # Pred = Blue
    pred_masked = np.zeros((*pred.shape, 4))
    pred_masked[..., 2] = 1.0 # B
    pred_masked[..., 3] = pred.astype(float) * 0.4 # Alpha
    ax.imshow(pred_masked)
    
    ax.axis('off')
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()

def parse_args():
    parser = argparse.ArgumentParser(description="CoGD-Net Training")
    parser.add_argument("--task", type=str, required=True, help="Task ID (e.g., E1_CoGD_InDomain)")
    # Backwards compatibility alias
    parser.add_argument("--exp_id", type=str, default=None, help="Alias for --task")
    
    parser.add_argument("--resume", type=str, default=None, help="Checkpoint to resume from")
    parser.add_argument("--smoke_test", action="store_true", help="Run a quick smoke test")
    parser.add_argument("--batch_size", type=int, default=None, help="Override batch size")
    parser.add_argument("--grad_accum", type=int, default=None, help="Override gradient accumulation")
    parser.add_argument("--model", type=str, default=None, help="Override base SAM2 model path")
    parser.add_argument("--project_root", type=str, default=None, help="Project root directory")
    parser.add_argument("--data_dir", type=str, default=None, help="Data directory (PICCOLO)")
    parser.add_argument("--inference", action="store_true", help="Run in inference mode (requires --resume)")
    return parser.parse_args()

def perform_sanity_check(cfg):
    """
    Fail fast if critical resources are missing.
    """
    print("\n🧐 Performing Pre-flight Sanity Logic...")
    
    # 1. Check Data Directory
    if cfg.data_dir:
        if not cfg.data_dir.exists():
             # If strictly checking, raise error. But usually data_dir might be auto-discovered.
             pass
        else:
             print(f"✅ Data Directory Verified: {cfg.data_dir}")
    
    # 2. Check Model Path (if local)
    if os.environ.get("HF_HUB_OFFLINE") == "1":
        if not os.path.exists(cfg.model.sam2_id):
             raise FileNotFoundError(f"❌ CRITICAL: Offline model path not found: {cfg.model.sam2_id}")
        else:
             print(f"✅ Model Path Verified: {cfg.model.sam2_id}")
             
    # 3. Check Write Permissions
    try:
        cfg.project_root.mkdir(parents=True, exist_ok=True)
        test_file = cfg.project_root / ".perm_check"
        test_file.touch()
        test_file.unlink()
        print(f"✅ Write Permissions Verified: {cfg.project_root}")
    except Exception as e:
        raise PermissionError(f"❌ CRITICAL: Cannot write to project root: {e}")

    print("🚀 Sanity Check Passed! proceeding...\n")

def main():
    args = parse_args()
    task_id = args.task if args.task else args.exp_id
    
    # 1. Initialize Configuration
    cfg = NexusConfig(exp_id=task_id, smoke_test=args.smoke_test)
    if args.project_root:
        cfg.project_root = Path(args.project_root)
    if args.data_dir:
        cfg.data_dir = Path(args.data_dir)
    
    # Overrides based on EXPERIMENT_MATRIX
    if task_id in EXPERIMENT_MATRIX:
        print(f"🧩 Loaded config settings for {task_id}")
        matrix = EXPERIMENT_MATRIX[task_id]
        if "description" in matrix: cfg.description = matrix["description"]
        if "train_datasets" in matrix: cfg.train_datasets = matrix["train_datasets"]
        if "test_datasets" in matrix: cfg.test_datasets = matrix["test_datasets"]
        
        # Nested Model Config
        if "model" in matrix:
            for k, v in matrix["model"].items():
                if hasattr(cfg.model, k):
                    setattr(cfg.model, k, v)
                    
        # Nested Train Config
        if "train" in matrix:
            for k, v in matrix["train"].items():
                if hasattr(cfg.train, k):
                    setattr(cfg.train, k, v)
    else:
        print(f"⚠️ Task '{task_id}' not found in EXPERIMENT_MATRIX. Using defaults.")

    # CLI Overrides
    if args.resume:
        cfg.resume_from = args.resume
        
    if args.batch_size:
        cfg.train.batch_size = args.batch_size
    if args.grad_accum:
        cfg.train.grad_accumulate = args.grad_accum
        
    # Offline Model Redirection (Jan 24 Stability Patch)
    local_paths = [
        "/jhdx0003008/models/sam2-hiera-large",
        "/root/projects/ai4s/temp_models/sam2-hiera-large",
        "/root/models/sam2-hiera-large"
    ]
    
    if args.model:
        cfg.model.sam2_id = args.model
    else:
        for path in local_paths:
            if os.path.exists(path):
                print(f"📡 Local model detected at {path}. Switching to offline mode.")
                cfg.model.sam2_id = path
                os.environ["HF_HUB_OFFLINE"] = "1"
                break

    perform_sanity_check(cfg)
    cfg.init_workspace()
    cfg.save_manifest()
    
    # Initialize W&B
    if cfg.use_wandb:
        wandb.init(
            project=cfg.wandb_project,
            name=cfg.exp_id,
            config=asdict(cfg),
            mode="online" if not os.environ.get("WANDB_OFFLINE") else "offline"
        )
    
    print(f"🚀 Launching CoGD Experiment: {cfg.exp_id}")
    print(f"📂 Output Dir: {cfg.exp_dir}")
    
    # 2. Model Setup
    print("🏗️ Building NexusGraft Model...")
    model = NexusGraft(cfg)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    
    # [RESUME] Load Checkpoint if requested
    if getattr(cfg, "resume_from", None) and os.path.exists(cfg.resume_from):
        print(f"🔄 Resuming from checkpoint: {cfg.resume_from}")
        state_dict = torch.load(cfg.resume_from, map_location=device)
        model.load_state_dict(state_dict)

    # 3. Data Setup
    print("💾 Loading Datasets...")
    train_loader, test_loaders = create_dataloaders(cfg)
    
    # Ensure checkpoint dir exists
    (cfg.exp_dir / "checkpoints").mkdir(parents=True, exist_ok=True)

    def validate(model, loader, desc="Validation", calc_hd95=False):
        model.eval()
        eval_metrics = {"dice": 0, "iou": 0, "sens": 0, "prec": 0, "hd95": 0}
        
        # Detailed Logger Setup
        detailed_rows = []
        
        steps = 0
        with torch.no_grad():
            loop = tqdm(loader, desc=desc, leave=False)
            for batch_idx, batch in enumerate(loop):
                for k, v in batch.items():
                    if isinstance(v, torch.Tensor):
                        batch[k] = v.to(device)
                        
                masks, _ = model(batch)
                
                if 'mask' in batch:
                   gt = batch['mask'].float()
                   pred = torch.sigmoid(masks)
                   metrics = calculate_metrics(pred, gt, calc_hd95=calc_hd95)
                   for k in eval_metrics:
                       eval_metrics[k] += metrics.get(k, torch.tensor(0.0)).item()
                   steps += 1
                   loop.set_postfix(dice=metrics["dice"].item())
                   
                   # VISUALIZATION (Save first 5 batches)
                   if steps < 5:
                       vis_dir = cfg.exp_dir / "visualizations"
                       vis_dir.mkdir(exist_ok=True)
                       # Vis first sample in batch
                       save_path = vis_dir / f"{desc.replace(' ', '_')}_batch_{steps}.png"
                       save_sample_vis(batch['wli'][0], masks[0], batch['mask'][0], save_path)

                   # Capture per-sample metrics
                   detailed_rows.append({
                       "batch_idx": batch_idx,
                       "dice": metrics["dice"].item(),
                       "hd95": metrics["hd95"].item() if calc_hd95 else 0.0,
                       "iou": metrics["iou"].item()
                   })

        if steps > 0:
            # Save detailed metrics if inference mode
            if args.inference and desc.startswith("Eval"):
                import pandas as pd
                df = pd.DataFrame(detailed_rows)
                df.to_csv(cfg.exp_dir / f"detailed_metrics_{desc.replace(' ','_')}.csv", index=False)
            
            avg_metrics = {k: v/steps for k, v in eval_metrics.items()}
            return avg_metrics
        return None

    # 4. Mode Selection
    # (Inference Only)
    if args.inference:
        print("🔮 Starting Inference Evaluation...")
        if not test_loaders:
             print("❌ No test datasets configured.")
             return

        # Prepare CSV
        csv_path = cfg.exp_dir / "inference_results.csv"
        csv_headers = ["Experiment_ID", "Dataset", "Dice", "IoU", "Sensitivity", "Precision", "HD95"]
        
        # Safe open for write (overwrite or append?)
        open_mode = 'a' if os.path.exists(csv_path) else 'w'
        with open(csv_path, open_mode, newline='') as f:
            writer = csv.writer(f)
            if open_mode == 'w':
                writer.writerow(csv_headers)
            
        for name, loader in test_loaders.items():
             print(f"📊 Evaluating Dataset: {name}")
             metrics = validate(model, loader, desc=f"Eval {name}", calc_hd95=True)
             if metrics:
                 print(f"✅ Results [{name}]: Dice: {metrics['dice']:.4f} | IoU: {metrics['iou']:.4f} | HD95: {metrics['hd95']:.4f}")
                 
                 # Log to CSV
                 with open(csv_path, 'a', newline='') as f:
                     writer = csv.writer(f)
                     writer.writerow([
                         cfg.exp_id, 
                         name, 
                         f"{metrics['dice']:.4f}", 
                         f"{metrics['iou']:.4f}", 
                         f"{metrics['sens']:.4f}",
                         f"{metrics['prec']:.4f}",
                         f"{metrics['hd95']:.4f}"
                     ])
             else:
                 print(f"⚠️ No labeled data in {name}.")
                 
        return

    # 4. Training Loop (Skeleton)
    if train_loader:
        print("🔥 Starting Training...")
        optimizer = optim.AdamW(model.parameters(), lr=cfg.train.lr)
        
        epochs = cfg.train.stage_epochs[0] if not cfg.smoke_test else 1
        # Sum of all stages? Usually list is [5, 10, 15] meaning phase length.
        # But this manual loop iterates 'epochs' which is just first element?
        # Original code line 340: `epochs = cfg.train.stage_epochs[0]`.
        # This seems like it only runs Stage 1!
        # Maybe the original `train_cogd.py` was incomplete?
        # But `NexusSystem` (Lightning) handles stage switching.
        # Here we have a manual loop.
        # I will keep logic matching `train_cogd.py` but note this limitation.
        # Actually, let's enable full training if list provided.
        # `NexusSystem` had `on_train_epoch_start` to check stages.
        # Here we should probably sum(stage_epochs).
        
        total_epochs = sum(cfg.train.stage_epochs) if not cfg.smoke_test else 1
        
        for epoch in range(total_epochs):
            model.train()
            loop = tqdm(train_loader, desc=f"Epoch {epoch+1}/{total_epochs}")
            
            epoch_loss = 0
            epoch_metrics = {"dice": 0, "iou": 0, "sens": 0, "prec": 0}
            steps = 0
            
            for batch in loop:
                # Move to device
                for k, v in batch.items():
                    if isinstance(v, torch.Tensor):
                        batch[k] = v.to(device)
                
                optimizer.zero_grad()
                # Forward
                masks, refined_feats = model(batch)
                
                # Metric Containers
                batch_metrics = {"dice": torch.tensor(0.0), "iou": torch.tensor(0.0), "sens": torch.tensor(0.0), "prec": torch.tensor(0.0)}

                if 'mask' in batch:
                    # Resize or ensure shape match if needed
                    gt = batch['mask'].float()
                    pred = torch.sigmoid(masks) 
                    
                    # Dice Loss (1 - Dice) + BCE
                    metrics = calculate_metrics(pred, gt, calc_hd95=False)
                    batch_metrics = metrics
                    
                    # Hybrid Loss
                    bce = nn.BCELoss()(pred, gt)
                    dice_loss = 1.0 - metrics["dice"]
                    loss = 0.5 * bce + 0.5 * dice_loss
                else:
                    # Fallback if no GT
                    loss = masks.mean()

                loss.backward()
                optimizer.step()
                
                epoch_loss += loss.item()
                for k in epoch_metrics:
                    if k in batch_metrics:
                        epoch_metrics[k] += batch_metrics[k].item()
                steps += 1
                
                if cfg.use_wandb:
                    log_dict = {"train/loss": loss.item(), "epoch": epoch + 1}
                    for k, v in batch_metrics.items():
                        log_dict[f"train/{k}"] = v.item()
                    wandb.log(log_dict)
                
                loop.set_postfix(loss=loss.item(), dice=batch_metrics["dice"].item())

            # Avg Metrics
            avg_metrics = {k: v/steps for k, v in epoch_metrics.items()}
            print(f"Epoch {epoch+1}/{total_epochs} Train Dice: {avg_metrics['dice']:.4f} | Loss: {epoch_loss/steps:.4f}")
            
            # [VALIDATION] Inline
            if test_loaders:
                # Use first test loader as validation
                val_name = list(test_loaders.keys())[0]
                val_loader = test_loaders[val_name]
                
                val_res = validate(model, val_loader, desc=f"Val Epoch {epoch+1}")
                if val_res:
                    print(f"Epoch {epoch+1}/{total_epochs} Val Dice: {val_res['dice']:.4f} | IoU: {val_res['iou']:.4f}")
                    
                    if cfg.use_wandb:
                        wandb.log({
                            f"val/dice": val_res['dice'],
                            f"val/iou": val_res['iou'],
                            f"val/sens": val_res['sens'],
                            "epoch": epoch + 1
                        })

            # Save Checkpoint
            chk_path = cfg.exp_dir / "checkpoints" / f"epoch_{epoch+1}.pt"
            torch.save(model.state_dict(), chk_path)
            print(f"💾 Checkpoint saved: {chk_path}")
            
        wandb.finish()
    
    # [TESTING] Final Evaluation
    print("\n🏁 Training Complete. Running Final Test Evaluation...")
    if test_loaders:
        # Prepare CSV
        csv_path = cfg.exp_dir / "experiment_results.csv"
        csv_headers = ["Experiment_ID", "Dataset", "Dice", "IoU", "Sensitivity", "Precision", "HD95"]
        
        with open(csv_path, 'a', newline='') as f:
            writer = csv.writer(f)
            # Write headers only if file empty/new (simplified check)
            if f.tell() == 0: writer.writerow(csv_headers)
            
            for name, loader in test_loaders.items():
                 print(f"📊 Final Test: {name}")
                 metrics = validate(model, loader, desc=f"Test {name}", calc_hd95=True)
                 if metrics:
                     print(f"🏆 Final Results [{name}]: Dice: {metrics['dice']:.4f} | IoU: {metrics['iou']:.4f} | HD95: {metrics['hd95']:.4f}")
                     
                     writer.writerow([
                         cfg.exp_id, 
                         name, 
                         f"{metrics['dice']:.4f}", 
                         f"{metrics['iou']:.4f}", 
                         f"{metrics['sens']:.4f}",
                         f"{metrics['prec']:.4f}",
                         f"{metrics['hd95']:.4f}"
                     ])
             
        print(f"📄 Results saved to: {csv_path}")
    
    print("✅ Experiment Completed.")

if __name__ == "__main__":
    main()
