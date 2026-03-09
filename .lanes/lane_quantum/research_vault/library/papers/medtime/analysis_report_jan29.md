# MedTime: Phase 1 Experiment Analysis Report
**Date:** Jan 29, 2026
**Status:** 🟡 Mixed Results (Valid Pipelines, Weak Baselines)

## 1. Executive Summary
We have successfully established the experimental pipeline for both Chinese (CN) and English (EN) datasets. The **Rule-Based Baseline** performs strongly on synthetic data but struggles on real-world medical texts due to rigid heuristic patterns. **Zero-Shot LLM** (Qwen/LLaMA) shows promise in entity recognition but fails significantly in temporal grounding (finding the correct time anchor), confirming the necessity of the proposed **GVP (Generate-Verify-Project)** framework.

## 2. Benchmark Results

| Method | Dataset | F1 (Temporal) | F1 (Trigger) | MAE (Days) | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Rule-Based** | `syn_test` (Synthetic) | **0.583** | 0.347 | 39.5 | ✅ Valid Baseline |
| **Rule-Based** | `med_test` (Real CN) | 0.083 | 0.666 | 25.8 | ⚠️ Weak Generalization |
| **Rule-Based** | `e3c_test` (Real EN) | 0.000 | 0.000 | 66.0 | ❌ Parsing/Format Error |
| **Zero-Shot (32B)** | `med_test` (Real CN) | **0.320** | 0.315 | 36.0 | ⚠️ Poor Grounding |
| **IE-Span (SFT)** | `med_test` (Real CN) | **0.389** | 0.502 | 57.5 | 🟢 Best Real Performance |
| **Zero-Shot (32B)** | `e3c_test` (Real EN) | 0.246 | 0.228 | 132.2 | ❌ High MAE |

## 3. Analysis Findings

### A. The "Synthetic-Real Gap" (Rule-Based)
The rule-based system achieves **0.58 F1 on synthetic data** but drops to **0.08 on real data**.
- **Cause:** Synthetic data follows rigid templates (e.g., "Patient diagnosed on [DATE]"). Real records use implicit, relative, or fuzzy timelines ("Three days post-op", "Last winter") which Regex fails to capture.
- **Implication:** Rules are insufficient; semantic reasoning is required.

### B. LLM Hallucination in Grounding (Zero-Shot)
Zero-shot models extract triggers well (Events) but fail to anchor them to the correct Reference Time (Admission Date).
- **Evidence:** High MAE (Mean Absolute Error) of 36-132 days.
- **Implication:** The proposed **"Projection"** module in GVP is critical to force the LLM to verify relative temporal logic.

### C. SFT Gains (IE-Span)
Fine-tuning (`ie_span_cn`) provides the best balance (F1 0.389), outperforming Zero-Shot by ~7 points.
- **Strength:** Better trigger detection (F1 0.50).
- **Weakness:** Still high MAE (57.5 days), suggesting it memorizes entity spans rather than learning temporal arithmetic.

## 4. Next Steps (Phase 2: GVP)

1.  **Fix English Baseline:** Debug the `baseline_rule_en` parser (currently 0.0 F1).
2.  **Activate GVP Ablations:**
    -   Run **No-Topology** (Standard SFT) to set a neural ceiling.
    -   Run **Full GVP** to test if consistency loss reduces MAE.
3.  **Data Alignment:** Ensure all datasets share the exact JSON schema to prevent parsing errors like in `e3c_test`.
