import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import pandas as pd
from pathlib import Path

# Config
N_SAMPLES = 300
OUTPUT_DIR = Path("papers/bio_thermal/figs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def generate_unified_field_data():
    """
    Simulates the 3D Unified Field:
    - Health: High Energy (E), Low Entropy (S), Low Force (F).
    - Aging: Low Energy (E), Med Entropy (S), Low Force (F).
    - Cancer: High Energy Flux (E_flux), High Entropy (S), High Force (F).
    """
    np.random.seed(2026)
    data = []
    
    # 1. Health (The "Low Entropy" Attractor)
    # High Efficiency, Low Mechanical Stress
    for _ in range(100):
        force = np.random.normal(1.0, 0.2)  # Soft
        energy_efficiency = np.random.normal(0.9, 0.05) # High
        # Entropy is low because Energy is high enough to pay for repair
        entropy = np.random.normal(2.0, 0.3) 
        data.append({"State": "Health", "F": force, "E": energy_efficiency, "S": entropy})
        
    # 2. Aging (The "Energy Crisis" Drift)
    # Energy Fades -> Entropy Rises slightly
    for _ in range(100):
        force = np.random.normal(1.2, 0.3) # Slightly stiffer
        energy_efficiency = np.random.normal(0.4, 0.1) # Declining
        # Entropy rises due to lack of repair energy
        entropy = np.random.normal(4.0, 0.5) 
        data.append({"State": "Aging", "F": force, "E": energy_efficiency, "S": entropy})
        
    # 3. Cancer (The "Physical Phase Transition")
    # Force Spikes -> Entropy Explodes. 
    # Energy changes from "Efficiency" to "Flux" (Warburg), but here we plot "Orderly Energy" which is low.
    for _ in range(100):
        force = np.random.normal(5.0, 1.0) # Stiff (Stiffness-Induced)
        energy_efficiency = np.random.normal(0.2, 0.1) # Dysfunctional OXPHOS
        # Entropy explodes due to Force + Lack of Control
        entropy = force * 1.5 + np.random.normal(0, 0.5) 
        data.append({"State": "Cancer", "F": force, "E": energy_efficiency, "S": entropy})
        
    return pd.DataFrame(data)

def plot_3d_manifold(df):
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')
    
    colors = {"Health": "green", "Aging": "orange", "Cancer": "red"}
    markers = {"Health": "o", "Aging": "^", "Cancer": "x"}
    
    for state in ["Health", "Aging", "Cancer"]:
        subset = df[df["State"] == state]
        ax.scatter(subset["E"], subset["F"], subset["S"], 
                  c=colors[state], marker=markers[state], s=80, label=state, alpha=0.6)
        
    ax.set_xlabel('Mitochondrial Efficiency ($E_{eff}$)')
    ax.set_ylabel('ECM Stiffness / Force ($F$)')
    ax.set_zlabel('Transcriptomic Entropy ($S$)')
    ax.set_title('The Unified Bio-Thermal Phase Space\nTransition from Homeostasis to Collapse')
    
    # Draw trajectory arrows (conceptual)
    # Health -> Aging
    h_mean = df[df["State"]=="Health"].mean(numeric_only=True)
    a_mean = df[df["State"]=="Aging"].mean(numeric_only=True)
    c_mean = df[df["State"]=="Cancer"].mean(numeric_only=True)
    
    ax.quiver(h_mean["E"], h_mean["F"], h_mean["S"], 
              a_mean["E"]-h_mean["E"], a_mean["F"]-h_mean["F"], a_mean["S"]-h_mean["S"], 
              color='k', arrow_length_ratio=0.1, alpha=0.5, label="Aging Drift")
              
    ax.quiver(a_mean["E"], a_mean["F"], a_mean["S"], 
              c_mean["E"]-a_mean["E"], c_mean["F"]-a_mean["F"], c_mean["S"]-a_mean["S"], 
              color='red', arrow_length_ratio=0.1, alpha=0.8, label="Carcinogenic Collapse")

    plt.legend()
    
    save_path = OUTPUT_DIR / "unified_3d_phase_space.png"
    plt.savefig(save_path)
    print(f"✅ Plot saved to {save_path}")

if __name__ == "__main__":
    print("🌌 Simulating Unified Bio-Thermal Field...")
    df = generate_unified_field_data()
    
    print("🎥 Rendering 3D Manifold...")
    plot_3d_manifold(df)
