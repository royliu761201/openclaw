import numpy as np
import matplotlib.pyplot as plt
import os
# import seaborn as sns # Not installed
from sklearn.datasets import load_breast_cancer
from sklearn.preprocessing import StandardScaler
from synergy_fl.benchmarks import generate_xor_data, generate_healthcare_data
from synergy_fl.real_world import generate_medtime_split_data

def explore_xor():
    print("🔍 Exploring XOR Dataset...")
    x1, x2, y = generate_xor_data(n_samples=1000)
    
    plt.figure(figsize=(10, 4))
    
    # Scatter (Joint View - Separable)
    plt.subplot(1, 3, 1)
    plt.scatter(x1 + np.random.normal(0, 0.05, 1000), 
                x2 + np.random.normal(0, 0.05, 1000), 
                c=y, cmap='coolwarm', alpha=0.6, s=10)
    plt.title('Joint View (Separable via Interaction)')
    plt.xlabel('Client A (x1)')
    plt.ylabel('Client B (x2)')
    
    # Histogram Client A (Marginal View - Unidentifiable)
    plt.subplot(1, 3, 2)
    plt.hist(x1[y==0], alpha=0.5, label='Class 0', density=True, bins=2)
    plt.hist(x1[y==1], alpha=0.5, label='Class 1', density=True, bins=2)
    plt.title('Client A Marginal (No Signal)')
    plt.legend()
    
    # Histogram Client B
    plt.subplot(1, 3, 3)
    plt.hist(x2[y==0], alpha=0.5, label='Class 0', density=True, bins=2)
    plt.hist(x2[y==1], alpha=0.5, label='Class 1', density=True, bins=2)
    plt.title('Client B Marginal (No Signal)')
    plt.legend()
    
    plt.tight_layout()
    plt.savefig('papers/synergy_fl/figs/data_xor_analysis.pdf')
    plt.close()

def explore_breast_cancer():
    print("🔍 Exploring Breast Cancer Split...")
    data = load_breast_cancer()
    X = StandardScaler().fit_transform(data.data)
    
    # Client A: 0-15, Client B: 15-30
    XA = X[:, :15]
    XB = X[:, 15:]
    
    # Correlation between A and B features
    # We want to see if info is redundant.
    # Take first PC of A and B
    from sklearn.decomposition import PCA
    pc_a = PCA(1).fit_transform(XA).flatten()
    pc_b = PCA(1).fit_transform(XB).flatten()
    
    plt.figure(figsize=(5, 4))
    plt.scatter(pc_a, pc_b, c=data.target, cmap='viridis', alpha=0.5, s=10)
    plt.title(f'Breast Cancer Split\nCorr(Client A, Client B) = {np.corrcoef(pc_a, pc_b)[0,1]:.2f}')
    plt.xlabel('Client A (PC1)')
    plt.ylabel('Client B (PC1)')
    plt.grid(True, linestyle='--', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('papers/synergy_fl/figs/data_breast_cancer_split.pdf')
    plt.close()

def explore_medtime_shift():
    print("🔍 Exploring MedTime Sim-to-Real Shift...")
    # Sim
    s_x1, s_x2, s_y = generate_medtime_split_data(n_samples=2000, seed=42)
    # Real (Shifted)
    r_x1, r_x2, r_y = generate_medtime_split_data(n_samples=50, seed=999)
    
    plt.figure(figsize=(8, 4))
    
    # Feature 1 Distribution
    plt.subplot(1, 2, 1)
    # sns.kdeplot removed
    plt.hist(s_x1.flatten(), density=True, alpha=0.5, label='Synthetic', bins=30)
    plt.hist(r_x1.flatten(), density=True, alpha=0.5, label='Real (Test)', bins=10)
    plt.title('Feature Distribution Shift')
    plt.legend()
    
    # Class Balance
    plt.subplot(1, 2, 2)
    plt.bar(['Sim (0)', 'Sim (1)'], [np.mean(s_y==0), np.mean(s_y==1)], alpha=0.5, label='Sim')
    plt.bar(['Real (0)', 'Real (1)'], [np.mean(r_y==0), np.mean(r_y==1)], alpha=0.5, label='Real')
    plt.title('Class Balance')
    plt.legend()
    
    plt.tight_layout()
    plt.savefig('papers/synergy_fl/figs/data_medtime_shift.pdf')
    plt.close()

if __name__ == "__main__":
    os.makedirs('papers/synergy_fl/figs', exist_ok=True)
    explore_xor()
    explore_breast_cancer()
    explore_medtime_shift()
    print("✅ Data exploration complete.")
