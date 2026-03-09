# OpenClaw Workspace Standards & Laws

This document codifies the "Combat Operational Rules" and "Constitutional Laws" governing the OpenClaw workspace.

## 1. Git-Only Sync Law (SSoT)
- **Goal**: Maintain a single source of truth across Node 01, Node 02, Node 03, and GPU Clusters.
- **Rule**: Code MUST be pushed to GitHub from the source node and pulled onto the target node.
- **Prohibited**: `scp`, `rsync` (for code), manual copy/paste in chat.

## 2. Toolification of Experience
- **Philosophy**: "A rule is only as good as the tool that enforces it."
- **Action**: Whenever a new workflow (like "Rescue Node 05 Models") is successfully completed, it must be turned into a script or a skill.
- **Location**:
    - **Meta-Tools**: `openclaw/skills/`
    - **Mission-Tools**: `workspace/scripts/`

## 3. Secret Isolation Law
- **Goal**: Zero secrets in the public cloud.
- **Rule**: `.env` files and API keys stay on local disk, backed up only to Node 03 and protected Google Drive.
- **Mechanism**: `.gitignore` MUST contain `*.env` and `**/secrets/*`.

## 4. Physical Isolation Law
- **Goal**: Prevention of system pollution.
- **Rule**: All project work is confined to `~/workspace` or `/jhdx0003008/workspace`.
- **Warning**: Do not touch `/usr/local/bin` or system directories without explicit PDCA approval.

## 5. Anti-Bloat Law
- **Goal**: Maintain high-speed Git operations.
- **Rule**: No binaries > 10MB in Git. No large datasets.
- **Solution**: Use `data-vault` (Node 03) or specialized data skills for heavy assets.
