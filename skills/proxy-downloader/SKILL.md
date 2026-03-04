---
name: proxy-downloader
emoji: 🌍
description: Downloads files securely via a global proxy exit node, auto-routes the file to the Mac 03 secure vault (for permanent backup), and then physically erases the footprint on the proxy.
metadata: { "openclaw": { "requires": { "bins": ["python3"] } } }
---

# Global Proxy Downloader Skill

A robust, enterprise-grade fetching pipeline meant for circumventing heavy firewalls while preventing local disk exhaustion on the proxy node.

## The Workflow / Pipeline

When you call this tool:

1. **Fetch**: Uses the Windows Exit Node (`roy-005`, `100.98.236.51`) connected to a global proxy to snatch large files (like LLM `.bin` weights or GitHub repos).
2. **Transfer**: Pulls it from the Windows machine to a temporary relay on the central hub.
3. **Backup / Dump**: `scp`s the payload permanently into the Mac 03 (`roy-003`) secure storage vault (`~/.openclaw_backups/downloads`).
4. **Scrub**: Calls `del` to physically delete the heavy artifact on the proxy machine, ensuring 0% footprint.

## Tools

### ⬇️ `proxy_downloader`

Initiates the secure download, transfer, backup, and scrubbing workflow.

- **url** (string, required): The target HTTP/HTTPS resource to download.
- **filename** (string, required): The target filename to write it as (for example, `model.bin` or `repo.zip`).
- **backup_dir** (string, optional): Where this file will permanently reside on `roy-003` (defaults to `~/.openclaw_backups/downloads`).

**Usage**:

```bash
# Download a 2GB model weight cleanly and securely
./scripts/proxy_downloader.py "https://huggingface.co/../model.bin" "model.bin"
```
