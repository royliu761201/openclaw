import torch
import torch.nn as nn
import torch.nn.functional as F

class DeepONet(nn.Module):
    """
    Standard DeepONet architecture for operator learning.
    Branch network: maps inputs (a) to latent space.
    Trunk network: maps coordinates (z) to latent space.
    """
    def __init__(self, branch_dim, trunk_dim, hidden_dim=128, p_out=64):
        super().__init__()
        self.branch = nn.Sequential(
            nn.Linear(branch_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, p_out)
        )
        self.trunk = nn.Sequential(
            nn.Linear(trunk_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, p_out)
        )
        self.bias = nn.Parameter(torch.zeros(1))

    def forward(self, a, z):
        # a: (batch, branch_dim)
        # z: (num_points, trunk_dim)
        b_out = self.branch(a) # (batch, p_out)
        t_out = self.trunk(z)  # (num_points, p_out)
        
        # Inner product between branch outputs and trunk outputs
        # out: (batch, num_points)
        out = torch.einsum('bi, pi -> bp', b_out, t_out)
        return out + self.bias

class RiskNOModel(nn.Module):
    """
    Risk-NO wrapper incorporating the variational CVaR threshold zeta.
    """
    def __init__(self, branch_dim, trunk_dim, alpha=0.95):
        super().__init__()
        self.operator = DeepONet(branch_dim, trunk_dim)
        # zeta is the learnable Value-at-Risk (VaR) threshold
        self.zeta = nn.Parameter(torch.tensor(0.0))
        self.alpha = alpha

    def forward(self, a, z):
        return self.operator(a, z)

    def compute_risk_loss(self, regret):
        """
        Rockafellar & Uryasev (2000) variational representation of CVaR.
        regret: (batch,) tensor of safety-critical violations.
        """
        # Loss = zeta + E[ (regret - zeta)_+ ] / (1 - alpha)
        penalty = torch.mean(F.relu(regret - self.zeta))
        return self.zeta + penalty / (1.0 - self.alpha)
