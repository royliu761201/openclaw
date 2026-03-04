---
name: claw-fetch
emoji: 🚀
description: Unified high-speed fetcher using aria2c with 16-parallel segments. Standardized directory structure for raw data, processed files, and model weights.
metadata: { "openclaw": { "requires": { "bins": ["aria2c", "bash"] } } }
---

# Claw Fetch Skill

Enterprise-grade unified fetcher designed for maximum speed and data organization.

## Tools

### `claw_fetch`

Downloads a file from a URL using multi-threaded acceleration and categorizes it.

- **url** (string, required): The source URL.
- **filename** (string, required): Destination filename.
- **type** (string, optional): Category: `raw` (default), `processed`, or `weights`.
- **provider** (string, optional): Source identifier (e.g., `huggingface`).

**Usage**:

```bash
# Fetching model weights
./scripts/claw-fetch.sh "https://example.com/model.bin" "v3.bin" "weights" "hf"
```
