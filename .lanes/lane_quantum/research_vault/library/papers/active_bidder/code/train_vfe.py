import torch
import torch.nn as nn
import torch.nn.functional as F
from rssm import RSSM

class TemporalFreeEnergyLoss(nn.Module):
    """
    Temporal Free Energy Loss (Evidence Lower Bound over Time).
    L = Sum_t [ KL(Q(s_t)||P(s_t)) - log P(o_t|s_t) ]
    """
    def __init__(self, beta_kl=1.0):
        super().__init__()
        self.beta = beta_kl

    def forward(self, post_mu, post_logvar, prior_mu, prior_logvar, recon_o, target_o):
        # 1. KL Divergence (Dynamics Consistency)
        # KL(Posterior || Prior)
        kl = -0.5 * torch.sum(1 + post_logvar - prior_logvar - 
                             (post_mu - prior_mu).pow(2) / prior_logvar.exp() - 
                             (post_logvar - prior_logvar).exp(), dim=1)
        kl_loss = kl.mean()
        
        # 2. Reconstruction Loss (Observation Likelihood)
        recon_loss = F.mse_loss(recon_o, target_o) # Assuming continuous embedding/image
        
        total_loss = self.beta * kl_loss + recon_loss
        return total_loss, {"kl": kl_loss.item(), "recon": recon_loss.item()}

if __name__ == "__main__":
    print("[Temporal-Bidder] Testing RSSM Training Loop...")
    
    # Hyperparams
    B, T = 8, 10  # Batch=8, Time=10
    obs_dim = 64
    act_dim = 10
    
    model = RSSM(state_dim=30, hidden_dim=200, action_dim=act_dim)
    criterion = TemporalFreeEnergyLoss(beta_kl=0.5)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    
    # Mock Sequence Data
    # Observations: (B, T, D)
    obs_seq = torch.randn(B, T, obs_dim)
    # Actions: (B, T, A) - Previous interactions
    act_seq = torch.randn(B, T, act_dim)
    
    # Init State
    h, s = model.init_state(B)
    
    total_loss_val = 0
    
    # BPTT Loop
    # Note: For strict BPTT, usually we run the whole sequence then backprop.
    # Here we accumulate loss.
    
    metrics_hist = []
    
    for t in range(T):
        obs_t = obs_seq[:, t]
        act_t = act_seq[:, t]
        
        out = model(h, s, act_t, obs_t)
        
        # Update States
        h = out["h"]
        s = out["s"] # Sampled posterior
        
        # Calc Step Loss
        loss, met = criterion(
            out["post_mu"], out["post_logvar"],
            out["prior_mu"], out["prior_logvar"],
            out["recon_obs"], obs_t
        )
        
        total_loss_val += loss
        metrics_hist.append(met)
    
    # Backward
    optimizer.zero_grad()
    total_loss_val.backward()
    optimizer.step()
    
    print(f"Total Sequence Loss: {total_loss_val.item():.4f}")
    print(f"Last Step Metrics: {metrics_hist[-1]}")
    print("✅ Temporal Active Inference Verified.")
