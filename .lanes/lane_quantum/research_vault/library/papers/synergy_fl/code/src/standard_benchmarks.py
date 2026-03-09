import numpy as np
import matplotlib.pyplot as plt
import os
from sklearn.datasets import load_breast_cancer, load_digits
from sklearn.preprocessing import StandardScaler
from synergy_fl.models import SynergisticModel, run_step

def run_breast_cancer_vfl(rounds=100, seed=42):
    print(f"🔬 Running Breast Cancer VFL Benchmark...")
    data = load_breast_cancer()
    X = data.data
    y = data.target
    
    # Preprocessing
    scaler = StandardScaler()
    X = scaler.fit_transform(X)
    
    # Vertical Split Strategy
    # Total 30 features.
    # Client A: First 15 features (Means, SEs)
    # Client B: Last 15 features (Worsts)
    mid = 15
    X_A = X[:, :mid]
    X_B = X[:, mid:]
    
    # MNC Projection
    # Real MNC aggregates the cross-product of encodings.
    # Here we project the high-dim features to a lower latent space proxy for the "SynergisticModel"
    # which is currently hardcoded for 4 dim [1, u, v, uv].
    
    # We take the 1st PCA component of each client's view as their "Synergy Signal"
    # This simulates them extracting local features, and then we check if the interaction of these features helps.
    
    from sklearn.decomposition import PCA
    
    pca_a = PCA(n_components=1, random_state=seed)
    pca_b = PCA(n_components=1, random_state=seed)
    
    u = pca_a.fit_transform(X_A).flatten()
    v = pca_b.fit_transform(X_B).flatten()
    
    # Lift features: [1, u, v, uv]
    # We assume 'u' and 'v' capture the main variance of each party.
    n_samples = len(y)
    phi = np.stack([np.ones(n_samples), u, v, u*v], axis=1)
    
    # -- Method 1: FedAvg --
    model_fedavg = SynergisticModel()
    acc_fedavg = []
    
    # -- Method 2: MNC --
    model_mnc = SynergisticModel()
    acc_mnc = []
    
    for r in range(rounds):
        # FedAvg
        run_step(model_fedavg, phi, y, method='fedavg', lr=0.1)
        preds_fed = (model_fedavg.predict(phi) > 0.5).astype(int)
        acc_fedavg.append(np.mean(preds_fed == y))
        
        # MNC
        run_step(model_mnc, phi, y, method='mnc', lr=0.1)
        preds_mnc = (model_mnc.predict(phi) > 0.5).astype(int)
        acc_mnc.append(np.mean(preds_mnc == y))
        
    return acc_fedavg, acc_mnc

def plot_standard_benchmarks(acc_fed, acc_mnc):
    os.makedirs('papers/synergy_fl/figs', exist_ok=True)
    
    plt.figure(figsize=(6, 4))
    plt.plot(acc_fed, label='FedAvg (Split View)', color='tab:red', linestyle='--')
    plt.plot(acc_mnc, label='MNC (Synergy-Aware)', color='tab:green', linewidth=2)
    
    plt.title('Standard Benchmark: Breast Cancer VFL (Sklearn)')
    plt.xlabel('Rounds')
    plt.ylabel('Accuracy')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend()
    # plt.ylim(0.8, 1.0) # Breast cancer usually gets high acc
    
    out_path = 'papers/synergy_fl/figs/benchmark_breast_cancer.pdf'
    plt.savefig(out_path, bbox_inches='tight')
    plt.savefig(out_path.replace('.pdf', '.png'), bbox_inches='tight', dpi=300)
    print(f"✅ Saved plot to {out_path}")

if __name__ == "__main__":
    acc_fed, acc_mnc = run_breast_cancer_vfl()
    plot_standard_benchmarks(acc_fed, acc_mnc)
