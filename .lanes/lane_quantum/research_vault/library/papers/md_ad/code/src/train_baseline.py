import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
import numpy as np
import argparse

# Mock Dataset: Molecular Dynamics Trajectories
class ThermodynamicDataset(Dataset):
    def __init__(self, size=1000, seq_len=20, atoms=5):
        self.size = size
        self.seq_len = seq_len
        self.atoms = atoms
        # Random "molecular" states: [Size, Seq, Atoms, 3]
        self.data = torch.randn(size, seq_len, atoms * 3)
        self.temp = torch.rand(size, 1) * 1000 # Temperature 0-1000K

    def __len__(self):
        return self.size

    def __getitem__(self, idx):
        # Input: Past trajectory + Temp
        # Target: Next frame prediction (simple shift for mock)
        seq = self.data[idx]
        temp = self.temp[idx]
        return seq[:-1], temp, seq[1:]

class MDADTransformer(nn.Module):
    def __init__(self, input_dim, d_model=64, nhead=4, num_layers=2):
        super().__init__()
        self.embedding = nn.Linear(input_dim, d_model)
        self.temp_embed = nn.Linear(1, d_model)
        self.transformer = nn.Transformer(d_model, nhead, num_layers, batch_first=True)
        self.head = nn.Linear(d_model, input_dim)

    def forward(self, x, temp):
        # x: [B, T, D]
        # temp: [B, 1] -> [B, 1, D]
        emb = self.embedding(x)
        t_emb = self.temp_embed(temp).unsqueeze(1).expand(-1, x.size(1), -1)
        src = emb + t_emb
        out = self.transformer(src, src) # Self-attention
        return self.head(out)

def train(args):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"🚀 MD-AD Baseline | Device: {device} | Epochs: {args.epochs}")

    ds = ThermodynamicDataset()
    loader = DataLoader(ds, batch_size=args.batch_size, shuffle=True)
    
    model = MDADTransformer(input_dim=15).to(device)
    optimizer = optim.Adam(model.parameters(), lr=1e-3)
    criterion = nn.MSELoss()

    for epoch in range(args.epochs):
        total_loss = 0
        for x, temp, y in loader:
            x, temp, y = x.to(device), temp.to(device), y.to(device)
            optimizer.zero_grad()
            pred = model(x, temp)
            loss = criterion(pred, y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        
        print(f"Epoch {epoch+1}: Loss = {total_loss / len(loader):.4f}")

    print("✅ MD-AD Training Complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--batch_size", type=int, default=32)
    args = parser.parse_args()
    train(args)
