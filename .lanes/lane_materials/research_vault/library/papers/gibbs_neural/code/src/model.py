import torch
import torch.nn as nn
import numpy as np

class MLP(nn.Module):
    def __init__(self, in_dim, out_dim, hidden_dim, depth, activation=nn.Tanh):
        super().__init__()
        layers = []
        layers.append(nn.Linear(in_dim, hidden_dim))
        layers.append(activation())
        for _ in range(depth - 1):
            layers.append(nn.Linear(hidden_dim, hidden_dim))
            layers.append(activation())
        layers.append(nn.Linear(hidden_dim, out_dim))
        self.net = nn.Sequential(*layers)

    def forward(self, x):
        return self.net(x)

class SineLayer(nn.Module):
    def __init__(self, in_features, out_features, bias=True, is_first=False, omega_0=30):
        super().__init__()
        self.omega_0 = omega_0
        self.is_first = is_first
        self.in_features = in_features
        self.linear = nn.Linear(in_features, out_features, bias=bias)
        self.init_weights()

    def init_weights(self):
        with torch.no_grad():
            if self.is_first:
                self.linear.weight.uniform_(-1 / self.in_features, 1 / self.in_features)
            else:
                self.linear.weight.uniform_(-np.sqrt(6 / self.in_features) / self.omega_0, 
                                            np.sqrt(6 / self.in_features) / self.omega_0)

    def forward(self, input):
        return torch.sin(self.omega_0 * self.linear(input))

class SinusoidalTrunk(nn.Module):
    """SIREN-based trunk with learnable spectral viscosity damping"""
    def __init__(self, in_dim, out_dim, hidden_dim, depth, omega_0=30):
        super().__init__()
        self.depth = depth
        self.layers = nn.ModuleList()
        self.layers.append(SineLayer(in_dim, hidden_dim, is_first=True, omega_0=omega_0))
        for _ in range(depth - 1):
            self.layers.append(SineLayer(hidden_dim, hidden_dim, is_first=False, omega_0=omega_0))
        self.final_linear = nn.Linear(hidden_dim, out_dim)
        
        # Learnable spectral viscosity (damping) coefficients for each layer
        self.viscosity = nn.ParameterList([
            nn.Parameter(torch.zeros(1)) for _ in range(depth)
        ])

    def forward(self, x):
        h = x
        for i in range(self.depth):
            h = self.layers[i](h)
            # Apply spectral damping (modulated by learnable viscosity)
            h = h * torch.exp(-torch.relu(self.viscosity[i]) * 1.0) 
        return self.final_linear(h)

class GateDeepONet(nn.Module):
    """
    Discontinuity-Gated Spectral DeepONet.
    Architecture:
    - Backbone: Discrete DeepONet for smooth features.
    - Detail: Spectral-viscous DeepONet for sharp shocks.
    - Gate: Discontinuity sensor.
    """
    def __init__(self, p_dim, x_dim, m_back=128, m_det=128, hidden_dim=128):
        super().__init__()
        # 1. Backbone Branch and Trunk
        self.backbone_branch = MLP(p_dim, m_back, hidden_dim, depth=3)
        self.backbone_trunk = MLP(x_dim, m_back, hidden_dim, depth=3, activation=nn.Tanh)
        self.backbone_bias = nn.Parameter(torch.zeros(1))
        
        # 2. Detail Branch and Trunk
        self.detail_branch = MLP(p_dim, m_det, hidden_dim, depth=3)
        self.detail_trunk = SinusoidalTrunk(x_dim, m_det, hidden_dim, depth=2, omega_0=45)
        
        self.m_back = m_back
        self.m_det = m_det

    def forward_backbone(self, p, x):
        """
        p: (B, P_dim) - Parameters
        x: (N_grid, X_dim) - Coordinates (Trunk pre-evaluation)
        Returns: (B, N_grid)
        """
        b = self.backbone_branch(p) # (B, M_back)
        t = self.backbone_trunk(x)   # (N_grid, M_back)
        # Bilinear product: (B, M_back) @ (M_back, N_grid) -> (B, N_grid)
        u_back = torch.matmul(b, t.t()) / self.m_back + self.backbone_bias
        return u_back

    def forward_detail(self, p, x):
        """Returns: (B, N_grid)"""
        b = self.detail_branch(p) # (B, M_det)
        t = self.detail_trunk(x)   # (N_grid, M_det)
        u_det = torch.matmul(b, t.t()) / self.m_det
        return u_det

    def compute_gate(self, u_back, q=0.9, beta=30.0):
        """
        Compute discontinuity gate from backbone gradients.
        u_back: (B, N_grid)
        Currently implements 1D central difference.
        """
        # (B, N) -> (B, N)
        du = torch.abs(u_back[:, 2:] - u_back[:, :-2]) # Gradient proxy
        # Padding to match original size
        du = nn.functional.pad(du, (1, 1), mode='replicate')
        
        # Quantile-based thresholding per sample
        # Note: torch.quantile is slow, using approximate threshold for now
        # Shape: (B, 1)
        threshold = torch.quantile(du, q, dim=1, keepdim=True)
        gate = torch.sigmoid(beta * (du - threshold))
        return gate

    def forward(self, p, x, mode='full', q=0.9, beta=30.0):
        """
        mode: 'backbone', 'detail', or 'full'
        """
        u_back = self.forward_backbone(p, x)
        if mode == 'backbone':
            return u_back
        
        u_det = self.forward_detail(p, x)
        if mode == 'detail':
            return u_det
        
        gate = self.compute_gate(u_back, q=q, beta=beta)
        u_pred = u_back + gate * u_det
        return u_pred, gate

class VanillaDeepONet(nn.Module):
    """SOTA Baseline: Vanilla DeepONet (no gate, no detail branch)"""
    def __init__(self, p_dim, x_dim, m=128, hidden_dim=128):
        super().__init__()
        self.branch = MLP(p_dim, m, hidden_dim, depth=3)
        self.trunk = MLP(x_dim, m, hidden_dim, depth=3, activation=nn.Tanh)
        self.m = m
        self.bias = nn.Parameter(torch.zeros(1))

    def forward(self, p, x):
        b = self.branch(p)
        t = self.trunk(x)
        return torch.matmul(b, t.t()) / self.m + self.bias

class SpectralConv1d(nn.Module):
    def __init__(self, in_channels, out_channels, modes1):
        super().__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.modes1 = modes1
        self.scale = (1 / (in_channels * out_channels))
        self.weights1 = nn.Parameter(self.scale * torch.rand(in_channels, out_channels, self.modes1, dtype=torch.complex64))

    def forward(self, x):
        batchsize = x.shape[0]
        x_ft = torch.fft.rfft(x)
        out_ft = torch.zeros(batchsize, self.out_channels, x.size(-1)//2 + 1, device=x.device, dtype=torch.complex64)
        out_ft[:, :, :self.modes1] = torch.einsum("bix,iox->box", x_ft[:, :, :self.modes1], self.weights1)
        x = torch.fft.irfft(out_ft, n=x.size(-1))
        return x

class FNO1d(nn.Module):
    """SOTA Baseline: Fourier Neural Operator 1D"""
    def __init__(self, modes, width, in_channels=5, out_channels=1):
        super().__init__()
        self.modes = modes
        self.width = width
        self.fc0 = nn.Linear(in_channels, self.width)
        self.conv0 = SpectralConv1d(self.width, self.width, self.modes)
        self.conv1 = SpectralConv1d(self.width, self.width, self.modes)
        self.w0 = nn.Conv1d(self.width, self.width, 1)
        self.w1 = nn.Conv1d(self.width, self.width, 1)
        self.fc1 = nn.Linear(self.width, 128)
        self.fc2 = nn.Linear(128, out_channels)

    def forward(self, x_in):
        # x_in: (batch, p_dim) -> Tile across space for FNO (u_in(x) = constant_p)
        x = x_in.unsqueeze(1).repeat(1, 256, 1) # (B, 256, 5)
        x = self.fc0(x)
        x = x.permute(0, 2, 1)
        
        x1 = self.conv0(x)
        x2 = self.w0(x)
        x = torch.nn.functional.gelu(x1 + x2)
        
        x1 = self.conv1(x)
        x2 = self.w1(x)
        x = x1 + x2
        
        x = x.permute(0, 2, 1)
        x = self.fc1(x)
        x = torch.nn.functional.gelu(x)
        x = self.fc2(x)
        return x.squeeze(-1)
