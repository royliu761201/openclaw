import numpy as np
import os
import argparse
from tqdm import tqdm
from pathlib import Path

def generate_1d_poisson(batch_size=1, grid_size=64, num_steps=10):
    """
    Generates optimization trajectories for 1D Poisson Equation: -u'' = f
    Solver: Jacobi Method (Classic iterative solver)
    
    Returns:
        trajectories: List of dictionaries containing {state, residual, update, f}
    """
    trajectories = []
    
    for _ in range(batch_size):
        # 1. Physical Setup
        x = np.linspace(0, 1, grid_size)
        dx = x[1] - x[0]
        
        # Source term f(x): Random combination of sin frequencies
        k1, k2 = np.random.randint(1, 5, 2)
        f = np.sin(k1 * np.pi * x) + 0.5 * np.sin(k2 * np.pi * x)
        
        # Boundary Conditions: u(0)=0, u(1)=0
        
        # 2. Solver Initialization (Random Guess)
        u_curr = np.random.randn(grid_size) * 0.1
        u_curr[0] = 0
        u_curr[-1] = 0
        
        trajectory = {
            "u_history": [],
            "r_history": [],
            "delta_history": [],
            "f": f
        }
        
        # 3. Iterative Solving (Jacobi)
        # Poisson: -u_xx = f  =>  (-u[i-1] + 2u[i] - u[i+1]) / dx^2 = f[i]
        # Jacobi Update: u[i] = 0.5 * (u[i-1] + u[i+1] + dx^2 * f[i])
        
        # True Solution (via dense linear algebra for reference, optional)
        # A = np.zeros((grid_size, grid_size)) ...
        
        for step in range(num_steps):
            u_next = np.copy(u_curr)
            
            # Compute Interior Update
            # u_new[i] = (u[i-1] + u[i+1] + f[i]*dx^2) / 2
            u_next[1:-1] = 0.5 * (u_curr[:-2] + u_curr[2:] + f[1:-1] * dx**2)
            
            # Boundary Clamp
            u_next[0] = 0
            u_next[-1] = 0
            
            # Compute Residual: r = f - (-Laplacian * u)
            # L(u) approx (-u[i-1] + 2u[i] - u[i+1])/dx^2
            laplacian_u = np.zeros_like(u_curr)
            laplacian_u[1:-1] = -(u_curr[:-2] - 2*u_curr[1:-1] + u_curr[2:]) / dx**2
            
            residual = f - laplacian_u # r = f - Lu
            residual[0] = 0 # BC satisfied
            residual[-1] = 0
            
            delta_u = u_next - u_curr
            
            # Store State
            trajectory["u_history"].append(u_curr.copy())
            trajectory["r_history"].append(residual.copy())
            trajectory["delta_history"].append(delta_u.copy())
            
            # Update
            u_curr = u_next
            
        trajectories.append(trajectory)
        
    return trajectories

def generate_2d_poisson(batch_size=1, grid_size=64, num_steps=10):
    """
    Generates 2D Poisson trajectories: -Laplacian(u) = f
    Solver: Jacobi (5-point stencil)
    """
    trajectories = []
    
    for _ in range(batch_size):
        # 1. Setup 2D field
        x = np.linspace(0, 1, grid_size)
        y = np.linspace(0, 1, grid_size)
        X, Y = np.meshgrid(x, y)
        dx = x[1] - x[0]
        
        # Source f: Sum of 2D sines
        k1, k2 = np.random.randint(1, 5, 2)
        l1, l2 = np.random.randint(1, 5, 2)
        f = np.sin(k1*np.pi*X)*np.sin(l1*np.pi*Y) + 0.5*np.sin(k2*np.pi*X)*np.sin(l2*np.pi*Y)
        
        # Init u (Random)
        u_curr = np.random.randn(grid_size, grid_size) * 0.1
        # BCs: 0 at boundary
        u_curr[0, :] = 0; u_curr[-1, :] = 0
        u_curr[:, 0] = 0; u_curr[:, -1] = 0
        
        trajectory = {"u_history": [], "r_history": [], "delta_history": [], "f": f}
        
        for step in range(num_steps):
            u_next = u_curr.copy()
            
            # Jacobi Update: u[i,j] = 0.25 * (u[i+1] + u[i-1] + u[j+1] + u[j-1] + f*dx^2)
            # Vectorized Interior
            u_next[1:-1, 1:-1] = 0.25 * (
                u_curr[0:-2, 1:-1] + u_curr[2:, 1:-1] +
                u_curr[1:-1, 0:-2] + u_curr[1:-1, 2:] +
                f[1:-1, 1:-1] * dx**2
            )
            
            # Re-clamp BCs (Dirichlet = 0)
            u_next[0, :] = 0; u_next[-1, :] = 0
            u_next[:, 0] = 0; u_next[:, -1] = 0
            
            # Residual: r = f - (-Laplacian u)
            # Laplacian approx: (u_l + u_r + u_u + u_d - 4u) / dx^2
            lap_u = np.zeros_like(u_curr)
            lap_u[1:-1, 1:-1] = (
                u_curr[0:-2, 1:-1] + u_curr[2:, 1:-1] +
                u_curr[1:-1, 0:-2] + u_curr[1:-1, 2:] -
                4 * u_curr[1:-1, 1:-1]
            ) / dx**2
            
            residual = f - (-lap_u)
            residual[0, :] = 0; residual[-1, :] = 0
            residual[:, 0] = 0; residual[:, -1] = 0
            
            delta_u = u_next - u_curr
            
            trajectory["u_history"].append(u_curr.copy())
            trajectory["r_history"].append(residual.copy())
            trajectory["delta_history"].append(delta_u.copy())
            
            u_curr = u_next
            
        trajectories.append(trajectory)
        
    return trajectories

def generate_pacman_poisson(batch_size=1, grid_size=64, num_steps=10):
    """
    OOD Test: Poisson on a non-convex 'Pacman' domain.
    """
    trajectories = []
    
    # Define Pacman Mask
    x = np.linspace(-1, 1, grid_size)
    y = np.linspace(-1, 1, grid_size)
    X, Y = np.meshgrid(x, y)
    
    # Circular domain
    R = np.sqrt(X**2 + Y**2)
    Angle = np.arctan2(Y, X)
    
    # Mask: Inside Circle AND (Angle > something or < something)
    # Open mouth at angle 0
    mask = (R < 0.8) & ~((np.abs(Angle) < 0.5) & (X > 0))
    mask = mask.astype(float)
    
    for _ in range(batch_size):
        # Source f
        k1, k2 = np.random.randint(1, 5, 2)
        f = np.sin(k1*np.pi*(X+1)/2)*np.sin(k2*np.pi*(Y+1)/2)
        f = f * mask # Source only inside domain
        
        u_curr = np.random.randn(grid_size, grid_size) * 0.1 * mask
        dx = 2.0 / grid_size # scale roughly
        
        trajectory = {"u_history": [], "r_history": [], "delta_history": [], "f": f}
        
        for step in range(num_steps):
            u_next = u_curr.copy()
            
            # Jacobi with Mask Enforcement
            # 1. Standard Update
            u_next[1:-1, 1:-1] = 0.25 * (
                u_curr[0:-2, 1:-1] + u_curr[2:, 1:-1] +
                u_curr[1:-1, 0:-2] + u_curr[1:-1, 2:] +
                f[1:-1, 1:-1] * dx**2
            )
            
            # 2. Enforce Mask (Dirichlet BC everywhere outside domain)
            u_next = u_next * mask
            
            # Residual
            lap_u = np.zeros_like(u_curr)
            lap_u[1:-1, 1:-1] = (
                u_curr[0:-2, 1:-1] + u_curr[2:, 1:-1] +
                u_curr[1:-1, 0:-2] + u_curr[1:-1, 2:] -
                4 * u_curr[1:-1, 1:-1]
            ) / dx**2
            
            # Residual is zero outside domain automatically if we define it so matches equation
            # Or simplified: r = (f - (-Lap)) * mask
            residual = (f - (-lap_u)) * mask
            
            delta_u = u_next - u_curr
            
            trajectory["u_history"].append(u_curr.copy())
            trajectory["r_history"].append(residual.copy())
            trajectory["delta_history"].append(delta_u.copy())
            
            u_curr = u_next
            
        trajectories.append(trajectory)
        
    return trajectories

def generate_variable_poisson(batch_size=1, grid_size=64, num_steps=10, nu_range=(0.1, 0.5)):
    """
    Generates Poisson trajectories with variable coefficient nu:
    -nu * Laplacian(u) = f
    Solver: Jacobi
    """
    trajectories = []
    
    for _ in range(batch_size):
        # 1. Setup
        x = np.linspace(0, 1, grid_size)
        y = np.linspace(0, 1, grid_size)
        X, Y = np.meshgrid(x, y)
        dx = x[1] - x[0]
        
        # Sample nu
        nu = np.random.uniform(nu_range[0], nu_range[1])
        
        # Source f
        k1, k2 = np.random.randint(1, 5, 2)
        f = np.sin(k1*np.pi*X)*np.sin(k2*np.pi*Y)
        
        # Init u
        u_curr = np.random.randn(grid_size, grid_size) * 0.1
        u_curr[0,:]=0; u_curr[-1,:]=0; u_curr[:,0]=0; u_curr[:,-1]=0
        
        trajectory = {"u_history": [], "r_history": [], "delta_history": [], "f": f, "nu": nu}
        
        for step in range(num_steps):
            u_next = u_curr.copy()
            
            # Jacobi for -nu*Lap(u) = f  =>  -nu*(Neighbors - 4u)/dx^2 = f
            # => 4u - Neighbors = f*dx^2/nu
            # => u = 0.25 * (Neighbors + f*dx^2/nu)
            
            u_next[1:-1, 1:-1] = 0.25 * (
                u_curr[0:-2, 1:-1] + u_curr[2:, 1:-1] +
                u_curr[1:-1, 0:-2] + u_curr[1:-1, 2:] +
                (f[1:-1, 1:-1] * dx**2) / nu
            )
            
            # Residual: r = f - (-nu*Lap(u))
            lap_u = np.zeros_like(u_curr)
            lap_u[1:-1, 1:-1] = (
                u_curr[0:-2, 1:-1] + u_curr[2:, 1:-1] +
                u_curr[1:-1, 0:-2] + u_curr[1:-1, 2:] -
                4 * u_curr[1:-1, 1:-1]
            ) / dx**2
            
            residual = f - (-nu * lap_u)
            # Apply Dirichlet to residual (error is 0 at boundary)
            residual[0,:]=0; residual[-1,:]=0; residual[:,0]=0; residual[:,-1]=0
            
            delta_u = u_next - u_curr
            
            trajectory["u_history"].append(u_curr.copy())
            trajectory["r_history"].append(residual.copy())
            trajectory["delta_history"].append(delta_u.copy())
            
            u_curr = u_next
            
        trajectories.append(trajectory)
        
    return trajectories

def save_dataset(trajectories, output_dir, name="poisson"):
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Pack [N, Step, Grid, Grid] (for 2D) or [N, Step, Grid] (1D)
    u_stack = np.array([t["u_history"] for t in trajectories])
    r_stack = np.array([t["r_history"] for t in trajectories])
    d_stack = np.array([t["delta_history"] for t in trajectories])
    f_stack = np.array([t["f"] for t in trajectories])
    
    # Determine dim for filename
    dim = "2d" if u_stack.ndim == 4 else "1d"
    
    np.savez(f"{output_dir}/{name}_{dim}_jacobi.npz", 
             u=u_stack, r=r_stack, delta=d_stack, f=f_stack)
    print(f"✅ Saved dataset to {output_dir}/{name}_{dim}_jacobi.npz")
    print(f"   Shape: {u_stack.shape}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=1000)
    parser.add_argument("--dim", type=int, default=2, choices=[1, 2])
    parser.add_argument("--out", type=str, default="data/newton/data_2d")
    parser.add_argument("--pacman", action="store_true", help="Generate Pacman geometry")
    parser.add_argument("--ood_coeff", action="store_true", help="Generate Coefficient OOD data")
    args = parser.parse_args()
    
    print(f"🚀 Generating {args.samples} {args.dim}D Poisson optimization trajectories...")
    
    if args.pacman:
        print("👻 Mode: Pacman Geometry (OOD)")
        data = generate_pacman_poisson(batch_size=args.samples)
        save_dataset(data, args.out, name="pacman")
    elif args.ood_coeff:
        print("🧪 Mode: Variable Coefficient OOD (nu=0.01)")
        # For OOD test, we want a fixed hard coefficient
        data = generate_variable_poisson(batch_size=args.samples, nu_range=(0.01, 0.01))
        save_dataset(data, args.out, name="coeff_ood")
    elif args.dim == 1:
        data = generate_1d_poisson(batch_size=args.samples)
        save_dataset(data, args.out)
    else:
        # Default 2D training data (implicit nu=1)
        data = generate_2d_poisson(batch_size=args.samples)
        save_dataset(data, args.out)

def generate_darcy_flow(batch_size=1, grid_size=64, num_steps=10):
    """
    Generates 2D Darcy Flow trajectories: -div(a(x) * grad(u)) = f
    a(x): Permeability field (piecewise constant)
    Solver: Jacobi with variable coefficients
    """
    trajectories = []
    
    for _ in range(batch_size):
        x = np.linspace(0, 1, grid_size)
        y = np.linspace(0, 1, grid_size)
        X, Y = np.meshgrid(x, y)
        dx = x[1] - x[0]
        
        # Permeability a(x): Blocks of high/low K
        a = np.ones((grid_size, grid_size))
        # Add random blocks
        for _ in range(3):
            rx, ry = np.random.randint(0, grid_size, 2)
            rw, rh = np.random.randint(10, 20, 2)
            val = np.random.choice([0.1, 10.0])
            a[max(0, rx-rw):min(grid_size, rx+rw), max(0, ry-rh):min(grid_size, ry+rh)] = val
            
        # Source f
        f = np.sin(2*np.pi*X) * np.cos(2*np.pi*Y) + 1.0 # Constant source
        
        # Init u
        u_curr = np.zeros((grid_size, grid_size))
        
        trajectory = {"u_history": [], "r_history": [], "delta_history": [], "f": f, "a": a}
        
        # 5-point stencil with variable coefficient
        # -[ a_e(u_E - u_P) - a_w(u_P - u_W) ]/dx^2 ... = f
        # u_P * (a_e + a_w + a_n + a_s) = f*dx^2 + a_e*u_E + ...
        
        for step in range(num_steps):
            u_next = u_curr.copy()
            
            # Compute coefficients at interfaces (harmonic mean / arithmetic mean)
            # Simple Arithmetic mean for grid center
            a_field = a
            
            # Vectorized Update (Simplified isotropic approximation for speed in this generator)
            # u[i,j] = (a[i+1]*u[i+1] + a[i-1]*u[i-1] + ...) / sum(a)
            
            # Using simple Jacobi relaxation for diffusion -div(a grad u) = f
            # u_new = u_old + omega * D^-1 * (f - A u_old) -> This effectively captures the solver dynamics
            # We simulate "Solver Steps"
            
            # Residual R = f + div(a grad u)
            # Grad u
            u_y, u_x = np.gradient(u_curr, dx)
            # Flux
            q_x = a * u_x
            q_y = a * u_y
            # Div
            _, div_q_x = np.gradient(q_x, dx)
            div_q_y, _ = np.gradient(q_y, dx) # numpy returns axis 0 first (y), axis 1 (x)
            
            div_flux = div_q_x + div_q_y
            residual = f + div_flux # Since eqn is -div = f => div = -f => f + div = 0 ? 
            # -div(a grad u) = f  =>  f + div(a grad u) = LHS - RHS = Residual (if u is wrong)
            # Actually R = f - (-div) = f + div
            
            # Update: delta u = alpha * Residual (Richardson iteration / Gradient Descent step)
            alpha = 0.001 # learning rate / pseudo-time step
            delta_u = alpha * residual
            
            # Boundary conditions (Dirichlet u=0)
            delta_u[0,:]=0; delta_u[-1,:]=0; delta_u[:,0]=0; delta_u[:,-1]=0
            
            u_next = u_curr + delta_u
            
            trajectory["u_history"].append(u_curr.copy())
            trajectory["r_history"].append(residual.copy())
            trajectory["delta_history"].append(delta_u.copy())
            
            u_curr = u_next
            
        trajectories.append(trajectory)
        
    return trajectories
