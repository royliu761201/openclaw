
import os
import torch
import torch.nn as nn
from torch.nn import functional as F
from torch.utils.data import Dataset, DataLoader
import json
import argparse
from tqdm import tqdm
from src.poker_ad.model import PokerAD, PokerADConfig

class PokerTrajectoryDataset(Dataset):
    """
    Dataset for Poker-AD.
    Loads JSON trajectories and tokenizes them.
    Each item is a context window of tokens.
    """
    def __init__(self, data_path, vocab_size=100, block_size=1024):
        self.data = self._load_data(data_path)
        self.vocab_size = vocab_size
        self.block_size = block_size
        # TODO: Implement proper tokenizer.
        # For Leduc, actions are limited (Checker, Call, Bet, Fold).
        # Cards are limited (J, Q, K).
        # We need a mapping.
        
    def _load_data(self, path):
        if not os.path.exists(path):
            print(f"⚠️ Data file {path} not found. Generating SYNTHETIC data.")
            # Generate 100 fake trajectories
            return [{"context": [1]*10} for _ in range(100)]
        with open(path) as f:
            return json.load(f)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        # Placeholder for real processing
        # Returns inputs, targets, mask
        # Ideally we sample a random chunk from a trajectory
        return torch.zeros(self.block_size, dtype=torch.long), torch.zeros(self.block_size, dtype=torch.long), torch.zeros(self.block_size)

def train(args):
    # Config
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    config = PokerADConfig(
        vocab_size=args.vocab_size,
        block_size=args.block_size,
        n_layer=args.n_layer,
        n_head=args.n_head,
        n_embd=args.n_embd
    )
    
    # Model
    model = PokerAD(config).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr)
    
    # Data (Mock for now until real data arrives)
    dataset = PokerTrajectoryDataset(args.data_path, args.vocab_size, args.block_size)
    loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True)
    
    print(f"🚀 Starting Training on {device}...")
    model.train()
    
    for epoch in range(args.epochs):
        pbar = tqdm(loader)
        for x, y, mask in pbar:
            x, y, mask = x.to(device), y.to(device), mask.to(device)
            
            logits, loss = model(x, y, mask)
            
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            pbar.set_description(f"Epoch {epoch} | Loss: {loss.item():.4f}")
            
        # Save Checkpoint
        torch.save(model.state_dict(), f"{args.ckpt_dir}/model_epoch_{epoch}.pt")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_path", type=str, default="data/poker_ad/raw/pilot_batch.json")
    parser.add_argument("--ckpt_dir", type=str, default="checkpoints/poker_ad")
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=3e-4)
    # Model Config
    parser.add_argument("--vocab_size", type=int, default=100)
    parser.add_argument("--block_size", type=int, default=1024)
    parser.add_argument("--n_layer", type=int, default=4)
    parser.add_argument("--n_head", type=int, default=4)
    parser.add_argument("--n_embd", type=int, default=256)
    
    args = parser.parse_args()
    os.makedirs(args.ckpt_dir, exist_ok=True)
    train(args)
