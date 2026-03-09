import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
import argparse

# Mock Crystal Structure Dataset
class CarbonDataset(Dataset):
    def __init__(self, size=500, atom_count=8):
        self.size = size
        self.data = torch.randn(size, atom_count, 3) # Positions
        self.y = torch.randn(size, 1) # Energy

    def __len__(self):
        return self.size

    def __getitem__(self, idx):
        return self.data[idx], self.y[idx]

# Simple Invariant Network (Mock GNN)
class CarbonNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.encoder = nn.Linear(3, 16)
        self.head = nn.Linear(16, 1)

    def forward(self, x):
        # x: [B, Atoms, 3]
        feat = self.encoder(x) # [B, A, 16]
        # Mean pooling (invariant to permutation)
        pool = feat.mean(dim=1) # [B, 16]
        return self.head(pool)

def train(args):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"💎 Carbon Evolution Baseline | Device: {device} | Epochs: {args.epochs}")

    ds = CarbonDataset()
    loader = DataLoader(ds, batch_size=args.batch_size)
    
    model = CarbonNet().to(device)
    optimizer = optim.Adam(model.parameters(), lr=1e-3)
    criterion = nn.MSELoss()

    for epoch in range(args.epochs):
        total_loss = 0
        for x, y in loader:
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad()
            pred = model(x)
            loss = criterion(pred, y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        
        print(f"Epoch {epoch+1}: Loss = {total_loss / len(loader):.4f}")

    print("✅ Carbon Evolution Training Complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch_size", type=int, default=16)
    args = parser.parse_args()
    train(args)
