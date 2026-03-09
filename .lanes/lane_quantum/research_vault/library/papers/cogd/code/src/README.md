# CoGD-Net: Conditional Graph Diffusion for Long-Tail Object Segmentation

This directory contains the core implementation of the CoGD-Net framework.

## 1. 📂 Data Organization

The system expects datasets to be organized in the `data/` directory (or specified via `--data_dir`).

**Structure:**

```
data/
├── piccolo/
│   ├── train/
│   │   ├── images/  # .png (WLI)
│   │   └── masks/   # .png (Binary)
│   └── test/ ...
├── kvasir/
│   ├── train/ ...
│   └── test/ ...
└── cvc/
    └── ...
```

* **Config Reference**: Dataset paths are managed in `src/cogd/config.py`.
* **Overrides**: Use `--data_dir /path/to/datasets` to point to a custom location.

---

## 2. 🔥 Training

Use `train_cogd.py` (located in project root) to launch experiments. The `--exp_id` argument controls the configuration mixin.

**Basic Training:**

```bash
python train_cogd.py --exp_id E1_CoGD_InDomain
```

**Common Experiment IDs:**

* `E1_CoGD_InDomain`: Train on Kvasir+CVC, Test on Kvasir+CVC.
* `E2_CoGD_PICCOLO`: Train on PICCOLO (w/ synthetic), Test on PICCOLO.
* `Ablation_NoGraft`: Train without the Graph Diffusion module (Baseline).
* `Baseline_SAM2`: Pure SAM2 architecture (No CoGD components).

**Arguments:**

* `--smoke_test`: Run 1 epoch on a tiny subset (debug).
* `--batch_size N`: Override default batch size.

---

## 3. 🔮 Evaluation (Inference)

To evaluate a trained model, use the `--inference` flag along with `--resume`.

**Command:**

```bash
python train_cogd.py \
    --exp_id E1_CoGD_InDomain \
    --inference \
    --resume medtime_results/E1_CoGD_InDomain/checkpoints/epoch_50.pt
```

* **Output**: Results are saved to `medtime_results/<exp_id>/inference_results.csv`.
* **Visuals**: Sample predictions are saved in `medtime_results/<exp_id>/visualizations/`.

---

## 4. 🔄 Resuming Training

To continue a training run from a crash or specific epoch:

**Command:**

```bash
python train_cogd.py \
    --exp_id E1_CoGD_InDomain \
    --resume medtime_results/E1_CoGD_InDomain/checkpoints/epoch_20.pt
```

* **Note**: The optimizer state is currently *not* fully restored in this simplified script (logic loads `model.load_state_dict`). For full state resumption, ensure `optimizer` is also saved/loaded in `train_cogd.py` (Current implementation focuses on model weights).

---

## 5. 🛠️ Development

* **Config**: See `src/cogd/config.py` for hyperparameter defaults.
* **Model**: Core logic is in `src/cogd/models/cogd.py`.
* **Metrics**: `dice`, `iou`, `hd95` are calculated in `src/cogd/metrics.py`.
