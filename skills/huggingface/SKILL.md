---
name: huggingface
description: Download datasets and models from HuggingFace.
metadata: { "openclaw": { "requires": { "bins": ["python"] } } }
---

# HuggingFace Skill

Tools for interacting with the HuggingFace Hub.

## Heavy Asset Visa & Git Bloat Protection
> **[L1 Constitution Block]**: HuggingFace models and datasets are typically massive (GBs).
> 1. You are STRICTLY FORBIDDEN from downloading datasets or models directly into `~/workspace/projects_core/` or `~/workspace/docs/`. Doing so will bloat the Git SSoT and paralyze synchronization.
> 2. You MUST route downloads to the local node's Cold Vault (e.g., `/Volumes/[DiskName]/data_vault/models/` on Mac 03, or an un-tracked `~/.cache/huggingface/` location) and then `ln -s` symlink them into your project's `data/` directory.

## Tools

### `download_dataset`
Download a dataset.

- **dataset_id** (string, required): e.g., "glue", "squad".
- **split** (string, optional): e.g., "train".

### `download_model`
Download a model snapshot.

- **model_id** (string, required): e.g., "bert-base-uncased".
