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
