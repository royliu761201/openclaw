import torch
import torch.nn as nn
import torch.optim as optim
import wandb
import os
import argparse
import numpy as np
from model import GateDeepONet
from data import get_dataloaders
import yaml
from datetime import datetime

def train_stage1(args):
    # 1. Initialize W&B
    wandb.init(project="GibbsNeural", name=f"Stage1_{args.task}", config=args)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    # 2. Setup Data
    train_loader, test_loader, ds = get_dataloaders(args.data_root, task=args.task, mode='mollified', batch_size=args.batch_size)
    nx = 256 # Grid size
    x_coords = torch.linspace(0, 1, nx).view(-1, 1).to(device)
    
    # 3. Build Model
    model = GateDeepONet(p_dim=5, x_dim=1).to(device)
    optimizer = optim.Adam(model.parameters(), lr=args.lr)
    criterion = nn.MSELoss()
    
    print(f"🚀 Starting Stage 1 Training on {args.task}...")
    
    # 4. Training Loop
    for epoch in range(args.epochs):
        model.train()
        train_loss = 0
        for batch in train_loader:
            p = batch['params'].to(device)
            target = batch['targets'].to(device) # (B, N)
            
            optimizer.zero_grad()
            # Only train backbone in Stage 1
            u_back = model.forward_backbone(p, x_coords)
            loss = criterion(u_back, target)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
            
        # Validation
        model.eval()
        val_loss = 0
        with torch.no_grad():
            for batch in test_loader:
                p = batch['params'].to(device)
                target = batch['targets'].to(device)
                u_back = model.forward_backbone(p, x_coords)
                val_loss += criterion(u_back, target).item()
        
        train_loss /= len(train_loader)
        val_loss /= len(test_loader)
        
        wandb.log({"epoch": epoch, "train_loss": train_loss, "val_loss": val_loss})
        
        if (epoch+1) % 10 == 0:
            print(f"Epoch {epoch+1}/{args.epochs} - Val Loss: {val_loss:.6f}")

    # 5. Save Model to NAS
    model_dir = os.path.join(args.data_root, "models")
    os.makedirs(model_dir, exist_ok=True)
    save_path = os.path.join(model_dir, f"stage1_backbone_{args.task}.pth")
    torch.save(model.state_dict(), save_path)
    
    # Save training metadata
    run_info = {
        "stage": 1,
        "task": args.task,
        "epochs": args.epochs,
        "final_val_loss": val_loss,
        "timestamp": datetime.now().isoformat()
    }
    with open(os.path.join(model_dir, f"stage1_{args.task}_info.yaml"), 'w') as f:
        yaml.dump(run_info, f)
        
    print(f"✅ Stage 1 Training Complete. Model saved to {save_path}")
    wandb.finish()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_root", type=str, default="./data")
    parser.add_argument("--task", type=str, default="sod", choices=["sod", "blast"])
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--batch_size", type=int, default=64)
    parser.add_argument("--lr", type=float, default=1e-3)
    args = parser.parse_args()
    train_stage1(args)
