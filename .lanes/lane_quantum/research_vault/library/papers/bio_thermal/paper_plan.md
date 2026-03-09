# Paper Plan: Bio-Thermal World Models for Embodied AI

**Target Venue**: NeurIPS (CCF-A) / Nature Machine Intelligence (JCR Q1, IF>10)
**Theme**: Foundational Work in Physics-Informed Embodied Intelligence (PIEI)
**Core Value**: Empowering AI with "Physical Common Sense" for autonomous therapy — seeing the invisible (subcutaneous heat) and predicting the future (thermal evolution).

---

## 1. Title

**English**: Bio-Thermal World Models for Embodied AI: Physics-Informed Cross-modal Perception and Prediction in Autonomous Therapy
**Chinese**: 面向具身智能的生物热力学世界模型：自主理疗中的物理信息跨模态感知与预测

## 2. Core Pitch (The "A-Class" Story)

* **The Problem**: Traditional Embodied AI excels at geometry ("pick and place") and semantics ("open the door") but is blind to **deep physical interactions** (e.g., heat transfer inside biological tissue). In medical therapy, this blindness leads to "invisible, uncontrollable" risks.
* **Our Solution**: Introducing **Bio-Thermal World Models**. Unlike black-box predictors, our model is grounded in the Pennes bio-heat equation. It takes surface signals (IR/RGB) and "hallucinates" the scientifically accurate 3D subcutaneous thermal state, predicting future evolution under robotic intervention.
* **The "Wow" Factor**: "We didn't just train a robot; we built a digital twin of human thermodynamics."
  * **Data Scale**: 1M+ physics-verified interaction frames (generated via CPU cluster).
  * **Depth**: Solving an Inverse Problem (Surface IR -> Volumetric Temperature) in real-time.

---

## 3. Structure & Content

### **Abstract**

* **Pain Point**: Non-invasive therapy (e.g., Moxibustion) relies on intuition because subcutaneous heat is invisible.
* **Proposal**: A Physics-Informed World Model trained via a massive Sim2Data pipeline.
* **Method**: Combines high-fidelity bio-thermal simulation (Pennes equation) with a Transformer-based observer.
* **Result**: Achieves SOTA accuracy in thermal prediction and demonstrates robust Sim2Real transfer on phantoms.

### **1. Introduction**

* **Why Body?** Embodied agents must understand how their actions (e.g., heating) physically alter the environment (human tissue).
* **Why Physics?** Data-driven models fail on OOD (Out-of-Distribution) safety critical cases. Integrating PDEs ensures safety and interpretability.
* **Contribution**:
    1. First large-scale Bio-Thermal Embodied dataset (**Moxi-Sim**).
    2. Novel Architecture: Cross-modal Observer + PINN-guided Predictor.
    3. Demonstration of "X-Ray Vision" for thermal therapy.

### **2. Methodology (The Workload)**

* **3.1 Digital Simulation Engine (CPU Cluster)**
  * **Physics Core**: Embedding Pennes Bio-Heat Equation into NVIDIA Isaac Sim / Custom Solver.
  * **Digital Population**: Procedural generation of 100+ anatomical variants (BMI, age-dependent tissue properties: conductivity, perfusion).
  * **Action Space**: Robot arm holding moxibustion device (heat source modeling).
* **3.2 Bio-Thermal World Model (L20 GPU)**
  * **Architecture**: Transformer-based Encoder-Decoder (e.g., Video Vision Transformer).
  * **Input**: Sequence of $I_{RGB}$, $I_{IR}$, Robot Pose $P_t$.
  * **Latent State**: Voxel-based 3D Heat Map $H_{vol}$ (The "World Model").
  * **Output**: Predicted Surface $I_{IR}^{t+k}$ and Volumetric $H_{vol}^{t+k}$.
* **3.3 Physics-Informed Loss (PINN)**
  * Loss includes a residual term from the heat equation: $\mathcal{L}_{phy} = || \rho c \frac{\partial T}{\partial t} - \nabla \cdot (k \nabla T) - Q_{blood} - Q_{ext} ||^2$.
  * Ensures predictions respect energy conservation.

### **3. Experiments (Saturation Attack)**

* **Exp 1: Reconstruction Accuracy (In-Silico)**
  * **Metric**: MAE/RMSE of predicted subcutaneous temperature vs. Ground Truth (GT) from simulator.
  * **Hypothesis**: PIEI outperforms pure ResNet/TransUnet baselines by >20%.
* **Exp 2: Generalization (OOD)**
  * **Test**: Evaluation on "Extreme Thin" (BMI<18.5) and "Obese" (BMI>30) patient models.
  * **Hypothesis**: Physics constraints prevent physical violations (e.g., >100°C spikes) seen in baseline models.
* **Exp 3: Dynamic Robustness**
  * **Test**: Perturbations (Breathing motion, AC wind cooling).
  * **Hypothesis**: Recurrent World Model maintains lock despite noise.
* **Exp 4: Sim2Real (Validation)**
  * **Setup**: Robotic arm performing moxibustion on a **biomimetic phantom** (agar/silicone with embedded thermocouples).
  * **Result**: IR surface matching is high; internal thermocouple readings align with model predictions.

---

## 4. Execution Plan (3-Week Sprint 🚀)

**Goal**: Complete data generation, model training, and core validation for NeurIPS submission.

| Phase | Days | Core Task | Hardware | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Week 1: Foundations** | D1-D3 | **Fix Newton Engine** (Bug: Norm Stats), Scale Sim2Data to 1M frames. | CPU Cluster | **IN PROGRESS** |
| | D4-D7 | **Train World Model V1**. Baseline comparisons (FNO/UNet). | L20 GPU | Pending |
| **Week 2: Deep Dive** | D8-D10 | **OOD Stress Tests**. Integrate PINN Loss. | L20 GPU | Pending |
| | D11-D14 | **Sim2Real Validation**. Phantom experiments with thermal cam. | Robot Arm | Pending |
| **Week 3: Polish** | D15-D21 | **Paper Writing**. Final Plots. Video Demo Generation. | - | Pending |

**Immediate Action**: Fix `src/newton/train_newton.py` logic for saving normalizers to ensure valid experimental results.
