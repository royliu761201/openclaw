---
name: ssh
description: Execute commands and transfer files on remote servers via SSH.
metadata: { "openclaw": { "requires": { "bins": ["python3"] } } }
---

# SSH Skill

Remote execution and file transfer using Paramiko.

## Tools

### `ssh_exec`

Execute a command on a remote server.

- **command** (string, required): Command to run (e.g., "nvidia-smi").
- **host** (string, optional): Override default host.
- **user** (string, optional): Override default user.

**Usage**:

```bash
python3 skills/ssh/scripts/ssh_tool.py exec "nvidia-smi"
```

### `ssh_upload`

Upload a file to the remote server.

- **local** (string, required): Local path.
- **remote** (string, required): Remote path.

**Usage**:

```bash
python3 skills/ssh/scripts/ssh_tool.py upload "workspace/script.py" "/home/user/script.py"
```

### `ssh_write`

Write content directly to a remote file.

- **remote** (string, required): Remote path.
- **content** (string, required): Content to write.

**Usage**:

```bash
python3 skills/ssh/scripts/ssh_tool.py write "/tmp/hello.txt" "Hello World"
```

### `ssh_download`

Download a file from the remote server.

- **remote** (string, required): Remote path.
- **local** (string, required): Local path.

**Usage**:

```bash
python3 skills/ssh/scripts/ssh_tool.py download "/home/user/output.log" "workspace/output.log"
```

### `ssh_conda`

Manage remote Conda environments.

- **subcommand** (string): `create`, `clone`, `delete`, `install`, `update`, `list`, or `install-manager`.
- **name** (string): Environment name.
- **packages** (list, optional): Packages to install/create with (use `--packages pkg1 pkg2`).
- **detach** (flag, optional): Run in background (useful for long installs).
- **clone_from** (string, optional): Source environment (clone).

**Usage**:

```bash
# Auto-Install Miniconda (if missing)
python3 skills/ssh/scripts/ssh_tool.py conda install-manager

# Create (Offline/Background)
python3 skills/ssh/scripts/ssh_tool.py conda create -n my_env --packages python=3.9 numpy --detach

# Install (Long Running)
python3 skills/ssh/scripts/ssh_tool.py conda install -n my_env --packages torch --detach

# Clone
python3 skills/ssh/scripts/ssh_tool.py conda clone -n new_env --clone-from old_env

# Execute in Env
python3 skills/ssh/scripts/ssh_tool.py exec "python train.py" --conda_env my_env
```
