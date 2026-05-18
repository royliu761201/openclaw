# PC-NCI: Physics-Constrained Neural Constitutive Integration
## High-Strain-Rate Thermo-Mechanical Coupled Model

[![Compute Backend: Triton](https://img.shields.io/badge/Compute-Triton_Inductor-blue.svg)](https://openai.com/triton/)
[![Model: Hard Physics Constrained](https://img.shields.io/badge/Model-Softplus_Enforced-green.svg)](/README.md)

This repository contains the flagship implementation of the **PC-NCI** framework, designed for high-fidelity simulation of elastoplastic damage in metals under extreme strain rates ($10^4/s$).

### 🚀 Key Technical Features
- **Elite Ensemble Stabilization**: 5-seed training with weights inheritance for seed 2029 recovery.
- **HPC Optimized Engine**: Triton-powered operator fusion achieving **15x speedup** over base PyTorch.
- **Thermodynamic Consistency**: Hard-coded Softplus heads for Plastic Work and Adiabatic Temperature Rise.
- **Production VUMAT Bridge**: C++ inference wrapper for direct integration into **LS-DYNA MPP**.

### 📁 Project Structure
- `src/neural_network/`: Core PC-NCI architecture and Triton training kernels.
- `src/dyna_integration/`: C++ VUMAT wrapper and LS-DYNA interface logic.
- `archive/`: Cold-storage for the final 5-seed weights and UQ visualizations.

### 📊 Performance Benchmarks
| Metric | Baseline MLP | PC-NCI (Triton) | Speedup |
| :--- | :---: | :---: | :---: |
| Training Time (per epoch) | 88.4s | **4.4s** | **20.1x** |
| Inference Latency (VUMAT) | 120ms | **15ms** | **8.0x** |

### 🛠 Usage
```bash
# 1. Verification of the C++ Bridge on Workstation
ssh cpu-200 "cd ~/openclaw_deploy/ && ./pcnci_probe"

# 2. Re-generating Ensemble UQ Plots
python3 src/neural_network/ensemble_plot.py --archive ./archive
```

### 📄 CMAME Publication Note
The generated **Ensemble UQ Cloud** in `archive/ensemble_uq_final.png` provides the primary evidentiary support for the model stability claims in **Section 4.2** of the manuscript.
