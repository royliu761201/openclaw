---
name: intel-fetch
description: Advanced data reconnaissance and retrieval macro-skill. Replaces legacy downloaders. Enforces the Data Follows Compute protocol and handles proxy bouncing.
---

# Intel Fetch

> **Core Mission**:
> Unified retrieval of all external data, model weights, and heavy assets. Replaces legacy `gpu-downloader` and ad-hoc crawlers.

## T-1: Symlink-First Protocol

Before downloading any GB-scale asset, the Agent **MUST first check** the target machine's cold storage vault:

- GPU: `/jhdx0003008/data/`, `/models/`, `/packages/`
- Node 03: `~/openclaw_data/wheels_vault/`

**If asset exists, download is STRICTLY PROHIBITED!** Symlink (`ln -s`) for zero-second loading.

---

## T0: Mandatory Pre-flight (ATM22 Campaign Hardening)

> [!CAUTION]
> This tier was MISSING during ATM22, causing 12 failures and 40 hours waste. Violators will repeat history.

Before T1/T2/T3, you **MUST** complete these 3 checks on the target node:

### 0.1 Network Reachability Probe

```bash
ssh_tool.py exec "curl -sI --connect-timeout 5 <DATA_SOURCE_URL> | head -3"
```

If empty or timeout, **immediately abandon direct fetch**, jump to T2.

### 0.2 SSH Chain Verification (cross-node transfers)

```bash
ssh Node05 "ssh -o ConnectTimeout=5 Node06 echo hop1_ok"
ssh Node05 "ssh -J Node06 -p 30305 GPU echo hop2_ok"
```

### 0.3 Disk Space + Credential Confirmation

```bash
ssh_tool.py exec "df -h /target/dir && whoami"
# HuggingFace: python3 -c "from huggingface_hub import HfApi; print(HfApi(token='...').whoami()['name'])"
# Kaggle: kaggle datasets list -s dummy
```

---

## T1: Direct Node Fetch

1. SSH into target execution node (e.g., Node 02 or GPU).
2. In cold storage (`~/data_vault/` or `/tmp/`), issue direct download:
   - **Kaggle**: `kaggle datasets download` or `curl` + Kaggle API
   - **HuggingFace**: `huggingface-cli download <model>`
   - **Generic**: `wget -c`, `curl -L -O`

   > **[GPU Network Profile - 2026-03-21 Verified]**
   >
   > | Status        | Sites                                                                                               |
   > | ------------- | --------------------------------------------------------------------------------------------------- |
   > | Direct        | AWS S3, NCBI GEO, CZ CELLxGENE, OpenNeuro, Kaggle, Tsinghua/SJTU mirrors                            |
   > | Blocked       | HuggingFace, GitHub, PyPI                                                                           |
   > | DNS Blackhole | `zenodo.org` (hosts to 127.0.0.1), `hf-mirror.com` (DNS unreachable), `huggingface.co` (curl empty) |
   >
   > **Trap**: Dead proxies in `.profile`/`.bashrc` (e.g., `socks5h://127.0.0.1:7890`) silently blackhole ALL HTTP.
   > **Preflight**: `grep -i proxy ~/.profile ~/.bashrc /etc/environment 2>/dev/null`

   > **[Long Task SOP: tmux > nohup]**
   > `ssh_tool.py exec --detach` + `nohup` verified unreliable.
   > **Long tasks MUST use `tmux`**:
   >
   > ```bash
   > tmux kill-session -t <name> 2>/dev/null
   > tmux new-session -d -s <name> 'wget -c -O <out> <url> 2>&1 | tee <log>; echo DONE; bash'
   > tmux ls
   > ```

## T2: Node 05 Proxy Bypass

When the target node is air-gapped:

1. **Node 05 Gateway**: Command Node 05 (overseas exit node) as download proxy.
2. **Kaggle Zipped Pipeline**:
   - Run `kaggle datasets download -d <dataset> --force` on Node 05.
   - **NEVER `--unzip`!** Keep compressed through entire chain.
3. **End-to-End Transport (Rsync + Jump Host)**:
   - Push from Node 05 directly to GPU. **Node 05 MUST jump through Node 06** (`-J roy-006@100.66.251.115`).
   - **scp PROHIBITED for >1GB**. Use `rsync --partial --progress -e "ssh -J roy-006@100.66.251.115 -p 30305"`.
   - Decompress only at **final destination**.

## T2.5: Kaggle to HuggingFace Relay (ATM22 Battle-Proven)

> [!IMPORTANT]
> Use when data source is blocked by BOTH GPU network AND Kaggle exit IP. Verified 2026-03-21.

**Scenario**: Data source hit by GPU DNS blackhole + Kaggle IP banned by anti-bot.

**Chain**:

```
Data Source --(Kaggle All-in-One Kernel)--> HuggingFace --(Node 05)--> rsync -J --> GPU
```

**Rules**:

1. **All-in-one Kernel**: Download + HF upload in SINGLE script. Kernel-to-Kernel output mounting fails for large files.
2. **Chunked download**: HTTP Range split into <16GB chunks (Kaggle disk limit 20GB).
3. **HF is transit only**: Delete HF repo after data lands on GPU.
4. **GPU cannot pull from HF**: Both `huggingface.co` and `hf-mirror.com` unreachable from GPU. Must relay via Node 05.

## T3: Post-Landing Cleanup (MANDATORY)

> [!CAUTION]
> Data arriving at GPU does NOT end the mission. **All transit caches MUST be purged** before marking transfer complete. Failure to clean = data leakage + disk waste across the cluster.

After assets land on GPU and pass `h5py`/integrity verification:

### Cleanup Checklist

| #   | Target                  | What to Purge                                     | Command                                                          |
| --- | ----------------------- | ------------------------------------------------- | ---------------------------------------------------------------- |
| 1   | **Node 05** (`C:\tmp\`) | Downloaded files + extracted dirs                 | `ssh roy-05 "del C:\tmp\<file> && rmdir /s /q C:\tmp\<dir>"`     |
| 2   | **HuggingFace**         | Transit repo (if created for relay)               | `huggingface-cli repo delete <repo> --yes`                       |
| 3   | **Kaggle**              | Kernel output, dataset staging                    | Delete kernel + output via Kaggle web or `kaggle kernels delete` |
| 4   | **GPU `.cache/`**       | HF hub cache from failed direct attempts          | `rm -rf /jhdx0003008/data/pesso/<project>/.cache`                |
| 5   | **Local Mac `/tmp/`**   | Any partial scp / relay files                     | `rm -f /tmp/<file>`                                              |
| 6   | **Node 03 vault**       | Replicate FIRST, then mark transit copy for purge | `rsync` to `~/data_vault/`, purge source after                   |

### Rules

1. **Clean in reverse order** — furthest relay node first (Node 05), then intermediate (HF/Kaggle), then local.
2. **Verify before delete** — Always `ls`/`dir` the target to confirm it's the correct transit file, NOT the final copy.
3. **Never delete the GPU final copy** — The Anti-Destruction Anchor (L0) applies.
4. If vault replication (Node 03) is required, replicate BEFORE purging any transit cache.

---

## L1 Compliance

1. Data directories from `intel-fetch` MUST be in `.gitignore`.
2. Complex crawlers MUST include sandbox lock (`in_venv = sys.prefix != sys.base_prefix`).

## Trigger Rule

Infinite priority. Triggered by ANY instruction involving heavy external assets (>100MB). **Agent MUST take over routing. No blind wget.**

---

## Execution Examples

```bash
# === Pull HF BERT to air-gapped Node 02 vault ===

# 1: Check vault (dedup)
ssh_tool.py --host 03 exec "ls ~/data_vault/models/bert-base-uncased"

# 2: Node 05 external fetch
ssh_tool.py --host node05 exec "huggingface-cli download bert-base-uncased --local-dir /tmp/bert-base"

# 3: Rsync into vault (MUST use rsync!)
rsync -avz --progress -e "ssh -o StrictHostKeyChecking=no" \
  ./bert-tmp roy-002@100.90.140.62:/data_vault/models/bert-base

# 4: Purge transit cache
ssh_tool.py --host node05 exec "rm -rf /tmp/bert-base"

# 5: Symlink into project
ln -s /data_vault/models/bert-base ./model_weights
```

```bash
# === [BATTLE-TESTED 2026-03-22] HF Dataset → GPU via Node 05 → Node 06 Jump ===
# Route: Node 05 (Canada, curl) → Node 06 (JumpHost) → GPU (10.190.30.220)
# Used for: Poseidon NS-PwC (4.86GB), verified integrity on GPU.

# --- ONE-TIME SETUP: Provision SSH keys on Node 05 (Windows, no pre-existing SSH) ---
# Copy BOTH private + public key to Node 05:
scp -o StrictHostKeyChecking=no ~/.ssh/id_ed25519 roy-05:"C:\Users\roy-005\.ssh\id_ed25519"
scp -o StrictHostKeyChecking=no ~/.ssh/id_ed25519.pub roy-05:"C:\Users\roy-005\.ssh\id_ed25519.pub"

# Verify 05→06→GPU chain:
ssh roy-05 "ssh -o StrictHostKeyChecking=no -i C:\Users\roy-005\.ssh\id_ed25519 \
  -J roy-006@100.66.251.115 -p 30305 root@10.190.30.220 \"echo GPU_REACHED\""

# --- DOWNLOAD + DIRECT TRANSFER ---
# Step 1: Node 05 downloads from HF (curl, no Python needed)
ssh roy-05 "curl -L -o C:\tmp\data.nc https://huggingface.co/datasets/<repo>/resolve/main/<file>"

# Step 2: Node 05 SCP directly to GPU via Node 06 jump (-J flag, NOT ProxyCommand)
# IMPORTANT: Windows scp.exe does NOT support %h:%p in ProxyCommand. MUST use -J flag.
ssh roy-05 "scp -o StrictHostKeyChecking=no \
  -i C:\Users\roy-005\.ssh\id_ed25519 \
  -J roy-006@100.66.251.115 \
  -P 30305 \
  C:\tmp\data.nc \
  root@10.190.30.220:/jhdx0003008/data/target_dir/"

# Step 3: GPU-side verification
ssh gpu "python3 -c 'import h5py; f=h5py.File(\"/path/to/data.nc\",\"r\"); print(f[\"velocity\"].shape)'"

# Step 4: Purge Node 05 transit cache
ssh roy-05 "del C:\tmp\data.nc"
```
