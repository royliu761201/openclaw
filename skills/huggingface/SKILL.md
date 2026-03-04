---
name: huggingface
description: Download datasets and models from HuggingFace.
metadata: { "openclaw": { "requires": { "bins": ["python"] } } }
---

# HuggingFace Skill

Tools for interacting with the HuggingFace Hub.

## Tools

### `download_dataset`
Download a dataset.

- **dataset_id** (string, required): e.g., "glue", "squad".
- **split** (string, optional): e.g., "train".

### `download_model`
Download a model snapshot.

- **model_id** (string, required): e.g., "bert-base-uncased".
