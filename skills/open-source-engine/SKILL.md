---
name: open-source-engine
description: Advanced NeurIPS-compliant double-blind code repository generator. Integrates CaLaM-grade README aesthetics, GitHub API namespace handling, Vault Keeper OAuth syncing, and a Physical SSoT architecture with strict `internal_ops/` isolation to satisfy the Boss's data governance laws.
---

# `open-source-engine`

The `open-source-engine` is a flagship structural compilation skill. It transforms active AI/ML research codebases into impeccably formatted, anonymous public repositories tailored for top-tier conference submissions (e.g., NeurIPS, ICML).

## ⚡️ TRIGGER RULES

You MUST execute this skill ONLY when:
- The user requests to "open source a project", "prepare anonymous code", or "sync up the external public repository".

## 🛠️ USAGE (Pure MD-Driven SOP)

### 1. Execute Open-Source Pipeline

Takes two positional arguments: the active project workspace root, and the intended Public Repository label name.

```bash
python3 $HOME/openclaw/skills/open-source-engine/scripts/open_source_repo.py <workspace_dir> <public_name>
# Example: python3 ./open_source_repo.py /Users/roy-jd/workspace/projects_core/pesso PESSO
```

## ⚠️ CONSTITUTIONAL ANCHORS (THE BOSS'S SSoT LAW)

- **Physical SSoT Master Branch**: 
  - **MANDATORY**: All source code MUST reside physically within `projects_core/<project>`. Soft symlinks to public folders are STRICTLY FORBIDDEN as they break the Single Source of Truth and lead to empty repository bugs.
  - The engine uses **One-Way Physical Mirroring**: It copies assets from the Master Workspace to the Public Staging area, never the reverse.
- **Internal Ops Isolation (`internal_ops/` Pattern)**: 
  - To prevent "Engineering Drift" (non-academic scripts like VRAM probes, WandB hooks, or deployment scrap), developers must move operational tools to an `internal_ops/` directory within the master workspace.
  - The engine's **White-List Synchronization** automatically skips this directory, ensuring the public repo remains a pure scientific artifact.
- **Aggressive Purgation & Markdown Scrubbing**: 
  - Automatically strips sensitive identifiers (`Roy`, absolute paths, cluster IPs) across `.py`, `.sh`, and `.md` files.
  - Specifically targets absolute file URIs in READMEs to maintain double-blind integrity.
- **Nuclear History Purge**: 
  - Provides a `--reset-history` protocol to flatten the entire Git history into a single, clean `initial commit`. This is the standard for finalized NeurIPS submissions to ensure no historical metadata leaks.
- **GitHub Namespace Autonomy**: Harnesses the Vault Keeper's `GITHUB_OAUTH_TOKEN` to generate remote endpoints via the GitHub API, silently stripping any unappealing local suffixes like `_OpenSource` to provide a clean repository name (e.g., `royliu761201/PESSO`).
