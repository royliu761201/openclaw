---
name: kaggle
emoji: 🏅
description: Interact with Kaggle API (Datasets, Kernels).
metadata: { "openclaw": { "requires": { "bins": ["python3"] } } }
---

# Kaggle Skill

Advanced tools for Kaggle automation.

## Requirements

The script requires Kaggle authentication credentials. You can provide these in two ways:

1.  **Environment Variables** (Recommended):
    Add the following to your project's `.env` file:
    ```bash
    KAGGLE_USERNAME=your_username
    KAGGLE_KEY=your_key
    ```
2.  **Kaggle CLI Config**:
    Place your `kaggle.json` key file in `~/.kaggle/kaggle.json`.

## Remote Standards (L20 Cluster)

**CRITICAL**: When running on the remote server (`research-bot`), adhere to these paths:

1.  **Data Download**: ALWAYS download datasets to `/root/research_bot/data/kaggle/[dataset_name]`.
    - Do NOT download to the project folder. Use `ln -s` to link it.
2.  **Kernels**: Run kernels that output to `/root/research_bot/results/kaggle`.

## Tools

### `kaggle_dataset_push`

Create or update a Kaggle dataset. Code-as-Dataset supported.

- **path** (string, required): Local folder containing `dataset-metadata.json` and files.
- **message** (string, optional): Version note.
- **zip** (flag): If set, uploads as a zip archive (auto-zips folder content).

**Usage**:

```bash
./scripts/kaggle_tool.py dataset_push "workspace/my_dataset" -m "Update" -z
```

### `kaggle_kernel_push`

Push (deploy) a kernel to Kaggle.

- **path** (string, required): Local folder containing `kernel-metadata.json` and script file.

**Usage**:

```bash
./scripts/kaggle_tool.py kernel_push "workspace/my_kernel"
```

### `kaggle_kernels_list`

List kernels to check status.

- **user** (string, optional): Filter by user. If omitted, lists **your** kernels.
- **search** (string, optional): Filter by title text.

**Usage**:

```bash
./scripts/kaggle_tool.py kernels_list --user "username" --search "openclaw"
```

### `kaggle_kernels_output`

Download logs and output files from a kernel run.

- **slug** (string, required): Kernel slug (e.g., `username/kernel-slug`).
- **path** (string, required): Destination folder.

**Usage**:

```bash
./scripts/kaggle_tool.py kernels_output "xiaohualiu/openclaw-experiment" "workspace/output"
```

## Troubleshooting (FAQ)

### Execution Failed?

If a kernel execution fails:

1.  **Check Status**: Use `kernels_list` to see if it's "error" or "running".
2.  **Get Logs**: Use `kernels_output` to download the log files (`.log`).
3.  **Auth Errors (403)**: Ensure `.env` has valid `KAGGLE_USERNAME` and `KAGGLE_KEY`.
4.  **Conflict (409)**: The kernel slug exists. Append a timestamp or delete the old kernel via Web UI.
