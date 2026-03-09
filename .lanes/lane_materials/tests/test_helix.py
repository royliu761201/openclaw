import asyncio
import os
import sys

# Add src to path
sys.path.append(os.path.abspath("src"))

from core.double_helix import DoubleHelix

def test_helix_scaffolding():
    print("=== Testing Double Helix Scaffolding ===")
    
    helix = DoubleHelix(base_path="tests/helix_data")
    
    # Mock LaTeX content with placeholders
    latex_source = r"""
    \section{Results}
    Our method achieves a top-1 accuracy of \newcommand{\OurAccuracy}{PENDING} on ImageNet, 
    outperforming the baseline spread of \newcommand{\BaselineSpread}{PENDING}.
    Speed wise, we clock in at \newcommand{\InferenceSpeed}{TBD} ms per batch.
    """
    
    print("\n[Input LaTeX Scanned]")
    # 1. Scan
    placeholders = helix.scan_paper_placeholders(latex_source)
    assert len(placeholders) == 3
    print(f"Detected Placeholders: {[p['command'] for p in placeholders]}")
    
    # 2. Derive Tasks
    tasks = helix.derive_experiments(placeholders)
    print(f"\n[Derived Experiments]")
    for t in tasks:
        print(f"- {t['goal']} (Metric: {t['metric']})")
        
    assert len(tasks) >= 2 # Accuracy and Speed detected

if __name__ == "__main__":
    test_helix_scaffolding()
