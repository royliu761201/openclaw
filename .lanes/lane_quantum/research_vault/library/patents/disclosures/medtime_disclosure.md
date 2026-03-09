# Technical Disclosure: MedTime System

**Internal Ref:** AI4S-PAT-003
**Title:** SYSTEM AND METHOD FOR TOPOLOGICAL CONSISTENCY ENFORCEMENT IN LONGITUDINAL EVENT EXTRACTION
**Project:** MedTime (Medical Temporal Reasoning)

> [!NOTE]
> Refined according to `PATENT_STANDARDS.md`. Focus: Logic/Hardware Failure Correction.

## 1. Technical Field
The present invention relates to the field of Natural Language Processing (NLP) and Clinical Informatics, specifically to a **Generate-Verify-Project (GVP)** architecture for ensuring causal and temporal logic consistency in large-scale unstructured data extraction.

## 2. Background and Technical Problem

### 2.1 The Technical Defect
In processing "Longitudinal Data" (e.g., Electronic Health Records, Financial Logs), existing sequence-to-sequence models (LLMs) exhibit a specific defect: **"Temporal Hallucination"**.
*   **Root Cause:** Standard Self-Attention mechanisms encode position ($PE$) but do not encode directed graph topology ($G_{time}$).
*   **Manifestation:** generated events frequently violate physical causality (e.g., *Surgery* timestamped after *Discharge*, or *Diagnosis* timestamped before *Symptom Onset*).
*   **Failure Mode:** On complex clinical benchmarks (MedTime-CN), state-of-the-art models (e.g., Qwen-72B) achieve only **28.2% F1** in Zero-Shot settings due to these topology violations.

### 2.2 Limitation of Prior Art
*   **Rule-based Systems:** Brittle, cannot handle linguistic variety (Recall < 40%).
*   **Standard SFT (Supervised Fine-Tuning):** Fits language statistics but not logic; requires massive annotated data.
*   **RLHF:** Expensive human feedback, hard to optimize for discrete logic constraints.

## 3. Technical Solution: GVP Architecture

The invention proposes a modular **Neuro-Symbolic System** comprising three coupled processing units:

### 3.1 Module 1: Event Generator ($\mathcal{G}$)
*   **Function:** Extracts raw event mentions $(e, t)$ from unstructured text.
*   **Implementation:** A finetuned Transformer model optimized for "Recall" rather than Precision. It generates a "Candidate Graph" $G_{cand}$ which may contain logic errors.

### 3.2 Module 2: Topology Verifier ($\mathcal{V}$)
*   **Function:** A discriminative model (Logic Critic) that scores the validity of event pairs.
*   **Mechanism:** It does not predict text. It takes pairs $(e_i, e_j)$ and predicts a relation $R \in \{<, >, =\}$.
*   **Output:** A formulation of "Hard Constraints" (e.g., $t_{admission} \le t_{surgery} \le t_{discharge}$).

### 3.3 Module 3: Manifold Projector ($\mathcal{P}$)
*   **Function:** **Core Innovation**. A differentiable optimization layer (or discrete search) that projects the flawed output of $\mathcal{G}$ onto the "Valid Manifold" defined by $\mathcal{V}$.
*   **Hardware Implementation:** This projection occurs at **Inference Time** (Test-Time) without retraining the large model.
*   **Algorithm:** Solves: $\hat{y} = \arg\min_{y} ||y - \mathcal{G}(x)|| \text{ s.t. } \mathcal{V}(y) = \text{Valid}$.

## 4. Technical Effects (Beneficial Results)

1.  **Solution to Temporal Hallucination:**
    *   By explicitly enforcing constraints via $\mathcal{P}$, the system eliminates "impossible timelines".
    *   **Metric:** Temporal F1 score improved from 28.2% (Baseline) to **84.2%** (SOTA) on the verified MedTime-CN dataset.

2.  **Logic-Language Decoupling (Cross-Lingual Transfer):**
    *   Because "Time is Universal" (topology is language-agnostic), the Verifier trained on Chinese logic successfully corrects English errors.
    *   **Result:** Zero-shot transfer to English (E3C dataset) achieved **50.0% F1**, double the baseline (24.6%).

3.  **High-Precision Alignment:**
    *   Mean Absolute Error (MAE) reduced to **3.2 days**, enabling deployment in critical Clinical Decision Support (CDS) systems where 40-day errors are unacceptable.

## 5. Exemplary Embodiments

### 5.1 Cloud-Based Clinical API
*   Input: Unstructured Medical PDF/Note.
*   Processing: Parallel generation of events -> GPU-accelerated Constraint Solving (Projector) -> JSON Output.
*   Output: Structural Timeline for Insurance Audit.

### 5.2 Edge-Device "Active Correction"
*   Deployed on a doctor's tablet. The "Verifier" runs locally (lightweight) to flag timeline errors in real-time dictation ("Doctor, you said discharge was before surgery?").

## 6. Claims (Draft Points)

1.  **A Method** for extracting temporally consistent event sequences, comprising:
    *   Generating a set of candidate events utilizing a generative probabilistic model;
    *   Constructing a topological constraint graph via a discriminative verifier model;
    *   Projecting said candidate events onto a valid solution space defined by said constraint graph to minimize a temporal logic loss.

2.  **The Method of Claim 1**, wherein the projection is performed at inference time utilizing a constrained optimization algorithm.

3.  **A System** comprising a processor configured to execute the method of claim 1, specifically adapted to process Electronic Health Records (EHR).
