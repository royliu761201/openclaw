---
name: lsdyna-manager
emoji: 🏗️
description: Manage LS-DYNA simulations on the JHUN CPU workstation cluster (10.190.30.200).
---

# LS-DYNA Manager Skill

This skill provides instructions and patterns for running LS-DYNA simulations on the JHUN cluster login node (`10.190.30.200`).

## Connection Baseline

The workstation is accessed via a proxy jump through Node `06`.

- **Alias**: `cpu-200`
- **Host**: `10.190.30.200`
- **User**: `jhdx0000158`
- **Passwordless**: Configured using `id_ed25519` key.

> [!IMPORTANT]
> **SSOT Credentials**
> If you lose the SSH key or need to re-configure, the credentials are stored in `/Users/roy-jd/workspace/secrete.json`.

## Slurm Submission Standards

To run a job, you **MUST** specify the partition and the account. Failure to include the account results in an `Unspecified error`.

- **Partition**: `-p dyna`
- **Account**: `-A jhdx`

### Basic Job Template (`run_dyna.sh`)

```bash
#!/bin/bash
#SBATCH -J LS-DYNA_JOB
#SBATCH -p dyna           # Target the CPU workstation partition
#SBATCH -A jhdx           # REQUIRED: User account association
#SBATCH -N 1              # Number of nodes
#SBATCH -n 16             # Number of CPU cores
#SBATCH -o %j.out
#SBATCH -e %j.err

# Load the LS-DYNA environment
module load lsdyna/r16.1.1

# Execute LS-DYNA
# Replace input.k with your actual keyword file
# mpp-dyna -i input.k
```

## Available Software Versions

Check available versions with `module avail lsdyna`.
Currently verified:
- `lsdyna/r12.2.2`
- `lsdyna/r14.2.0`
- `lsdyna/r16.1.1` (Recommended)

## Troubleshooting

1. **Permission Denied (SSH)**: Run `ssh-add ~/.ssh/id_ed25519` in your local terminal.
2. **Unspecified Error (sbatch)**: Double check that `#SBATCH -A jhdx` is included in your script.
3. **Partition Down**: Use `sinfo` to check if the `dyna` partition is `up` and `idle`.
