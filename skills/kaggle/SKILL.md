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

## Remote Standards (Heavy Asset Visa Enforcement)

> **[L1 Constitution Block - INTEL-FETCH REQUIRED]**: 
> Kaggle datasets are often massive archives. **You are strictly forbidden** from downloading Kaggle datasets natively within this skill or dumping them into `~/workspace/projects_core/`.
> 
> 👉 **To download Kaggle Datasets, you MUST invoke the `intel-fetch` Macro-Skill.** `intel-fetch` implements the required "Node 05 US Proxy Jump" and "Node 03 Vault Symlinking" to safely load the assets without crashing the Git SSoT or stalling behind GFW.
>
> This `kaggle` skill is NOW STRICTLY limited to executing code (Kernels) and uploading outputs (`dataset_push`).

### Dependencies
- The `kaggle` Python package installed globally or in the active python environment.
- Sufficient disk space for datasets.

[L1 Constitution Block]

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

### `kaggle_remote_fetch` (MD-Driven KISS Protocol)

🔥 **High-Level Protocol**🔥 For heavy assets, do NOT run tasks locally. Instead of relying on Python payload wrappers, we use raw MD-driven SSH sequences to utilize high-bandwidth execution nodes (e.g. Node 02, Node 05). **NOTE**: The remote node does not need `openclaw` installed, it merely uses standard `huggingface-cli` and `kaggle` tools.

**Usage (Raw CLI Protocol via `ssh_tool.py`)**:

```bash
# 1. SSH into high-bandwidth gateway (e.g. Node 02 or 05) to pull raw files directly from HF
ssh_tool.py --host 02 exec "huggingface-cli download THU-ATOM/posebusters --repo-type dataset --local-dir /tmp/posebusters"

# 2. Assemble minimal Kaggle metadata physically on the remote edge
ssh_tool.py --host 02 exec "echo '{\"title\": \"posebusters-data\", \"id\": \"YOUR_USERNAME/posebusters-data\", \"licenses\": [{\"name\": \"CC0-1.0\"}]}' > /tmp/posebusters/dataset-metadata.json"

# 3. Inject strict secret context & push cloud payload entirely natively
ssh_tool.py --host 02 --env "KAGGLE_USERNAME=xxx" --env "KAGGLE_KEY=yyy" exec "kaggle datasets create -p /tmp/posebusters --dir-mode zip"
```

## Troubleshooting (FAQ)

### Execution Failed?

If a kernel execution fails:

1.  **Check Status**: Use `kernels_list` to see if it's "error" or "running".
2.  **Get Logs**: Use `kernels_output` to download the log files (`.log`).
3.  **Auth Errors (403)**: Ensure `.env` has valid `KAGGLE_USERNAME` and `KAGGLE_KEY`.
4.  **Conflict (409)**: The kernel slug exists. Append a timestamp or delete the old kernel via Web UI.
