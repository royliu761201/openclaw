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
>    `SSH_HOST=100.90.140.62 SSH_USER=roy-002 SSH_PORT=22 python3 ssh_tool.py exec ...`
> 8. **The Sudo Over SSH Law**: When requiring root privileges to modify core system settings (e.g., `pmset`, `networksetup`) on remote nodes, NEVER execute raw `sudo` via SSH as it will silently hang awaiting an interactive prompt. You MUST fetch the plaintext password from the Master Secrets Vault (`~/.secrets/secrets_flat.json` or `.openclaw_secrets`) and pipe it via stdin (e.g., `echo 'mypass' | sudo -S <cmd>`).
> 9. **The Dead Proxy Preflight Law**: Before running heavy `wget` or `curl` commands on GPU/academic nodes, you MUST verify `~/.profile` or `~/.bashrc` does not contain dead proxy variables (e.g., `http_proxy=127.0.0.1:7890`) that will silently hang connections.
> 10. **The Tmux Resilience Law**: NEVER use `nohup <cmd> &` over SSH for heavy data pipeline execution. It is inherently unreliable and may drop out when the SSH session formally closes. You MUST use OS-level session persistence via `tmux`: `ssh_tool.py exec "tmux new-session -d -s <task> '<cmd>'"`
> 11. **The Terminal Escaping Hell Law**: NEVER attempt to write multi-line scripts or use `heredoc` (`<<EOF`) inline within an `ssh_exec` call. Shell escaping chains will corrupt your variables (e.g., `$()` evaluated locally instead of remotely). You MUST write the script locally to `/tmp/`, `ssh_upload` it, and then execute it cleanly.
> 12. **The DNS S3 Bypass Law (GFW/Islands)**: When downloading from Academic APIs on GPU isolated networks (e.g., `openneuro-py`, `cellxgene_census`), DNS resolution of API domains will often fail (`[Errno -3] Temporary failure in name resolution`), yet raw S3 fetching remains unobstructed. You MUST bypass the fragile APIs and use native physics (`aws s3 sync s3://...` or `curl -O`) mapping directly to the underlying buckets.
> 13. **The Windows `administrators_authorized_keys` Trap**: Windows OpenSSH for **admin users** ignores `~\.ssh\authorized_keys` and instead reads `C:\ProgramData\ssh\administrators_authorized_keys`. If SSH hangs (key auth silent fail) on a Windows jump host, check `sshd_config` for `AuthorizedKeysFile __PROGRAMDATA__/ssh/administrators_authorized_keys` and add the public key there. This bit us during the ATM22 campaign and cost hours of debugging.
> 14. **The SSH Key Mesh Pre-flight Law**: Before ANY cross-node data transfer, you MUST verify the full SSH chain works with a simple `echo ok` test. For jump chains (e.g., Node 05 → Node 06 → GPU), test EACH hop independently: first `Node05 → Node06`, then `Node05 -J Node06 → GPU`. Never blindly launch a multi-hour SCP/rsync and assume the chain is intact.
> 15. **The rsync-over-scp Law (Large File Mandate)**: For files >1GB, you are **STRICTLY PROHIBITED** from using `scp`. Use `rsync --partial --progress -e "ssh ..."` exclusively. `scp` has zero resume capability — a 14GB transfer that breaks at 12MB must restart from zero. `rsync --partial` automatically resumes from the last successfully transferred byte. This is non-negotiable for all cross-node large file operations.

## Tools

### `ssh_exec`

Execute a command on a remote server.

- **command** (string, required): Command to run (e.g., "nvidia-smi").
- **host** (string, optional): Override default host.
- **user** (string, optional): Override default user.
- **detach** (flag, optional): Run in background using **Linux `setsid()` (true OS-level daemonization)**. Returns PID immediately. Process survives SSH disconnect.

> [!IMPORTANT]
> **Anti-Hallucination Law #9 (Detach Mode)**
>
> `exec --detach` uses `subprocess.Popen(start_new_session=True)` + base64-encoded command on Linux.
> This calls the OS-level `setsid()` syscall — the process is placed in a **completely independent session**, immune to SIGHUP.
> The old pattern (`nohup sh -c '...' &`) was **NOT reliable** — Paramiko's channel close could still kill background processes via session group cleanup.
> Detached process stdout/stderr is routed to `/tmp/openclaw_detach.log`.

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
