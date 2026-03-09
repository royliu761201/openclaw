import torch
import torch.optim as optim
import torch.nn as nn

def train_risk_no(model, 
                  data_loader, 
                  z, 
                  v_limit, 
                  lambda_p=0.2, 
                  lambda_r=0.1, 
                  epochs=1500, 
                  tw=300):
    """
    Main training loop for Risk-NO.
    
    Args:
        model: RiskNOModel instance.
        data_loader: DataLoader yielding (a, u_gt).
        z: Coordinates (num_points, trunk_dim).
        v_limit: Safety threshold for peak values.
        lambda_p: Weight for PDE residual loss.
        lambda_r: Weight for Risk loss.
        epochs: Number of training epochs.
        tw: Risk warm-up start epoch.
    """
    optimizer = optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-5)
    mse_fn = nn.MSELoss()
    
    model.train()
    for epoch in range(epochs):
        epoch_mse = 0
        epoch_risk = 0
        num_batches = 0
        
        for a, u_gt in data_loader:
            optimizer.zero_grad()
            
            # 1. Forward pass
            u_pred = model(a, z)
            
            # 2. Fidelity Loss (MSE)
            loss_mse = mse_fn(u_pred, u_gt)
            
            # 3. PDE Residual Loss (Simplified for this version)
            # In a full PINO, this involves autograd-based derivatives of u_pred w.r.t z
            # Here we use a curvature penalty as a proxy for the wave equation
            loss_pde = torch.mean(torch.diff(u_pred, n=2, dim=1)**2)
            
            # 4. Risk Loss (CVaR on Regret)
            # Regret definition: Ground peak > limit AND prediction < ground peak
            u_max_gt = torch.max(u_gt, dim=1)[0]
            u_max_pred = torch.max(u_pred, dim=1)[0]
            
            # Dangerous samples are those exceeding the safety limit
            is_danger = (u_max_gt > v_limit).float()
            # Positive regret = under-estimation on dangerous samples
            regret = is_danger * torch.clamp(u_max_gt - u_max_pred, min=0)
            
            loss_risk = model.compute_risk_loss(regret)
            
            # Weighting and Warm-up
            curr_lambda_r = lambda_r if epoch > tw else 0.0
            
            loss_total = loss_mse + lambda_p * loss_pde + curr_lambda_r * loss_risk
            
            loss_total.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            
            epoch_mse += loss_mse.item()
            epoch_risk += loss_risk.item()
            num_batches += 1
            
        if epoch % 100 == 0:
            avg_mse = epoch_mse / num_batches
            avg_risk = epoch_risk / num_batches
            print(f"Epoch {epoch:4d} | MSE: {avg_mse:.6f} | Risk: {avg_risk:.6f} | Zeta: {model.zeta.item():.4f}")

    print("Training Complete.")

if __name__ == "__main__":
    # Dummy Main for Risk-No
    import sys
    # Mock RiskNOModel since we cannot import it easily without src path setup
    class RiskNOConfig: pass
    class RiskNOModel(nn.Module):
        def __init__(self, c): super().__init__(); self.zeta = torch.tensor(0.5); self.layer = nn.Linear(2,1)
        def forward(self, a, z): 
            # Output shape must be (batch, trunk_dim) = (batch, 64)
            # z is (64, 2)
            return torch.randn(a.shape[0], 64) 
        def compute_risk_loss(self, r): return torch.mean(r)

    # Mock Data
    class MockDataset(torch.utils.data.Dataset):
        def __init__(self):
            # a: (10, ?) -> let's say (10, 1)
            self.data = torch.randn(100, 1)
            # u_gt: (10, 64)
            self.targets = torch.randn(100, 64)
        def __len__(self): return 100
        def __getitem__(self, idx): return self.data[idx], self.targets[idx]

    loader = torch.utils.data.DataLoader(MockDataset(), batch_size=16)
    
    config = RiskNOConfig()
    model = RiskNOModel(config)
    
    # Mock Z coordinates
    z = torch.randn(64, 2) 
    
    print("🚀 Starting Risk-No Training (Synthetic Mode)...")
    train_risk_no(model, loader, z, v_limit=1.0, epochs=100)
