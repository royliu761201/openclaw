---
name: wandb
description: Interact with Weights & Biases (Log metrics, List runs).
metadata: { "openclaw": { "requires": { "bins": ["python3"] }, "install": [ { "id": "pip-install", "kind": "pip", "label": "Install WandB", "packages": ["wandb", "python-dotenv"] } ] } }
---

# Weights & Biases Skill

Log metrics and manage runs on WandB.

## Disallowing Global Telemetry Bloat
> **[L1 Constitution Block - Anti-Bloat Law]**: W&B naturally defaults to writing `./wandb/` folders in the current working directory, which often bloats the SSoT Git repo with thousands of telemetry files.
> You MUST explicitly set the environment variable `WANDB_DIR` to route output to a Git-ignored `results/` or `outputs/` folder before launching python training scripts (e.g., `WANDB_DIR=./results/wandb python main.py`).

## Tools

### `wandb_log`
Log a metric to a project.

- **project** (string, required): Project name.
- **metric** (string, required): Metric name (e.g., "accuracy").
- **value** (number, required): Metric value.

**Usage**:
```bash
python3 skills/wandb/scripts/wandb_tool.py log --project "openclaw-test" --metric "accuracy" --value 0.95
```

### `wandb_runs`
List recent runs in a project.

- **path** (string, required): Project path (entity/project).
- **limit** (number, optional): Max runs to return (default: 10).

**Usage**:
```bash
python3 skills/wandb/scripts/wandb_tool.py runs --path "xiaohualiu/openclaw-test" --limit 5
```
