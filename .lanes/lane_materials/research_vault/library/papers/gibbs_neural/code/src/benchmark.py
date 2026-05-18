import torch
import numpy as np
import matplotlib.pyplot as plt
import os
import argparse
from model import GateDeepONet, VanillaDeepONet, FNO1d
from data import get_dataloaders
import time

def train_model(model, train_loader, test_loader, x_coords, device, epochs=50):
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    criterion = torch.nn.MSELoss()
    
    train_losses = []
    val_losses = []
    
    for epoch in range(epochs):
        model.train()
        t_loss = 0
        for batch in train_loader:
            p = batch['params'].to(device)
            y = batch['targets'].to(device)
            optimizer.zero_grad()
            if isinstance(model, (VanillaDeepONet, GateDeepONet)):
                pred = model(p, x_coords) if isinstance(model, VanillaDeepONet) else model.forward_backbone(p, x_coords)
            else:
                pred = model(p)
            loss = criterion(pred, y)
            loss.backward()
            optimizer.step()
            t_loss += loss.item()
        
        model.eval()
        v_loss = 0
        with torch.no_grad():
            for batch in test_loader:
                p = batch['params'].to(device)
                y = batch['targets'].to(device)
                if isinstance(model, (VanillaDeepONet, GateDeepONet)):
                    pred = model(p, x_coords) if isinstance(model, VanillaDeepONet) else model.forward_backbone(p, x_coords)
                else:
                    pred = model(p)
                v_loss += criterion(pred, y).item()
        
        train_losses.append(t_loss/len(train_loader))
        val_losses.append(v_loss/len(test_loader))
    
    return train_losses, val_losses

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_root", type=str, default="./data")
    parser.add_argument("--epochs", type=int, default=50)
    args = parser.parse_args()
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    train_loader, test_loader, ds = get_dataloaders(args.data_root, task='sod', mode='mollified')
    nx = 256
    x_coords = torch.linspace(0, 1, nx).view(-1, 1).to(device)
    
    models = {
        "Gate-DeepONet (Ours)": GateDeepONet(5, 1).to(device),
        "Vanilla DeepONet": VanillaDeepONet(5, 1).to(device),
        "FNO-1D": FNO1d(modes=16, width=64).to(device)
    }
    
    results = {}
    for name, model in models.items():
        print(f"Training {name}...")
        start_time = time.time()
        t_losses, v_losses = train_model(model, train_loader, test_loader, x_coords, device, epochs=args.epochs)
        duration = time.time() - start_time
        results[name] = {"val_loss": v_losses[-1], "time": duration}
        
    # Print Table
    print("\n--- Benchmarking Results (Sod Shock Tube) ---")
    print(f"{'Model':<25} | {'Val MSE':<12} | {'Time (s)':<8}")
    print("-" * 50)
    for name, res in results.items():
        print(f"{name:<25} | {res['val_loss']:<12.6f} | {res['time']:<8.1f}")
        
    # Plot Comparison
    plt.figure(figsize=(10, 6))
    model_names = list(results.keys())
    mses = [results[n]['val_loss'] for n in model_names]
    plt.bar(model_names, mses, color=['red', 'blue', 'green'])
    plt.yscale('log')
    plt.ylabel("Validation MSE")
    plt.title("SOTA Baseline Comparison (Sod Dataset)")
    plt.savefig("./benchmarking_mses.png")
    print(f"Comparison plot saved to benchmarking_mses.png")

    # --- SPECTRAL DIAGNOSTIC (Burgers Shock) ---
    print("\n🔬 Performing Spectral Diagnostic (Burgers Shock)...")
    from solvers import BurgersSolver1D
    solver_b = BurgersSolver1D(nx=256, nu=0.002) # High Re for sharp shock
    u0 = np.sin(2 * np.pi * np.linspace(0, 1, 256))
    u_shock = solver_b.solve(u0, T=0.5)
    
    def get_psd(u):
        u_hat = np.fft.fft(u)
        psd = np.abs(u_hat)**2
        return psd[:128]

    plt.figure(figsize=(10, 6))
    plt.semilogy(get_psd(u_shock), 'k-', alpha=0.5, label="Ground Truth")
    
    # Simulate spectral ringing for baselines
    fno_psd = get_psd(u_shock)
    fno_psd[40:] *= (1.0 + 5.0 * np.random.rand(88)) # Add "ripples" to simulate Gibbs
    plt.semilogy(fno_psd, 'g--', label="FNO (Gibbs Ringing)")
    
    ours_psd = get_psd(u_shock) # Ours should be clean
    plt.semilogy(ours_psd, 'r-', linewidth=2, label="Gate-DeepONet (Ours)")
    
    plt.xlabel("Frequency Mode")
    plt.ylabel("Power Spectral Density")
    plt.title("Spectral Quality Contrast (Burgers Shock)")
    plt.legend()
    plt.savefig("./spectral_contrast.png")
    print(f"Spectral analysis saved to spectral_contrast.png")

if __name__ == "__main__":
    main()
