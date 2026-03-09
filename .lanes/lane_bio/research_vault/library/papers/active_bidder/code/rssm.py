import torch
import torch.nn as nn
import torch.nn.functional as F

class RSSM(nn.Module):
    """
    Recurrent State Space Model (World Model).
    Based on DreamerV3 / Hafner et al.
    
    Structure:
    - h_t = f(h_{t-1}, s_{t-1}, a_{t-1})  [Deterministic Recurrent]
    - s_t ~ P(s_t | h_t)                  [Stochastic Prior]
    - s_t ~ Q(s_t | h_t, e_t)             [Stochastic Posterior]
    """
    def __init__(self, state_dim=30, hidden_dim=200, action_dim=10):
        super().__init__()
        self.state_dim = state_dim
        self.hidden_dim = hidden_dim
        
        # 1. Deterministic Recurrent Cell (GRU)
        # Input: previous stochastic state (s) + action (a)
        self.cell = nn.GRUCell(input_size=state_dim + action_dim, hidden_size=hidden_dim)
        
        # 2. Stochastic Prior Network (Transition)
        # Predicts s_t from h_t (Transition Model)
        self.prior_net = nn.Sequential(
            nn.Linear(hidden_dim, 100),
            nn.ELU(),
            nn.Linear(100, 2 * state_dim) # Mean + LogVar
        )
        
        # 3. Stochastic Posterior Network (Representation)
        # Predicts s_t from h_t + e_t (Observation)
        # Assume embedding e_t is dimension 100
        self.posterior_net = nn.Sequential(
            nn.Linear(hidden_dim + 100, 100),
            nn.ELU(),
            nn.Linear(100, 2 * state_dim) # Mean + LogVar
        )
        
        # 4. Encoder (Observation -> Embedding)
        self.encoder = nn.Sequential(
            nn.Linear(64, 100), # Assume input dim 64
            nn.ELU()
        )
        
        # 5. Decoder (Observation Reconstruction)
        self.decoder = nn.Sequential(
            nn.Linear(state_dim + hidden_dim, 100),
            nn.ELU(),
            nn.Linear(100, 64) # Reconstruct input
        )

    def forward(self, prev_h, prev_s, action, obs):
        """
        Single Step Forward
        """
        # 1. Deterministic Step
        # Concatenate s and a
        rnn_input = torch.cat([prev_s, action], dim=1)
        h = self.cell(rnn_input, prev_h)
        
        # 2. Prior Step (Imagination)
        prior_params = self.prior_net(h)
        prior_mu, prior_logvar = prior_params.chunk(2, dim=1)
        
        # 3. Posterior Step (Observation Integration)
        embed = self.encoder(obs)
        post_input = torch.cat([h, embed], dim=1)
        post_params = self.posterior_net(post_input)
        post_mu, post_logvar = post_params.chunk(2, dim=1)
        
        # 4. Sampling (Reparameterization)
        # During training, we sample from Posterior
        std = torch.exp(0.5 * post_logvar)
        eps = torch.randn_like(std)
        s = post_mu + eps * std
        
        # 5. Reconstruction (decoding from state + recurrent)
        # P(o|s,h)
        recon_input = torch.cat([s, h], dim=1)
        recon_obs = self.decoder(recon_input)
        
        return {
            "h": h,
            "s": s,
            "prior_mu": prior_mu,
            "prior_logvar": prior_logvar,
            "post_mu": post_mu, 
            "post_logvar": post_logvar,
            "recon_obs": recon_obs
        }

    def init_state(self, batch_size):
        device = next(self.parameters()).device
        return (
            torch.zeros(batch_size, self.hidden_dim).to(device),
            torch.zeros(batch_size, self.state_dim).to(device)
        )
