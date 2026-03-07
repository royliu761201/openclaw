---
name: forge-fetch
description: Use this skill to securely and asynchronously synchronize massive datasets from external sources (HuggingFace/Kaggle) directly to the GPU Forge and Node 03 Vault. It enforces the GPU-First, compute-centric Fetching Protocol.
metadata: { "openclaw": { "requires": { "bins": ["python3"] } } }
---

# 🔄 GPU-First Data Synchronization

This skill enforces the "Data follows Compute" (数据跟计算跑) hardware law established in `07_HARDWARE_NETWORK_LAW.md`.

## Workflow
It performs the following strict sequence asynchronously:
1. **Node 01 Immunity**: Forces a `.gitignore` into the project's data directory to prevent Git bloat.
2. **GPU Native Fetch**: Bypasses intermediate nodes by deploying an asynchronous `nohup` worker directly onto the target GPU. The worker utilizes the GPU's local reverse tunnel (`socks5h://127.0.0.1:7890`) to download the asset at maximum speed directly to the computing disk. 
3. **Vault Replication**: Once downloaded, the GPU worker automatically SCPs a backup of the high-value asset back to the Node 03 (Vault) for permanent disaster recovery and cross-node sharing.

## Tools

### `forge_fetch`

Initiates the secure asynchronous download and backup pipeline.

- **project** (string, required): The root name of the project receiving the data (e.g., `PESSO` or `CaLaM`).
- **source_url** (string, required): The URL pointing to the heavy asset (HuggingFace/DaRUS/Kaggle file).
- **filename** (string, required): The destination filename to be written (e.g., `1D_CFD_Train.hdf5`).
- **target_gpu** (string, optional): The SSH alias of the target compute server. Defaults to `gpu02`.

**Usage**:

```bash
python3 /Users/roy-jd/Documents/projects/openclaw/skills/forge-fetch/scripts/forge_fetch.py \
    --project "PESSO" \
    --source_url "https://huggingface.co/..." \
    --filename "dataset.h5" \
    --target_gpu "gpu02"
```

## Anti-Pattern Detection
This skill explicitly replaces and obsoletes the legacy `proxy_downloader` which wasted bandwidth by hopping through Node 05 and Node 01 before reaching the GPU.
