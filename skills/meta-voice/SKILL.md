---
name: meta-voice
emoji: 🎙️
description: Professional Meta-based Voice Skill (SeamlessM4T v2) strictly for high-quality Voice-to-Voice (V2V) translation, offloaded to remote GPU.
metadata:
  {
    "openclaw":
      {
        "requires": { "env": ["SSH_HOST", "SSH_PORT", "SSH_USER"], "bins": ["python3"] }
      },
  }
---

# Meta Voice Skill (Seamless V2V)

This skill provides state-of-the-art Voice-to-Voice translation using Meta's SeamlessM4T v2 model. It automatically offloads the heavy computation to the remote GPU server.

## Actions

### V2V (Voice-to-Voice)

Translates or re-synthesizes an input voice file into another language (default: Mandarin).

```bash
python3 skills/meta-voice/meta_voice.py --input input.wav --output output.wav
```

> [!IMPORTANT]
> **API Daemon Requirement**
> This skill now interacts with a persistent processing backend on the GPU. You MUST deploy the remote API server first.
> Copy the `v2v_server.py` and `deploy_v2v_service.sh` to your GPU server (`10.190.30.220`), then run as root:
>
> ```bash
> chmod +x deploy_v2v_service.sh
> ./deploy_v2v_service.sh
> ```
>
> The API will then run permanently as a Linux `systemd` service (`systemctl status meta-v2v`) on port 8001.

## Engineering Standards

- **Remote Offloading**: All model inference happens on the GPU server.
- **Model Caching**: Models are cached in `/root/.cache/huggingface` on the server.
- **Error Handling**: Full SSH/Network resilience and dependency checks.
