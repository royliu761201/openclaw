---
name: workspace-asset-auditor
description: Forensic protocols for locating and recovering 'missing', 'stalled' or 'sandboxed' scientific assets in the local workspace.
---
# Workspace Asset Auditor Skill

This skill provides a standardized protocol for discovering files that have been successfully downloaded by browsers or agents but are 'invisible' to standard directory scans due to sandboxing (e.g., Playwright artifacts), hidden system paths, or specialized download directories.

## Core Capabilities

1. **System-Level Metadata Pursuit (mdfind)**
   Uses the macOS Spotlight index to locate files by exact byte size and timestamp, bypassing standard folder recursion limits.
   ```bash
   mdfind "kMDItemFSSize == [SIZE_IN_BYTES] && kMDItemContentModificationDate > \$time.now(-[MINUTES]m)"
   ```

2. **Browser Download Interrogation (Surgical SQLite)**
   Directly queries the Chrome `History` SQLite database to retrieve the `target_path` for completed downloads, providing the 'source of truth' for the file location.

3. **Sandbox Artifact Extraction**
   Automated traversal of agent-controlled temporary directories (e.g., `/private/var/folders/.../playwright-artifacts-*/`) to recover assets stalled in the brownser automation layer.

## When to Use
- When a file was reported as 'Downloaded' in UI but cannot be found via `find` or `ls`.
- When Chrome 'special directories' or custom 'Save As' locations are unknown.
- When an asset's UUID is the only known identifier.
