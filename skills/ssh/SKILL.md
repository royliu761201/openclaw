---
name: ssh
emoji: 🖥️
description: Execute commands and transfer files on remote servers via SSH.
metadata: { "openclaw": { "requires": { "bins": ["python3"] } } }
---

# SSH Skill

Execute commands and transfer files on remote servers via SSH (Paramiko).

## Requirements

To use this skill, you must set the following variables in your `.env` file:

```bash
SSH_HOST=ip_or_hostname
SSH_USER=username
SSH_KEY=/path/to/private_key  # Optional (Recommended)
SSH_PASS=password             # Optional (Fallback)
SSH_PORT=22                   # Optional (Default: 22)
```

> [!WARNING]
> **Anti-Hallucination Law (Paramiko Limitations)**
>
> 1. `ssh_tool.py` is built on `paramiko` and **DOES NOT READ `~/.ssh/config` dynamically**.
> 2. You **CANNOT** use human aliases like `roy-02`. You **MUST** query `tailscale ip -4` and use absolute Tailscale IPs (e.g., `100.90.140.62`).
> 3. The local `.env` file often pollutes `SSH_PORT` (e.g., to GPU server 30305). You **MUST** explicitly override `--env SSH_PORT=22` inline to bypass this pollution.
> 4. **SSH Key Mesh Baseline**: If `ssh_tool.py` hangs or fails with a seemingly unrelated exception, the root cause is frequently a missing `~/.ssh/authorized_keys` entry on the target or a missing local `~/.ssh/id_ed25519` keypair. You **MUST** preemptively verify their mutual SSH trust base before debugging Python.
> 5. **Air-gapped Island Law**: Nodes like `02` and `03` are **Air-gapped / Internal Only**. DO NOT use `ssh_exec` to blindly run public network fetching commands (e.g. `pip install`, `kaggle download`), as they will hang permanently payload drop. You MUST use Node 01, 05 or a Gateway to fetch, then `ssh_upload` them back to the island's isolated Sandbox (e.g. `~/openclaw/venv_cli`).
> 6. **Tailscale PMTUD Blackhole Law (Large Asset Downgrade)**: When pushing large assets (>50MB) across Tailscale nodes (100.x.x.x), standard `ssh_upload` (scp/paramiko) WILL face silent connection drops (`stalled`) due to Path MTU Discovery blackholes (MTU 1280 vs 1500). **YOU MUST ABANDON `ssh_upload`** for these payloads and instead use native `rsync -avz --progress` to forcibly stream and handle disconnects.
> 7. **Cross-Node Execution Proxy Ban (AB-036)**: When requested to run experiments or tail logs on target nodes, you MUST strictly use `ssh_tool.py exec`. ABSOLUTELY DO NOT fake or touch mock logs on the local host to simulate a successful remote execution.
>    **Explicit Invocation Master Strategy:**
>    `SSH_HOST=100.90.140.62 SSH_USER=roy-002 SSH_PORT=22 python3 ssh_tool.py exec ...`

## Tools

### `ssh_exec`

Execute a command on a remote server.

- **command** (string, required): Command to run (e.g., "nvidia-smi").
- **host** (string, optional): Override default host.
- **user** (string, optional): Override default user.
- **detach** (flag, optional): Run in background (nohup). Returns PID immediately.

**Usage**:

```bash
# Sync Execution (Wait for output)
./scripts/ssh_tool.py exec "nvidia-smi"

# Async Execution (Detached)
./scripts/ssh_tool.py exec "python train.py" --detach
```

### 📤 `ssh_upload`

Upload a file to the remote server.

- **local** (string, required): Local path.
- **remote** (string, required): Remote path.
- **resume** (flag, optional): Skip if remote file exists and size matches.

**Usage**:

```bash
./scripts/ssh_tool.py upload "workspace/script.py" "/home/user/script.py"
```

### 📝 `ssh_write`

Write content directly to a remote file.

- **remote** (string, required): Remote path.
- **content** (string, required): Content to write.

**Usage**:

```bash
./scripts/ssh_tool.py write "/tmp/hello.txt" "Hello World"
```

### 📥 `ssh_download`

Download a file from the remote server.

- **remote** (string, required): Remote path.
- **local** (string, required): Local path.

**Usage**:

```bash
./scripts/ssh_tool.py download "/home/user/output.log" "workspace/output.log"
```

### 🐍 `ssh_conda`

Manage remote Conda environments.

- **subcommand** (string): `create`, `clone`, `delete`, `install`, `update`, `list`, or `install-manager`.
- **name** (string): Environment name.
- **packages** (list, optional): Packages to install/create with (use `--packages pkg1 pkg2`).
- **detach** (flag, optional): Run in background (useful for long installs).
- **clone_from** (string, optional): Source environment (clone).

**Usage**:

```bash
# Auto-Install Miniconda (if missing)
./scripts/ssh_tool.py conda install-manager

# Create (Offline/Background)
./scripts/ssh_tool.py conda create -n my_env --packages python=3.9 numpy --detach

# Install (Long Running)
./scripts/ssh_tool.py conda install -n my_env --packages torch --detach

# Clone
./scripts/ssh_tool.py conda clone -n new_env --clone-from old_env

# Execute in Env (Background)
./scripts/ssh_tool.py exec "python train.py" --conda_env my_env --detach
```
