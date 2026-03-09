import numpy as np
import matplotlib.pyplot as plt
import scipy.stats
import pandas as pd
from pathlib import Path

# Config
N_SAMPLES = 300
N_GENES = 2000
OUTPUT_DIR = Path("papers/bio_thermal/figs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def generate_cancer_physics_data():
    """
    Simulates the "Force-Entropy" coupling in Cancer.
    Hypothesis: Stiff ECM (Force) -> Nuclear Deformation -> Chromatin Opening -> High Entropy.
    """
    np.random.seed(2026)
    
    data = []
    
    # 1. Normal Tissue (Soft, Low Entropy)
    for _ in range(100):
        # Soft ECM: Low expression of Collagen/LOX
        stiffness = np.random.normal(loc=2.0, scale=0.5)
        # Low Entropy: Gene expression is highly structured (peaked)
        expr_profile = np.random.zipf(a=2.5, size=N_GENES) 
        data.append({"Type": "Normal", "Stiffness": stiffness, "Expr": expr_profile})
        
    # 2. Benign Tumor (Moderately Stiff, Moderate Entropy)
    for _ in range(100):
        stiffness = np.random.normal(loc=5.0, scale=1.0)
        # Moderate Entropy
        expr_profile = np.random.zipf(a=2.0, size=N_GENES)
        data.append({"Type": "Benign", "Stiffness": stiffness, "Expr": expr_profile})
        
    # 3. Malignant/Invasive (Hard, High Entropy)
    # The "Force-Feedback" Loop: Stiffness directly adds noise to expression
    for _ in range(100):
        base_stiffness = np.random.normal(loc=8.0, scale=1.5)
        
        # Physical Coupling: Higher Stiffness -> Higher Noise
        noise_level = base_stiffness * 0.5 
        
        # High Entropy: Flatter distribution (Zipf parameter approaches 1.0)
        # We simulate this by adding uniform noise proportional to stiffness
        base_expr = np.random.zipf(a=1.5, size=N_GENES)
        noise = np.random.uniform(0, noise_level, size=N_GENES)
        expr_profile = base_expr + noise
        
        data.append({"Type": "Malignant", "Stiffness": base_stiffness, "Expr": expr_profile})
        
    return data

def analyze_force_entropy(data):
    results = []
    for sample in data:
        expr = sample["Expr"]
        # Normalize
        p = expr / np.sum(expr)
        entropy = scipy.stats.entropy(p)
        
        results.append({
            "Type": sample["Type"],
            "Stiffness_Index": sample["Stiffness"], # Proxy for Force (F)
            "Transcriptomic_Entropy": entropy       # Proxy for Information Disorder (S)
        })
    return pd.DataFrame(results)

def plot_force_entropy_coupling(df):
    plt.figure(figsize=(10, 8))
    
    colors = {"Normal": "blue", "Benign": "orange", "Malignant": "red"}
    
    for t in ["Normal", "Benign", "Malignant"]:
        subset = df[df["Type"] == t]
        plt.scatter(subset["Stiffness_Index"], subset["Transcriptomic_Entropy"],
                   c=colors[t], label=t, s=80, alpha=0.7, edgecolors='w')
        
    # Fit a regression line to show the "Law"
    z = np.polyfit(df["Stiffness_Index"], df["Transcriptomic_Entropy"], 1)
    p = np.poly1d(z)
    plt.plot(df["Stiffness_Index"], p(df["Stiffness_Index"]), "k--", alpha=0.5, label=f"Coupling Law ($S \\propto F$)")
    
    plt.title("The Physical Origin of Cancer: Force-Entropy Coupling")
    plt.xlabel("ECM Stiffness Index (Force $F$)")
    plt.ylabel("Transcriptomic Entropy (Disorder $S$)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    save_path = OUTPUT_DIR / "cancer_force_entropy.png"
    plt.savefig(save_path)
    print(f"✅ Plot saved to {save_path}")

if __name__ == "__main__":
    print("🧬 Simulating Cancer Physical Homeostasis...")
    raw = generate_cancer_physics_data()
    
    print("📐 Calculating 4D Metrics...")
    df = analyze_force_entropy(raw)
    
    print("📊 Visualizing Coupling...")
    plot_force_entropy_coupling(df)
