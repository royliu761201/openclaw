import numpy as np
import matplotlib.pyplot as plt
import os

def simulate_blast_2d():
    print("Simulating 2D Blast Wave for visualization...")
    nx, ny = 200, 200
    L = 1.0
    dx = L/nx
    dt = 0.0005
    steps = 400
    u = np.zeros((nx, ny))
    
    # Blast center
    cx, cy = nx // 4, ny // 2
    u[cx-2:cx+3, cy-2:cy+3] = 10.0
    
    # Obstacles (Heterogeneous media)
    mask = np.ones((nx, ny))
    # Wall with a gap
    mask[nx//2-5:nx//2+5, :] = 0.5 # Slow region
    mask[nx//2-5:nx//2+5, ny//2-15:ny//2+15] = 1.0 # Gap
    
    # Simple acoustic wave propagation as proxy for blast
    p = np.zeros((nx, ny)) # pressure
    v = np.zeros((nx, ny)) # velocity field proxy
    
    # Time stepping
    os.makedirs("../../papers/PESSO/figs", exist_ok=True)
    
    history = []
    
    for i in range(steps):
        # Wave equation approximation
        # d2p/dt2 = c^2 * nabla^2 p
        laplacian = (np.roll(p, 1, 0) + np.roll(p, -1, 0) + np.roll(p, 1, 1) + np.roll(p, -1, 1) - 4*p) / dx**2
        v += dt * mask * laplacian
        p += dt * v
        
        # Source (persistent for a bit)
        if i < 20:
             p[cx-2:cx+3, cy-2:cy+3] += 1.0
             
        # Damping
        v *= 0.995
        
        if i in [50, 150, 350]:
            history.append(p.copy())
            
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    for idx, (ax, data) in enumerate(zip(axes, history)):
        im = ax.imshow(data, cmap='inferno', origin='lower')
        ax.set_title(f"Step {idx}")
        ax.axis('off')
    
    plt.tight_layout()
    plt.savefig("../../papers/PESSO/figs/blast_vis.pdf")
    print("Blast-wave visualization saved.")

if __name__ == "__main__":
    simulate_blast_2d()
