---
name: gpu-downloader
description: Use this skill to securely and asynchronously synchronize massive datasets from external sources (HuggingFace/Kaggle) directly to the GPU Forge and Node 03 Vault. It enforces the GPU-First, compute-centric Fetching Protocol.
metadata: { "openclaw": { "requires": { "bins": ["python3"] } } }
---

# 🔄 GPU-First Data Synchronization

This skill enforces the "Data follows Compute" (数据跟计算跑) hardware law established in `07_HARDWARE_NETWORK_LAW.md`.

## 🧠 Agent-Driven Cascading Workflow (Brain + Script)

This skill completely abandons monolithic Python orchestration scripts. **YOU (the Agent) are the Brain.** You must execute the following strict sequence using `ssh_tool.py` (the muscle):

1.  **Symlink-First Verification (GPU Vault Check)**:
    Before pulling anything from the WAN, you MUST use `ssh_tool.py` to check the GPU Server's centralized asset library (`/jhdx0003008/data`, `/models`, or `/packages`). If the asset exists, use `ssh_tool.py` to create a fast `ln -s` symlink to the project's `data/raw/` folder, achieving a 0-second download.
2.  **Node 01 Immunity**:
    Ensure a `.gitignore` exists in the local project's data directory to prevent Git bloat.
3.  **The GPU Native Fetch (Direct Attempt)**:
    Dispatch an asynchronous `nohup curl -L -O` command directly to the target GPU node via `ssh_tool.py` to target the `projects_core/xxx/data/raw/` directory.
4.  **Cascading Pivot to Node 05 (The GFW Bypass)**:
    If the direct GPU fetch fails (e.g., Connection Refused, Timeout due to GFW), **YOU MUST CONSCIOUSLY PIVOT**.
    -   Command Node 05 (the US proxy bridge) via `ssh_tool.py` to download the asset to its `/tmp/` directory.
    -   Once successful, use `ssh_tool.py download` to pull the asset from Node 05, and immediately use `ssh_tool.py upload` to securely transport it into the GPU's central vault (`/jhdx0003008/data/`), acting as a compliant routing buffer.
    -   Clean up the `/tmp/` payload on Node 05.
5.  **Vault Replication**:
    Once the heavy asset is safely inside the GPU central vault, repeat the standard transfer: use `ssh_tool.py download` from the GPU and `upload` to Node 03 (The Vault) for permanent disaster recovery.

## Tools

### `ssh_tool.py`

**This is your primary weapon for this skill.** Use it to orchestrate the logic outlined above. DO NOT rely on the deprecated, hardcoded `gpu_downloader.py` monolithic script.

**Usage Examples**:

*   **Checking Vault**: `ssh_tool.py --host 10.190.30.220 --user root --port 22 exec "ls /jhdx0003008/data/my_asset.h5"`
*   **Direct Fetch**: `ssh_tool.py --host 10.190.30.220 --user root --port 22 exec "cd /root/research_bot/... && nohup curl -L -O https://... > download.log 2>&1 &"`
*   **Pivoting to Node 05**: `ssh_tool.py --host node05 --user [user] exec "curl -L -o /tmp/asset.h5 https://..."`
*   **Pulling to GPU**: `ssh_tool.py download --host node05 /tmp/asset.h5 ./asset.h5` THEN `ssh_tool.py upload --host 10.190.30.220 ./asset.h5 /jhdx0003008/data/`

## Anti-Pattern Detection
Do not attempt to run the legacy `gpu_downloader.py`. The "Brain" (You) must orchestrate the cascade to ensure resilience and adaptability against network failures.
