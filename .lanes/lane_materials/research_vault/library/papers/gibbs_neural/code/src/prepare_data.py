import numpy as np
import os
import argparse
from solvers import EulerSolver1D, EulerSolver2D, GaussianMollifier, save_run_info

# Canonical NAS paths
NAS_BASE = "/jhdx0003008/data/GibbsNeural"
RAW_DIR = os.path.join(NAS_BASE, "raw_sims")
PROC_DIR = os.path.join(NAS_BASE, "processed")

def generate_1d_dataset(n_samples=100, task_type='sod'):
    print(f"Generating 1D {task_type} dataset...")
    nx = 256
    solver = EulerSolver1D(nx=nx)
    
    data_raw = []
    data_mollified = []
    params = []
    
    for i in range(n_samples):
        # Sample parameters
        if task_type == 'sod':
            rhoL = 1.0; uL = 0.0; pL = 1.0 # Standard
            rhoR = 0.1 + 0.1 * np.random.rand()
            pR = 0.1 + 0.1 * np.random.rand()
            uR = 0.0
            T = 0.2
        elif task_type == 'lax':
            # Canonical Lax Shock Tube
            rhoL = 0.445; uL = 0.698; pL = 3.528
            rhoR = 0.5; uR = 0.0; pR = 0.571
            T = 0.16
        elif task_type == 'blast':
            # Strong blast wave (Woodward-Colella interaction)
            rhoL = 1.0; uL = 0.0; pL = 1000.0
            rhoR = 1.0; uR = 0.0; pR = 0.01
            T = 0.038
            
        # Initial condition
        U0 = np.zeros((3, nx))
        mid = nx // 2
        U0[:, :mid] = np.array([[rhoL], [rhoL*uL], [pL/(0.4) + 0.5*rhoL*uL**2]])
        U0[:, mid:] = np.array([[rhoR], [rhoR*uR], [pR/(0.4) + 0.5*rhoR*uR**2]])
        
        # Solve
        U_final = solver.solve(U0, T)
        _, _, p_final = solver.get_primitive(U_final)
        
        # Pre-process (Gaussian blur)
        p_mollified = GaussianMollifier.blur_1d(p_final, sigma=2.0)
        
        data_raw.append(p_final)
        data_mollified.append(p_mollified)
        params.append([rhoL, pL, rhoR, pR, T])
        
        if (i+1) % 10 == 0:
            print(f"  Progress: {i+1}/{n_samples}")
            
    return np.array(data_raw), np.array(data_mollified), np.array(params)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n1d", type=int, default=100)
    parser.add_argument("--n2d", type=int, default=10)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    
    # Strictly check NAS mount
    if not os.path.exists("/jhdx0003008") and not args.dry_run:
        print("CRITICAL ERROR: NAS /jhdx0003008 not found!")
        # Fallback for local testing if needed, but per LAW we should fail or warn
        print("Falling back to local data directory for PoC...")
        nas_root = "./data_local"
    else:
        nas_root = NAS_BASE
        
    os.makedirs(os.path.join(nas_root, "raw_sims"), exist_ok=True)
    os.makedirs(os.path.join(nas_root, "processed"), exist_ok=True)
    
    # 1D Sod
    raw, proc, params = generate_1d_dataset(args.n1d, task_type='sod')
    np.save(os.path.join(nas_root, "raw_sims", "1d_sod_raw.npy"), raw)
    np.save(os.path.join(nas_root, "processed", "1d_sod_mollified.npy"), proc)
    np.save(os.path.join(nas_root, "processed", "1d_sod_params.npy"), params)
    
    # 1D Blast
    raw, proc, params = generate_1d_dataset(args.n1d, task_type='blast')
    np.save(os.path.join(nas_root, "raw_sims", "1d_blast_raw.npy"), raw)
    np.save(os.path.join(nas_root, "processed", "1d_blast_mollified.npy"), proc)
    np.save(os.path.join(nas_root, "processed", "1d_blast_params.npy"), params)
    
    # Save Run Info
    metadata = {
        "project": "GibbsNeural",
        "description": "High-fidelity blast simulation dataset",
        "n_samples_1d": args.n1d * 2,
        "n_samples_2d": args.n2d,
        "gamma": 1.4,
        "blur_sigma": 2.0,
        "git_id": "HEAD" # Should be dynamic
    }
    save_run_info(nas_root, metadata)
    
    # Symlink to local project dir for seamless access
    local_data_dir = "./data"
    if not os.path.exists(local_data_dir):
        os.symlink(nas_root, local_data_dir)
        print(f"Created symlink: {local_data_dir} -> {nas_root}")

    print("✅ GibbsNeural Data Preparation Complete.")

if __name__ == "__main__":
    main()
