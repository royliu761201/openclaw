import torch
import numpy as np
import math
import argparse
from tqdm import tqdm

"""
2D Navier-Stokes Solver (Vorticity-Streamfunction Formulation)
- Crank-Nicolson for diffusion.
- Adams-Bashforth for advection.
- Pseudo-spectral spatial discretization.
"""

class NavierStokes2d:
    def __init__(self, N=64, L=1.0, dt=1e-3, nu=1e-4, device='cpu'):
        self.N = N
        self.L = L
        self.dt = dt
        self.nu = nu
        self.device = device
        
        # Grid
        h = L / N
        self.x = torch.linspace(0, L, N+1)[:-1].to(device)
        self.y = torch.linspace(0, L, N+1)[:-1].to(device)
        self.X, self.Y = torch.meshgrid(self.x, self.y, indexing='ij')
        
        # Wavenumbers
        k = torch.fft.rfftfreq(N, L / (2*math.pi)).to(device)
        self.k_x = k.view(-1, 1).repeat(1, N // 2 + 1)
        self.k_y = k.view(1, -1).repeat(N, 1) # Need full freq for y if using rfft2? 
        # Wait, for rfft2(x, dim=(0,1)), x is (N, N).
        # kx: (N,), ky: (N//2+1,) usually?
        
        # Correct Wavenumbers for standard torch.fft.rfft2
        kx = torch.fft.fftfreq(N, L / (2*math.pi)).to(device)
        ky = torch.fft.rfftfreq(N, L / (2*math.pi)).to(device)
        self.KX, self.KY = torch.meshgrid(kx, ky, indexing='ij')
        
        self.lap = -(self.KX**2 + self.KY**2)
        self.lap[0,0] = 1.0 # Avoid division by zero for inverse lap
        self.inv_lap = 1.0 / self.lap
        self.inv_lap[0,0] = 0.0
        
        # Dealiasing mask (2/3 rule)
        self.dealias_mask = (torch.abs(self.KX) < (2.0/3.0)*kx.max()) * (torch.abs(self.KY) < (2.0/3.0)*ky.max())

    def stream_function(self, w_h):
        return -self.inv_lap * w_h

    def nonlinear_term(self, w_h):
        # advection: - (u . grad) w
        # u = curl psi = (dpsi/dy, -dpsi/dx)
        psi_h = self.stream_function(w_h)
        
        # Derivatives in spectral space
        psi_x_h = 1j * self.KX * psi_h
        psi_y_h = 1j * self.KY * psi_h
        w_x_h = 1j * self.KX * w_h
        w_y_h = 1j * self.KY * w_h
        
        # Physical space
        psi_x = torch.fft.irfft2(psi_x_h, s=(self.N, self.N))
        psi_y = torch.fft.irfft2(psi_y_h, s=(self.N, self.N))
        w_x = torch.fft.irfft2(w_x_h, s=(self.N, self.N))
        w_y = torch.fft.irfft2(w_y_h, s=(self.N, self.N))
        
        # u . grad w = (psi_y * w_x - psi_x * w_y)
        adv = psi_y * w_x - psi_x * w_y
        
        # Dealiasing
        adv_h = torch.fft.rfft2(adv)
        return -adv_h * self.dealias_mask

    def step(self, w_h_prev, w_h_curr):
        # Crank-Nicolson for Diffusion, AB2 for Advection
        # (1 - 0.5*dt*nu*Lap) w_{n+1} = (1 + 0.5*dt*nu*Lap) w_n + dt * (1.5 N(w_n) - 0.5 N(w_{n-1}))
        
        N_curr = self.nonlinear_term(w_h_curr)
        N_prev = self.nonlinear_term(w_h_prev)
        
        rhs = (1.0 + 0.5 * self.dt * self.nu * self.lap) * w_h_curr + \
              self.dt * (1.5 * N_curr - 0.5 * N_prev)
              
        lhs_inv = 1.0 / (1.0 - 0.5 * self.dt * self.nu * self.lap)
        
        w_h_next = lhs_inv * rhs
        return w_h_next

def generate_dataset(args):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    solver = NavierStokes2d(N=args.resolution, nu=args.nu, dt=args.dt, device=device)
    
    data_u = []
    data_r = []
    data_delta = []
    
    print(f"🌊 Generating Navier-Stokes Data (nu={args.nu})...")
    
    for _ in tqdm(range(args.samples)):
        # Random Initial Condition (Gaussian Field)
        # Random Fourier coefficients
        w_h = torch.randn(args.resolution, args.resolution // 2 + 1, dtype=torch.cfloat, device=device)
        w_h = w_h * torch.exp(-0.5 * (solver.KX**2 + solver.KY**2) / (10**2)) # Smooth
        w0 = torch.fft.irfft2(w_h, s=(args.resolution, args.resolution))
        
        # Spin up (Physics warm up)
        w_h_prev = torch.fft.rfft2(w0)
        w_h_curr = solver.step(w_h_prev, w_h_prev) # First step roughly
        
        for _ in range(50): # Burn in
            w_h_next = solver.step(w_h_prev, w_h_curr)
            w_h_prev, w_h_curr = w_h_curr, w_h_next
            
        # Create "Solver Step" Scenario for Newton
        # We need u_k, r_k, delta_u
        # Let's say u_k is current state. Goal is u_{k+1}.
        # r_k: Ideally Residual of Steady State? Or Residual of Time Step?
        # For Time-Dependent: Newton connects u_t to u_{t+dt}.
        # Task: Predict next state given current state?
        # OR: Implicit Solve step?
        # Let's frame it as: Predict Next Step w_{n+1} from w_n.
        # Input u = w_n.
        # Residual r?
        # For explicit stepper, r is roughly the gradients/RHS.
        # r = N(w_n) + nu*Lap(w_n).
        
        # Calculate approx residual (instantaneous tendency)
        N_term = torch.fft.irfft2(solver.nonlinear_term(w_h_curr), s=(args.resolution, args.resolution))
        Diff_term = torch.fft.irfft2(solver.nu * solver.lap * w_h_curr, s=(args.resolution, args.resolution))
        r = N_term + Diff_term # dw/dt approx
        
        # Calculate Delta (Ground Truth)
        w_curr = torch.fft.irfft2(w_h_curr, s=(args.resolution, args.resolution))
        w_next_h = solver.step(w_h_prev, w_h_curr) # The actual next step (AB2)
        w_next = torch.fft.irfft2(w_next_h, s=(args.resolution, args.resolution))
        delta = w_next - w_curr
        
        data_u.append(w_curr.cpu().numpy())
        data_r.append(r.cpu().numpy())
        data_delta.append(delta.cpu().numpy())
        
    # Save
    import os
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    np.savez(args.output, u=np.array(data_u), r=np.array(data_r), delta=np.array(data_delta))
    print(f"✅ Saved {len(data_u)} samples to {args.output}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--resolution", type=int, default=64)
    parser.add_argument("--samples", type=int, default=1000)
    parser.add_argument("--nu", type=float, default=1e-4)
    parser.add_argument("--dt", type=float, default=1e-3)
    parser.add_argument("--output", type=str, default="data/newton/ns_data.npz")
    args = parser.parse_args()
    generate_dataset(args)
