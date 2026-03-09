# AI4S Engineering Standards (Industrial Grade)

## 1. 🏗️ Architecture & Philosophy
*   **Modularity**: Code MUST be modular. Separation of concerns (Config, Data, Model, Trainer, Eval).
*   **Abstraction**: Use abstract base classes for Models and Datasets to allow easy extension.
*   **Testing**: Unit tests for core modules. Integration tests for the full pipeline.
*   **CLI-First**: All hyperparameters MUST be configurable via `argparse` or `hydra`. No hardcoded values.

## 2. ⚡ Infrastructure Priority
*   **Primary**: **NVIDIA L20 Cluster** (Local SSH).
    *   *Why*: High memory, fast interconnect, persistent storage.
*   **Secondary**: **Kaggle P100** (Remote).
    *   *Why*: Bulk parallel runs, TTA (Test Time Augmentation).
*   **Optimization**:
    *   Use `Mixed Precision (AMP)` where possible.
    *   Use `DataLoader` with appropriate `num_workers`.
    *   Profile code to remove bottlenecks.

## 3. 📊 Tracking & Observability (Weights & Biases)
*   **Mandatory**: Every experiment MUST log to **WandB**.
*   **Run Naming**:
    *   Format: `{model}_{task}_{timestamp}_{id}`
    *   Example: `MedTime_Extraction_20240203_A1`
*   **Metrics**: Log `train_loss`, `val_loss`, `f1_score`, `accuracy` per epoch.
*   **Artifacts**: Save best model checkpoints as WandB artifacts or local path with clearer naming.

## 4. 📑 Reporting & Logs
*   **Automated Reports**: Experiment script must generate a `report.md` or `results.json` at the end.
*   **Logs**: Use Python `logging` module. Console output key steps; File output detailed debug info.
*   **Evaluation**:
    *   Detailed classification report (Precision/Recall/F1 per class).
    *   Confusion Matrix.
    *   Error Analysis (save top-k worst predictions).

## 5. 🔁 Reproducibility
*   **Seeds**: Set seeds for `torch`, `numpy`, `random`.
*   **Config**: Save the exact configuration used (dump `config.yaml` or `args.json`) in the run directory.
