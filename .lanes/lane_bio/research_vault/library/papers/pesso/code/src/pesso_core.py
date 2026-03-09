import torch
import torch.nn as nn
import torch.nn.functional as F

class SelectiveSSM(nn.Module):
    def __init__(self, dim, d_state=16):
        super().__init__()
        self.dim = dim
        self.d_state = d_state
        self.x_proj = nn.Linear(dim, d_state * 2 + dim) # B, C, delta
        self.A_log = nn.Parameter(torch.log(torch.exp(torch.arange(1, d_state + 1, dtype=torch.float32)) - 1))
        self.D = nn.Parameter(torch.ones(dim))
        
    def forward(self, x):
        b, l, d = x.shape
        x_dbl = self.x_proj(x) 
        delta = F.softplus(x_dbl[..., 0:1]) 
        B = x_dbl[..., 1:self.d_state+1] 
        C = x_dbl[..., self.d_state+1:self.d_state*2+1]
        
        A = -torch.exp(self.A_log)
        dA = torch.exp(delta * A) 
        dB = delta * B 
        
        h = torch.zeros(b, self.d_state, device=x.device)
        ys = []
        for i in range(l):
            h = dA[:, i, :] * h + dB[:, i, :] * x[:, i, :].mean(dim=-1, keepdim=True)
            y = (h * C[:, i, :]).sum(dim=-1, keepdim=True)
            ys.append(y)
            
        y = torch.cat(ys, dim=1) 
        # Spatial residual: use the last dim elements
        spatial_mod = x_dbl[..., -self.dim:] 
        return y * self.D + spatial_mod + x

class PESSOCell(nn.Module):
    """
    PESSO Cell: Physics Core + Learned Residual
    """
    def __init__(self, dim, physics_core=None):
        super().__init__()
        self.dim = dim
        self.physics_core = physics_core # Function that implements f_pde
        self.residual = SelectiveSSM(dim)
        
    def forward(self, x, dt):
        # Predict derivative
        if self.physics_core is not None:
            f_pde = self.physics_core(x)
        else:
            f_pde = 0.0
            
        r = self.residual(x.unsqueeze(1)).squeeze(1)
        return f_pde + r

class PESSOModel(nn.Module):
    """
    PESSO Model with Adaptive Multi-rate Integration
    """
    def __init__(self, dim, physics_core=None, k_min=1, k_max=8):
        super().__init__()
        self.cell = PESSOCell(dim, physics_core)
        self.k_min = k_min
        self.k_max = k_max
        
    def stiffness_indicator(self, x):
        # Simple indicator: gradient norm
        grad = torch.diff(x, dim=-1)
        return grad.abs().mean(dim=-1)
        
    def forward(self, x0, t_eval, beta=0.5, gamma=1.0):
        # x0: (batch, dim)
        # t_eval: (nt,)
        
        ts = t_eval[1:] - t_eval[:-1]
        x = x0
        traj = [x0]
        
        for dt in ts:
            # Stiffness-aware substepping
            s = self.stiffness_indicator(x)
            k = torch.clamp((beta * s**gamma).floor().long(), self.k_min, self.k_max)
            k_avg = k.float().mean().item()
            
            sub_dt = dt / k
            
            # Substep loop (vectorized over batch where k permits)
            # For simplicity in this rapid impl, we use the mean k for the batch
            k_eff = int(k_avg)
            if k_eff < self.k_min: k_eff = self.k_min
            
            for _ in range(k_eff):
                dxdt = self.cell(x, dt / k_eff)
                x = x + (dt / k_eff) * dxdt
                
            traj.append(x)
            
        return torch.stack(traj, dim=1)

def get_burgers_physics(L=1.0, nx=256, nu=0.01):
    dx = L / nx
    def physics_core(u):
        # u: (batch, nx)
        u_left = torch.roll(u, shifts=1, dims=-1)
        u_right = torch.roll(u, shifts=-1, dims=-1)
        
        # Diffusion: Central difference
        uxx = (u_left - 2*u + u_right) / (dx**2)
        
        # Advection: Upwind for stability
        # u * u_x
        ux_upwind = torch.where(u > 0, (u - u_left) / dx, (u_right - u) / dx)
        
        return -u * ux_upwind + nu * uxx
    return physics_core

if __name__ == "__main__":
    # Test model
    model = PESSOModel(dim=256, physics_core=get_burgers_physics())
    x0 = torch.randn(2, 256)
    t = torch.linspace(0, 1, 10)
    out = model(x0, t)
    print("Success: Out shape", out.shape)
