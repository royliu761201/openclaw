---
name: provision-shared-env
emoji: 🌍
description: Implements the L1 GPU Data Profile law to clone base-research into the global /jhdx0003008/envs/ namespace, strictly forbidding local node-isolated sandboxes.
---

# 🌍 Shared GPU Environment Provisioner

## 1. Operational Directive

According to system law `08_GPU_DATA_PROFILE.md`, creating private `conda` environments on GPU execution nodes (like `90-1` in `/home/kaixin/`) is physically forbidden. All heavy AI environments must be cloned securely to the 900TB shared array (`/jhdx0003008/envs/`) so they can seamlessly hot-swap between `90-1`, `90-2`, and other shadow nodes.

## 2. The Execution Contract

This skill strictly enforces the **Zero-Copy Hardlink Cloning (统一底座克隆法)**:
It will bypass global internet downloads (`pip install torch` bloat) and instantly hardlink the pristine `base-research` meta-environment into the target directory.

## 3. Usage

Run the unified script locally from the Mac to automate the remote payload:
`bash /Users/roy-jd/openclaw/skills/provision-shared-env/scripts/deploy.sh [ENV_NAME]`
Example:
`bash /Users/roy-jd/openclaw/skills/provision-shared-env/scripts/deploy.sh synergyfl`
