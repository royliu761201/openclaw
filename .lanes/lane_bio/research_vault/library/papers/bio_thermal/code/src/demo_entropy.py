import numpy as np
import matplotlib.pyplot as plt
import scipy.stats
import pandas as pd
from pathlib import Path

# Config
N_SAMPLES = 200
N_GENES = 1000
MITO_GENES_RATIO = 0.1  # 10% genes are "Energy" genes
OUTPUT_DIR = Path("papers/bio_thermal/figs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def generate_synthetic_data():
    """
    Generates synthetic gene expression data simulating:
    1. Young/Healthy: High Energy, Low Entropy
    2. Aging: Energy Declines, Entropy Increases
    3. Disease (Cancer): High Entropy, Variable Energy (Warburg)
    """
    np.random.seed(42)
    
    # Define gene sets
    n_mito = int(N_GENES * MITO_GENES_RATIO)
    mito_indices = np.arange(n_mito)
    
    data = []
    
    # Cluster 1: Young (High Energy, Low Entropy)
    # Energy genes are highly expressed and tightly regulated (low variance)
    # Other genes are regulated (low entropy)
    for _ in range(N_SAMPLES // 3):
        # Energy genes: High mean, low noise
        expr = np.random.exponential(scale=1.0, size=N_GENES)
        expr[mito_indices] = np.random.normal(loc=5.0, scale=0.5, size=n_mito) 
        # Sharpen distribution to lower entropy
        expr = np.power(expr, 2) 
        data.append({"Age": "Young", "Expr": expr})
        
    # Cluster 2: Aged (Low Energy, High Entropy)
    # Energy genes downregulated
    # Global regulation loss (High Entropy = flatter distribution)
    for _ in range(N_SAMPLES // 3):
        expr = np.random.exponential(scale=2.0, size=N_GENES) # Higher noise base
        expr[mito_indices] = np.random.normal(loc=2.0, scale=1.0, size=n_mito) # Lower energy
        data.append({"Age": "Aged", "Expr": expr})
        
    # Cluster 3: Cancer (Critical Criticality)
    # High Entropy (Chaos)
    for _ in range(N_SAMPLES // 3):
        expr = np.random.uniform(0, 10, size=N_GENES) # Max entropy (Uniform)
        data.append({"Age": "Cancer", "Expr": expr})
        
    return data, mito_indices

def calculate_metrics(data, mito_indices):
    results = []
    for sample in data:
        expr = sample["Expr"]
        # Normalize for Entropy
        p = expr / np.sum(expr)
        entropy = scipy.stats.entropy(p)
        
        # Energy Score (Mean of Mito Genes)
        energy_score = np.mean(expr[mito_indices])
        
        results.append({
            "Age": sample["Age"],
            "Entropy": entropy,
            "Energy": energy_score
        })
    return pd.DataFrame(results)

def plot_phase_plane(df):
    plt.figure(figsize=(10, 8))
    # Map ages to colors
    colors = {"Young": "green", "Aged": "orange", "Cancer": "red"}
    
    for age_group in ["Young", "Aged", "Cancer"]:
        subset = df[df["Age"] == age_group]
        plt.scatter(subset["Energy"], subset["Entropy"], 
                   c=colors[age_group], label=age_group, s=100, alpha=0.7, edgecolors='w')
    
    plt.title("Bio-Thermal Phase Plane: Energy vs. Entropy")
    plt.xlabel("Mito-Energetic Score (Energy Supply)")
    plt.ylabel("Transcriptional Entropy (Information Disorder)")
    
    # Add homeostatic limit line
    young_entropy_mean = df[df["Age"]=="Young"]["Entropy"].mean()
    plt.axhline(young_entropy_mean, color='g', linestyle='--', alpha=0.3, label="Homeostatic Limit")
    
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    save_path = OUTPUT_DIR / "energy_entropy_simulation.png"
    plt.savefig(save_path)
    print(f"✅ Plot saved to {save_path}")

if __name__ == "__main__":
    print("🧪 Bio-Thermal Tracker: Generating Synthetic Data...")
    raw_data, mito_idx = generate_synthetic_data()
    
    print("🧮 Calculating Energy-Entropy Metrics...")
    df = calculate_metrics(raw_data, mito_idx)
    
    print("📈 Visualizing Phase Plane...")
    plot_phase_plane(df)
    print("Done.")
