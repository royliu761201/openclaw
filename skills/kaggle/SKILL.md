---
name: kaggle
description: Interact with Kaggle API (Datasets, Kernels).
metadata: { "openclaw": { "requires": { "env": ["KAGGLE_USERNAME", "KAGGLE_KEY"] } } }
---

# Kaggle Skill

Advanced tools for Kaggle automation. Requires `dotenv` loaded credentials or `~/.kaggle/kaggle.json`.

## Tools

### `dataset_push`
Create or update a Kaggle dataset. Code-as-Dataset supported.

- **path** (string, required): Local folder containing `dataset-metadata.json` and files.
- **message** (string, optional): Version note.
- **zip** (flag): If set, uploads as a zip archive (auto-zips folder content).

**Usage**:
```bash
python skills/kaggle/scripts/kaggle_tool.py dataset_push "workspace/my_dataset" -m "Update" -z
```

### `kernel_push`
Push (deploy) a kernel to Kaggle.

- **path** (string, required): Local folder containing `kernel-metadata.json` and script file.

**Usage**:
```bash
python skills/kaggle/scripts/kaggle_tool.py kernel_push "workspace/my_kernel"
```

### `kernels_list`
List kernels to check status.

- **user** (string, optional): Filter by user.
- **search** (string, optional): Filter by title text.

**Usage**:
```bash
python skills/kaggle/scripts/kaggle_tool.py kernels_list --user "username" --search "openclaw"
```

### `kernels_output`
Download logs and output files from a kernel run.

- **slug** (string, required): Kernel slug (e.g., `username/kernel-slug`).
- **path** (string, required): Destination folder.

**Usage**:
```bash
python skills/kaggle/scripts/kaggle_tool.py kernels_output "xiaohualiu/openclaw-experiment" "workspace/output"
```

## Troubleshooting (FAQ)

### Execution Failed?
If a kernel execution fails:
1.  **Check Status**: Use `kernels_list` to see if it's "error" or "running".
2.  **Get Logs**: Use `kernels_output` to download the log files (`.log`).
3.  **Auth Errors (403)**: Ensure `.env` has valid `KAGGLE_USERNAME` and `KAGGLE_KEY`.
4.  **Conflict (409)**: The kernel slug exists. Append a timestamp or delete the old kernel via Web UI.
