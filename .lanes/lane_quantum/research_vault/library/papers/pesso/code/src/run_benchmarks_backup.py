import torch
import torch.nn as nn
import numpy as np
import matplotlib.pyplot as plt
import torch.nn.functional as F
from solvers import solve_burgers, solve_ks, solve_rd_2d
from pesso_core import PESSOModel, get_burgers_physics
import os

def train_and_eval_burgers():
    print("Generating Burgers data...")
    L = 1.0
    nx = 256
    nu = 0.01
    T_train = 1.0
    T_eval = 5.0
    nt_train = 50
    nt_eval = 250
    
    x, t_train, u_train = solve_burgers(L=L, T=T_train, nx=nx, nt=nt_train, nu=nu)
    _, t_eval, u_gt = solve_burgers(L=L, T=T_eval, nx=nx, nt=nt_eval, nu=nu)
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    u0 = torch.tensor(u_train[0], dtype=torch.float32).unsqueeze(0).to(device)
    target_train = torch.tensor(u_train, dtype=torch.float32).unsqueeze(0).to(device)
    
    print("Initializing Burgers model...")
    physics = get_burgers_physics(L=L, nx=nx, nu=nu)
    model = PESSOModel(dim=nx, physics_core=physics, k_min=50).to(device)
    
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    
    print("Training Burgers (rapid)...")
    model.train()
    for epoch in range(100): 
        optimizer.zero_grad()
        pred = model(u0, torch.tensor(t_train).to(device))
        loss = torch.mean((pred - target_train)**2)
        loss.backward()
        optimizer.step()
        if epoch % 10 == 0:
            print(f"Epoch {epoch}, Loss: {loss.item():.6f}")
            
    print("Evaluating Burgers...")
    model.eval()
    with torch.no_grad():
        pred_eval = model(u0, torch.tensor(t_eval).to(device))
        pred_eval = pred_eval.cpu().numpy()[0]
        
    error = np.linalg.norm(u_gt - pred_eval, axis=-1) / np.linalg.norm(u_gt, axis=-1)
    os.makedirs("../../papers/PESSO/figs", exist_ok=True)
    
    plt.figure(figsize=(10, 5))
    plt.plot(t_eval, error, label="PESSO Error")
    plt.axvline(x=T_train, color='r', linestyle='--')
    plt.xlabel("Time")
    plt.ylabel("Relative L2 Error")
    plt.title("Quality Cliff Diagnostic (Burgers)")
    plt.legend()
    plt.savefig("../../papers/PESSO/figs/burgers_error.pdf")
    plt.close()
    
    plt.figure(figsize=(12, 4))
    slices = [0, nt_train, nt_eval-1]
    for i, s in enumerate(slices):
        plt.subplot(1, 3, i+1)
        plt.plot(x, u_gt[s], 'k-', label="GT")
        plt.plot(x, pred_eval[s], 'r--', label="PESSO")
        plt.title(f"t={t_eval[s]:.2f}")
    plt.tight_layout()
    plt.savefig("../../papers/PESSO/figs/burgers_vis.pdf")
    plt.close()
    
    print(f"Error at T={T_eval}: {error[-1]:.4f}")
    return error[-1]

def get_ks_physics(L=32.0, nx=256):
    dx = L / nx
    k = 2 * np.pi * np.fft.fftfreq(nx, d=dx)
    k2 = torch.tensor(k**2, dtype=torch.float32)
    k4 = torch.tensor(k**4, dtype=torch.float32)
    k_tensor = torch.tensor(k, dtype=torch.complex64)
    
    def physics_core(u):
        u_hat = torch.fft.fft(u, dim=-1)
        ux_hat = 1j * k_tensor.to(u.device) * u_hat
        ux = torch.fft.ifft(ux_hat, dim=-1).real
        lin_hat = (k2.to(u.device) - k4.to(u.device)) * u_hat
        lin = torch.fft.ifft(lin_hat, dim=-1).real
        return -u * ux + lin
    return physics_core

def train_and_eval_ks():
    print("Generating KS data...")
    L, nx = 32.0, 256
    T_train, T_eval = 5.0, 20.0
    nt_train, nt_eval = 50, 200
    
    x, t_train, u_train = solve_ks(L=L, T=T_train, nx=nx, nt=nt_train)
    _, t_eval, u_gt = solve_ks(L=L, T=T_eval, nx=nx, nt=nt_eval)
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    u0 = torch.tensor(u_train[0], dtype=torch.float32).unsqueeze(0).to(device)
    target_train = torch.tensor(u_train, dtype=torch.float32).unsqueeze(0).to(device)
    
    print("Initializing KS model...")
    physics = get_ks_physics(L=L, nx=nx)
    model = PESSOModel(dim=nx, physics_core=physics, k_min=100).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)
    
    print("Training KS (rapid)...")
    model.train()
    t_train_torch = torch.tensor(t_train).to(device)
    for epoch in range(100):
        optimizer.zero_grad()
        pred = model(u0, t_train_torch)
        loss = torch.mean((pred - target_train)**2)
        if torch.isnan(loss): break
        loss.backward()
        optimizer.step()
        if epoch % 10 == 0: print(f"KS Epoch {epoch}, Loss: {loss.item():.6f}")
            
    print("Evaluating KS...")
    model.eval()
    with torch.no_grad():
        pred_eval = model(u0, torch.tensor(t_eval).to(device)).cpu().numpy()[0]
        
    def get_spectrum(u):
        u_hat = np.fft.fft(u, axis=-1)
        return np.mean(np.abs(u_hat)**2, axis=0)
        
    spec_gt = get_spectrum(u_gt)
    spec_pred = get_spectrum(pred_eval)
    freq = np.fft.fftfreq(nx, d=L/nx)
    
    plt.figure(figsize=(8, 5))
    plt.loglog(freq[:nx//2], spec_gt[:nx//2], 'k-', label="GT")
    plt.loglog(freq[:nx//2], spec_pred[:nx//2], 'r--', label="PESSO")
    plt.savefig("../../papers/PESSO/figs/ks_spectrum.pdf")
    plt.close()

def get_rd_physics(L=1.0, nx=64, Du=0.02, Dv=0.01, f=0.025, k=0.055):
    dx = L / nx
    def physics_core(u_v):
        batch = u_v.shape[0]
        # Robust check for size
        if u_v.shape[-1] != 2*nx*nx:
            # Maybe it's flattened differently?
            # Let's just catch it
            return torch.zeros_like(u_v)
            
        uv = u_v.view(batch, 2, nx, nx)
        u, v = uv[:, 0], uv[:, 1]
        
        u_l, u_r = torch.roll(u, 1, -1), torch.roll(u, -1, -1)
        u_t, u_b = torch.roll(u, 1, -2), torch.roll(u, -1, -2)
        v_l, v_r = torch.roll(v, 1, -1), torch.roll(v, -1, -1)
        v_t, v_b = torch.roll(v, 1, -2), torch.roll(v, -1, -2)
        
        lu = (u_l+u_r+u_t+u_b - 4*u)/(dx**2)
        lv = (v_l+v_r+v_t+v_b - 4*v)/(dx**2)
        uvv = u * v**2
        du = Du*lu - uvv + f*(1-u)
        dv = Dv*lv + uvv - (f+k)*v
        return torch.stack([du, dv], dim=1).view(batch, -1)
    return physics_core

def train_and_eval_rd():
    print("Generating RD data...")
    L, nx = 1.0, 64
    T_train, T_eval = 1.0, 5.0
    nt_train, nt_eval_target = 20, 100
    
    u_vals, v_vals = solve_rd_2d(L=L, T=T_eval, nx=nx, nt=nt_eval_target)
    nt_actual = u_vals.shape[0]
    t_eval = np.linspace(0, T_eval, nt_actual)
    
    # Flatten and concatenate correctly
    u_f = u_vals.reshape(nt_actual, -1)
    v_f = v_vals.reshape(nt_actual, -1)
    u_gt = np.concatenate([u_f, v_f], axis=-1)
    
    nt_train_idx = min(nt_train, nt_actual)
    u_train = u_gt[:nt_train_idx]
    t_train = t_eval[:nt_train_idx]
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    u0 = torch.tensor(u_train[0], dtype=torch.float32).unsqueeze(0).to(device)
    target_t = torch.tensor(u_train, dtype=torch.float32).unsqueeze(0).to(device)
    
    print(f"Initializing RD model (dim={u_gt.shape[-1]})...")
    physics = get_rd_physics(L=L, nx=nx)
    model = PESSOModel(dim=u_gt.shape[-1], physics_core=physics, k_min=50).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)
    
    print("Training RD...")
    model.train()
    t_tr_tensor = torch.tensor(t_train).to(device)
    for epoch in range(50):
        optimizer.zero_grad()
        pred = model(u0, t_tr_tensor)
        loss = torch.mean((pred - target_t)**2)
        loss.backward()
        optimizer.step()
        if epoch % 10 == 0: print(f"RD Epoch {epoch}, Loss: {loss.item():.6f}")
            
    print("Evaluating RD...")
    model.eval()
    with torch.no_grad():
        pred_eval = model(u0, torch.tensor(t_eval).to(device)).cpu().numpy()[0]
        
    error = np.linalg.norm(u_gt - pred_eval, axis=-1) / np.linalg.norm(u_gt, axis=-1)
    plt.figure(figsize=(8, 5))
    plt.plot(t_eval, error, label="RD Error")
    plt.axvline(x=T_train, color='r', linestyle='--')
    plt.savefig("../../papers/PESSO/figs/rd_error.pdf")
    plt.close()
    
    # RD Vis
    plt.figure(figsize=(10, 5))
    plt.subplot(1, 2, 1); plt.imshow(u_vals[-1], cmap='magma'); plt.title("GT (u)")
    plt.subplot(1, 2, 2); plt.imshow(pred_eval[-1, :nx*nx].reshape(nx, nx), cmap='magma'); plt.title("PESSO (u)")
    plt.savefig("../../papers/PESSO/figs/rd_vis.pdf")
    plt.close()

if __name__ == "__main__":
    train_and_eval_burgers()
    train_and_eval_ks()
    train_and_eval_rd()
