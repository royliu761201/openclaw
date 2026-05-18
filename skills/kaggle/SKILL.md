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

1. **Environment Variables** (Recommended):
   Export the following in the shell or runner that invokes the tool. If you keep them in a project `.env`, you must source that file explicitly before running the command; `kaggle_tool.py` no longer auto-loads `.env`.

   ```bash
   KAGGLE_USERNAME=your_username
   KAGGLE_KEY=your_key
   ```

2. **Kaggle CLI Config**:
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

### `kaggle_kernel_push` (Safeguarded)

Push (deploy) a kernel to Kaggle. **RAW PUSHING VIA CLI IS NOW FORBIDDEN.** You must use the python controller to prevent Dual-Account hallucination and CPU/GPU accelerator misallocation.

- **path** (string, required): Local folder containing `kernel-metadata.json` and script file.
- **account** (string, required): The target account credentials to use (e.g. `roylxh5147` or `account_B`). Prevents quota leakage.
- **hardware** (string, required): Explicit accelerator declaration (`5CPU` or `2P100`).

**Usage (The Kaggle Controller)**:

```bash
# To push a heavy PyTorch script to the 2x P100 Dual GPU under account A:
python3 /Users/roy-jd/workspace/.local_skills/kaggle/scripts/kaggle_controller.py push "workspace/my_kernel" --account roylxh5147 --hardware 2P100

# To push a lightweight scraping/EDA script to the 5x CPU under account B:
python3 /Users/roy-jd/workspace/.local_skills/kaggle/scripts/kaggle_controller.py push "workspace/my_eda" --account account_B --hardware 5CPU
```

The controller will auto-inject the correct `"accelerator"` metadata and ensure the specific `KAGGLE_CONFIG_DIR` is loaded before touching the cloud.

### `kaggle_kernels_list`

List kernels to check status.

- **user** (string, optional): Filter by user. If omitted, lists **your** kernels.
- **search** (string, optional): Filter by title text.

**Usage**:

```bash
./scripts/kaggle_tool.py kernels_list --user "username" --search "openclaw"
```

### `dispatch_kaggle_downloader` (Kaggle Downloader Proxy)

🔥 **High-Speed Network Bridge**🔥
Use this script when you need to download massive datasets (e.g. `pip install mantra-dataset` or `wget`) but local Mac proxy routes are broken or bandwidth is constrained. It automatically builds a python payload, pushes it as a Kaggle Kernel, runs it on Kaggle's gigabit network, zips the output, and gives you the exact SSH command to fetch it onto the `10.190` GPU Server.

- **username** (string): The Kaggle account username.
- **slug_name** (string): Unique identifier for the Kaggle Kernel.
- **pip_package_or_url** (string): The package name to `pip install` or direct `http` url to `wget`.
- **gpu_target_dir** (string, optional): The destination directory on the 10.190 GPU Server.

**Usage**:

```bash
./scripts/dispatch_kaggle_downloader.sh roylxh5147 mantra-downloader mantra-dataset /jhdx0003008/data/mantra
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

## Battle-Tested Dataset Deploy Path (经实战验证的最优路径)

> [!IMPORTANT]
> This 3-step procedure was distilled from **two major incident postmortems** (2026-03-12 identity/proxy crisis, 2026-03-18 silent-failure crisis) and the historical success of deploying the 409MB `medtime-gvp-cn-checkpoint` dataset. **Any agent deploying a dataset MUST follow this path.**

### Step 1: Prepare flat files + metadata

```bash
# Put all data files FLAT in one directory (no subdirectories!)
mkdir -p /tmp/my_dataset
cp *.pt /tmp/my_dataset/

# Create dataset-metadata.json
cat > /tmp/my_dataset/dataset-metadata.json << 'EOF'
{
  "title": "my-dataset-name",
  "id": "OWNER_USERNAME/my-dataset-name",
  "licenses": [{"name": "CC0-1.0"}]
}
EOF
```

### Step 2: Push via Python API (NOT CLI)

```python
import os
os.environ['KAGGLE_USERNAME'] = 'OWNER_USERNAME'
os.environ['KAGGLE_KEY'] = 'YOUR_KEY'
from kaggle.api.kaggle_api_extended import KaggleApi
api = KaggleApi()
api.authenticate()

# For new dataset:
result = api.dataset_create_new('/tmp/my_dataset', quiet=False, convert_to_csv=False)
# For version update:
# result = api.dataset_create_version('/tmp/my_dataset', 'v2', quiet=False, convert_to_csv=False)
print(f'Result: {result}')  # MUST check status == "Ok"
```

### Step 3: First kernel push MUST include mount-path probe

```python
# Paste this at the TOP of kernel_main.py for the FIRST run only
import os, sys, glob
print("[PROBE] Scanning /kaggle/input/")
for root, dirs, files in os.walk("/kaggle/input"):
    depth = root.replace("/kaggle/input", '').count(os.sep)
    print('  ' * depth + os.path.basename(root) + '/')
    for f in files[:5]:
        print('  ' * (depth+1) + f'{f} ({os.path.getsize(os.path.join(root,f))} B)')
    if depth > 3: break
sys.exit(0)  # Stop here — read logs, confirm path, then remove probe
```

After confirming the mount path from logs, use this **safe auto-detect pattern** in production:

```python
import glob, os
hits = glob.glob("/kaggle/input/**/<known_filename>", recursive=True)
DATA_ROOT = os.path.dirname(hits[0]) if hits else "/kaggle/input"
```

### Heavy Dataset Fetching (>10GB)

> [!CAUTION]
> The Kaggle Python CLI `kaggle datasets download --unzip` loads the entire central directory into RAM before writing. On massive datasets like ImageCAS (83GB), this consumes **>35GB VmRSS** and causes an OOM kill on the GPU server.

For massive datasets, completely bypass the CLI and use pure HTTP streaming via robust base tools:

```bash
# Automated Recovery (Recommended for GPU Server)
python3 /Users/roy-jd/openclaw/skills/kaggle/scripts/gpu_safe_download.py OWNER/DATASET_NAME -o /jhdx0003008/data/target_dir

# Manual Handshake (If automation fails)
# Extract your true auth token for curl
AUTH=$(echo -n "KAGGLE_USERNAME:KAGGLE_KEY" | base64)

# Stream direct to disk via curl (Memory footprint ~13MB).
# Note: The GPU Pod DNS cannot resolve www.kaggle.com directly, MUST use --resolve
curl -L --resolve www.kaggle.com:443:35.244.233.98 \
     -H "Authorization: Basic $AUTH" \
     -C - -o dataset.zip \
     "https://www.kaggle.com/api/v1/datasets/download/OWNER/DATASET_NAME"
```

### 🇦🇺 Internal Mirror Protocol (Sydney Physics Cluster)

> [!IMPORTANT]
> **GPU Node Isolation**: The Sydney `gpu` node (Node 220) cannot resolve `www.kaggle.com` directly. It MUST use the internal mirror gateway (Node 90-1).

**Step 1: Infrastructure Mapping**
If `ping kaggle-mirror.physics` fails, inject the following into `/etc/hosts` (requires sudo or coordination with Node 90-1):
```bash
10.190.35.201 kaggle-mirror.physics
```

**Step 2: Environment Injection**
Force the Kaggle CLI to route all API calls through the internal physics mirror:
```bash
export KAGGLE_API_ENDPOINT="https://kaggle-mirror.physics"
export KAGGLE_CONFIG_DIR="/path/to/your/project/.kaggle"
```

**Step 3: Protocol Verification**
Perform a zero-trust handshake before launching heavy downloads:
```bash
curl -k -I https://kaggle-mirror.physics
```

### Known Traps (from historical postmortems)

| #   | Trap                                                                                                                                                                                                                              | Killed     | Fix                                                                                                                                                                                                    |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1   | **Identity Hallucination** — guessing username from key name (`KAGGLE_ROYLXH_KEY` ≠ `roylxh`; real name is `roylxh5147`)                                                                                                          | 2026-03-12 | Always verify via `kaggle config view` or `~/.kaggle/kaggle.json`                                                                                                                                      |
| 2   | **`.env` Proxy Backstab** — `load_dotenv()` in `kaggle_tool.py` greedy-loads rogue `.env` with `HTTP_PROXY=127.0.0.1:7890`                                                                                                        | 2026-03-12 | Removed `load_dotenv()`; use only `KAGGLE_USERNAME` / `KAGGLE_KEY` env vars                                                                                                                            |
| 3   | **CLI Silent Failure** — `kaggle datasets create` returns exit 0 but creates nothing (v1.7.x bug)                                                                                                                                 | 2026-03-18 | Use Python API `api.dataset_create_new()` directly; `kaggle_tool.py` now auto-verifies                                                                                                                 |
| 4   | **Mount Path Prefix** — new API mounts at `/kaggle/input/datasets/{owner}/{slug}/` not `/kaggle/input/{slug}/`                                                                                                                    | 2026-03-18 | Always probe first; use `glob.glob` auto-detect                                                                                                                                                        |
| 5   | **numpy/Tensor mismatch** — `.pt` saved with numpy arrays crash `.numpy()` calls                                                                                                                                                  | 2026-03-18 | Use `_np = lambda x: x.numpy() if hasattr(x, 'numpy') else np.asarray(x)`                                                                                                                              |
| 6   | **Kernel ≠ Dataset owner** — cross-account private dataset mount fails silently (empty dir)                                                                                                                                       | 2026-03-18 | Keep kernel & dataset under same account, or make dataset public                                                                                                                                       |
| 7   | **CLI RAM Explosion** — `--unzip` on massive datasets buffers in RAM (>35GB usage) causing OOM                                                                                                                                    | 2026-03-16 | Never use `--unzip` for >10GB. Use `curl` raw HTTP streaming instead.                                                                                                                                  |
| 8   | **GPU DNS Quirk** — `wget`/`curl` fails with `[Errno -3] Temporary failure in name resolution`                                                                                                                                    | 2026-03-16 | GPU pod dns is custom; Hardcode CDN IP with `curl --resolve www.kaggle.com:443:35.244.233.98`                                                                                                          |
| 9   | **SSH Pipeline Deadlock** — `bash -c "nohup unzip && cp &"` over SSH dies silently on close                                                                                                                                       | 2026-03-16 | Base64 your script, decode remotely, `chmod +x`, then `nohup script.sh`                                                                                                                                |
| 10  | **Russian Doll Split Zips** — Kaggle authors upload multi-part split zips (`.change2zip`, `.z01`)                                                                                                                                 | 2026-03-16 | Reassemble via `zip -q -F "prefix.zip" --out "prefix_full.zip"` then unzip                                                                                                                             |
| 11  | **PyArrow / API OOM Explosion** — APIs like `cellxgene_census` buffer huge uncompressed arrays in RAM causing 30GB+ explosion even with chunking                                                                                  | 2026-03-20 | Completely bypass standard Python APIs. Probe metadata API for exact dataset ID, then execute physical HTTP direct download (e.g., `wget https://datasets.cellxgene.cziscience.com/{ID}.h5ad`).        |
| 12  | **Script Mode Phantom Files** — `kernel_type: "script"` only deploys the single `code_file`. Companion `.py` files in the same folder are silently ignored and will produce `FileNotFoundError` at runtime.                       | 2026-03-20 | Base64-encode companion scripts and self-extract them at runtime inside the entry point. Or use `dataset_sources` to mount them.                                                                       |
| 13  | **Disk Overflow on Data Generation** — Kaggle free tier has **20GB disk limit**. Data generation kernels that produce large HDF5/tar outputs will silently die with "disk space exceeded" if you don't pre-calculate output size. | 2026-03-21 | **Always do capacity math before pushing**: `n_samples × n_configs × per_sample_MB < 20GB`. Include tar overhead (~1.5x). Reduce `--n_samples` for Kaggle runs.                                        |
| 14  | **Skipping SKILL.md** — Agent wrote custom Kaggle code without reading this SKILL.md first, causing a cascade of 5 avoidable errors (CLI not found → 401 → FileNotFoundError → disk overflow) over 12 hours.                      | 2026-03-21 | **This SKILL.md exists for a reason.** Read it BEFORE writing any Kaggle automation code. Every trap above was discovered the hard way.                                                                |
| 15  | **GPU Metadata Lock (P100 Trap)** — Attempting to set `"accelerator": "GPU_T4"` in `kernel-metadata.json` for script deployments is ignored. Kaggle scripts ONLY accept `"accelerator": "GPU"` which strictly forces legacy P100. | 2026-03-27 | See [AB-KAG-07v2] below. Use `torch 2.7.1+cu126` wheel + `torchvision` from cu126 index + `os.execvpe()` process restart. The old `torch==2.3.1+cu118` protocol is **dead** as of 2026-04 Kaggle images. |
| 16  | **Torch/Torchvision Version Mismatch** — Installing only torch from cu126 but leaving system torchvision (0.25+cu128) causes `RuntimeError: operator torchvision::nms does not exist` due to ABI incompatibility. | 2026-04-05 | Always co-install `torchvision` alongside `torch` from the **same cu126 index**. Never install torch alone. |
| 17  | **Module Cache Poisoning** — `pip install torch==X` in the same Python process that already imported torch doesn't replace the in-memory module. `load_state_dict` then crashes with `ModuleNotFoundError: torch.utils.serialization`. | 2026-04-05 | Use `os.execvpe()` to fully restart the script after pip install, with an env-var guard (`MY_TORCH_COMPAT_READY=1`) to prevent infinite re-exec loops. |

### 🛡️ Kernel Push Pre-Flight Checklist (MANDATORY)

> [!IMPORTANT]
> **Every `kernel_push` call MUST pass this checklist.** This was established after a 5-failure, 12-hour incident on 2026-03-20/21.

- [ ] **Read this SKILL.md?** Especially Known Traps table above.
- [ ] **Using verified account?** `roylxh5147` + `KAGGLE_ROYLXH_KEY`. Unverified accounts get 401.
- [ ] **`title` == slug?** In `kernel-metadata.json`, set `"title": "<slug>"` to prevent 409 Conflict.
- [ ] **`code_file` is self-contained?** All dependencies either inlined (base64) or mounted via `dataset_sources`.
- [ ] **Disk math done?** Total output (data + tar) < 20GB. Show your calculation in a comment.
- [ ] **GPU memory safe?** Peak VRAM < 16GB (P100). Run tasks serially if needed.
- [ ] **Probe first?** For new kernel structures, push a probe-only version (print env, disk, paths) before the real job.

### Execution Failed?

If a kernel execution fails:

1. **Check Status**: Use `kernels_list` to see if it's "error" or "running".
2. **Get Logs**: Use `kernels_output` to download the log files (`.log`).
3. **Auth Errors (403)**: Ensure the current shell environment or `~/.kaggle/kaggle.json` has valid `KAGGLE_USERNAME` and `KAGGLE_KEY`.
4. **Auth Errors (401 Unauthorized during Kernel Push)**: The Notebook API requires the destination Kaggle account to be **Phone Verified**. Even if the API key can download datasets, it will return 401 on `kernel_push` if unverified. **Resolution**: Switch to a verified backup account key (e.g., `KAGGLE_ROYLXH_KEY`) using official dispatch scripts.
5. **Conflict (409 Conflict during Kernel Push)**: The `title` field in `kernel-metadata.json` MUST mathematically map to the kernel slug in the `id` field. Do NOT use human-readable titles that differ from the slug, or Kaggle will instantly reject the push with a 409 URL Conflict. **Resolution**: Set `"title": "$SLUG"`.

### Dataset Push Silent Failure (CRITICAL)

> [!CAUTION]
> **`kaggle` CLI v1.7.x `dataset create` returns exit code 0 but does NOTHING.** Do NOT trust a clean exit as proof of success. The tool's `dataset_push` command now auto-verifies via API after every push. If you see `[VERIFY] ⚠️ Dataset NOT found`, the push silently failed.

**Root cause**: The Python 3.9-compatible kaggle package (v1.7.4.5) has an internal exception in `upload_files()` that is caught and swallowed silently. Upgrading requires Python ≥ 3.11.

### Kernel FileNotFoundError — Mount Path Rules

> [!WARNING]
> Kaggle mount paths differ depending on HOW the dataset was created. **Always probe first.**

| Creation Method                       | Mount Path                               |
| ------------------------------------- | ---------------------------------------- |
| Legacy CLI / Web UI                   | `/kaggle/input/{slug}/`                  |
| Python API (`api.dataset_create_new`) | `/kaggle/input/datasets/{owner}/{slug}/` |

**Probe-First Principle**: If `FileNotFoundError` occurs on the first run, your **next push MUST include this probe** before any model code:

```python
import os, sys
print("[PROBE] Scanning /kaggle/input/")
for root, dirs, files in os.walk("/kaggle/input"):
    depth = root.replace("/kaggle/input", '').count(os.sep)
    print('  ' * depth + os.path.basename(root) + '/')
    for f in files[:5]:
        print('  ' * (depth+1) + f'{f} ({os.path.getsize(os.path.join(root,f))} B)')
    if depth > 3: break
print("[PROBE] Done.")
sys.exit(0)
```

After confirming the real path from the probe log, use this safe pattern in your kernel:

```python
import glob, os
hits = glob.glob("/kaggle/input/**/burgers_train.pt", recursive=True)
DATA_ROOT = os.path.dirname(hits[0]) if hits else "/kaggle/input"
```

### Data Format Mismatch (numpy vs torch)

`.pt` files saved with `torch.save({"u": numpy_array})` will deserialize as numpy, not Tensor. Always use:

```python
_np = lambda x: x.numpy() if hasattr(x, 'numpy') else np.asarray(x)
```

### Read-Only `/kaggle/input/` Mount (2026-03-26 实战验证)

Kaggle mounts datasets at `/kaggle/input/` as **completely read-only**. Any attempt to write files (checkpoints, W&B cache, `os.makedirs()`) under this path will crash with `OSError: [Errno 30] Read-only file system`. This is **not documented prominently** in official Kaggle docs.

**Mandatory fix**: All kernel bootstrapper scripts must include at the very top:

```python
import os
os.chdir('/kaggle/working')  # The ONLY writable directory
```

### Credential Pre-Flight Gate (2026-03-26 血的教训)

Before any `kaggle datasets create` or `kaggle kernels push`, **MUST validate credentials** via a whoami handshake:

```bash
export KAGGLE_USERNAME="TARGET_USER" KAGGLE_KEY="TARGET_KEY"
kaggle datasets list --user TARGET_USER  # Exit 0 = valid
```

If 401 → **ABORT immediately**. Do not proceed to push.

**SSoT**: The only authoritative source for Kaggle API tokens is `Kaggle Web > Settings > API > Create New Token`. Local files (`kaggle.json`, env vars) are **caches only** and must be periodically synced.

- **`[AB-KAG-06] Fail-Fast Smoke Test Before Full Sweep`**: 向 Kaggle 发射大规模矩阵实验前，**必须先用最小单元任务（1 个 task, 1 轮 epoch）做 Smoke Test 探针**。只有探针返回 `KernelWorkerStatus.COMPLETE` 后，才允许发射全量 Sweep。禁止未经探针直接全量盲推！(2026-03-26 SynergyFL 实战验证)
- **`[AB-KAG-07v2] Kaggle Script GPU Lock (P100 sm_60 架构陷阱) — 2026-04-05 实战更新`**: 在通过 API 发送 `kernel_type: "script"` 的后台任务时，`kernel-metadata.json` 中的 `accelerator` 字段**无法强制指定 `"GPU_T4"`**。系统只能接受 `"accelerator": "GPU"`，且云端**默认全部强制分配古老的 P100 (Pascal, sm_60) 架构**。

  > **严重后果**: Kaggle 官方新版容器搭载 Python 3.12 和 PyTorch >= 2.10+cu128。PyTorch 从 2.4 版本开始，默认的 CUDA 12.8 构建包**彻底移除了对 P100 (sm_60) 的 SASS 支持**。硬件交互会导致 `CUDA error: no kernel image is available` 闪退。

  > **⚠️ 旧协议 (cu118 / torch 2.3.1) 已失效！** Kaggle 2026-04 容器 Python 3.12 环境下 `torch 2.3.1+cu118` 的 `torchvision` 加载时会崩溃 (`ModuleNotFoundError: torch.utils.serialization`)。必须使用下面的 v2 协议。

  **[AB-KAG-07v2] 强制求生法则 (经 PIQ / RiskNO / TopoTME 三项目验证)**:

  核心要点：
  1. **使用 `torch 2.7.1+cu126`** 而非 2.3.1 — 这是目前已知最后一个支持 sm_60 的官方 wheel
  2. **同时安装 torchvision** — 从同一 cu126 索引安装，避免 operator registration 冲突
  3. **`os.execvpe()` 重启** — pip 安装后必须重启进程，否则 Python 模块缓存会加载旧版 torch
  4. **环境变量防重入** — 设置一个标志位避免重启后再次触发安装

  ```python
  # === [AB-KAG-07v2] P100 COMPATIBILITY PROTOCOL ===
  # MUST be at the VERY TOP of your script, BEFORE any `import torch`
  import subprocess, sys, os

  CU126_TORCH_VERSION = "2.7.1+cu126"

  def _resolve_cu126_torch_wheel():
      py_tag = f"cp{sys.version_info.major}{sys.version_info.minor}"
      version_tag = CU126_TORCH_VERSION.replace("+", "%2B")
      return (
          f"https://download.pytorch.org/whl/cu126/"
          f"torch-{version_tag}-{py_tag}-{py_tag}-manylinux_2_28_x86_64.whl"
      )

  def _ensure_compatible_torch():
      if os.environ.get("MY_TORCH_COMPAT_READY", "0") == "1":
          return  # Already re-exec'd

      try:
          import torch
      except ImportError:
          return

      if not torch.cuda.is_available():
          return

      try:
          capability = torch.cuda.get_device_capability(0)
      except Exception:
          return

      if capability >= (7, 0):
          return  # T4/V100/A100 etc. — no fix needed

      # P100 (sm_60) detected. Reinstall torch + torchvision from cu126.
      subprocess.run([
          sys.executable, "-m", "pip", "install", "-q",
          "--upgrade", "--force-reinstall", "--no-cache-dir",
          "--index-url", "https://download.pytorch.org/whl/cu126",
          "--extra-index-url", "https://pypi.org/simple",
          _resolve_cu126_torch_wheel(),
          "torchvision",  # MUST co-install to avoid operator mismatch
      ], check=True)

      # Re-exec script so Python loads the NEW torch cleanly
      reexec_env = os.environ.copy()
      reexec_env["MY_TORCH_COMPAT_READY"] = "1"
      os.execvpe(sys.executable, [sys.executable, __file__, *sys.argv[1:]], reexec_env)

  _ensure_compatible_torch()
  # === END PROTOCOL ===

  import torch  # NOW safe to import
  ```

  **参考实现**:
  - PIQ: `piq_soft_stabilizer_kaggle.py` → `ensure_compatible_torch()`
  - RiskNO: `scripts/ensure_legacy_torch_compat.py` → `build_pip_command()` + `os.execvpe()`
  - TopoTME: `kaggle_pack/kernel_main.py` → `_ensure_compatible_torch()` (V6 成功)


- **`[AB-KAG-08] Kaggle Quota Preservation (Poison Pill Override)`**: The official Kaggle CLI **does not have a `cancel` command** for running kernels. If you need to immediately abort a running kernel to stop it from wasting the 30-hour weekly GPU quota, DO NOT hallucinate a `kaggle kernels cancel` command.
  
  **Strategy**: Push an overriding "Poison Pill". Create an empty script that just calls `sys.exit(0)`, and use `kaggle kernels push` with the **exact same `kernel_slug` and `username`**.
  
  **Mechanism**: Kaggle's backend queue detects the new push, instantly terminates the old running P100 pod, runs the new 1-second empty script, and completes. This guarantees an instant remote kill and frees the GPU quota.

See also: `KAGGLE_COMPUTE_PROFILE.md [AB-KAG-04/05/06/07/08]` and `04_AGENT_ANTIBODIES.md [AB-050]`.
