---
name: vault-keeper
description: Highly-privileged, isolated secret distribution skill. Converts flat JSON keystores into bash-compatible environments across the OpenClaw topology.
---

# `vault-keeper` (The Gates) Skill

The `vault-keeper` is a highly-privileged operational skill completely ring-fenced from standard task logic. It governs the sync and distribution of API keys (LLM, Tavily, Exa, etc.) across the OpenClaw nodes.

## ⚡️ TRIGGER RULES

You MUST execute this skill ONLY when:

- The user explicitly requests to "distribute secrets", "sync API keys", or deploy the `.env` payload to edge nodes (like Node 02/03).

## 🛠️ USAGE (Pure MD-Driven SOP)

### 1. Distribute SSoT Secrets

Takes the master `secrets_flat.json` vault and securely deploys it via fail-fast SCP as `~/.openclaw_env` across the network, injecting the source commands into `~/.bash_profile`.

```bash
python3 $HOME/openclaw/skills/vault-keeper/scripts/sync_secrets.py
```

## ⚠️ CONSTITUTIONAL ANCHORS

- **Strict Isolation**: Because this skill pushes raw API keys across SSH, it MUST be executed entirely independently of generic reasoning tasks to prevent prompt-injection exfiltration.
- **Fail-Fast Enforcement**: The embedded script utilizes strict timeouts to prevent SSH handshakes from hanging the entire agent loop.
