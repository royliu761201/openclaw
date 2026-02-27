---
name: meta-voice
emoji: 🎙️
description: Professional Meta-based Voice Skill (SeamlessM4T v2 / MMS) for high-quality TTS and V2V, offloaded to remote GPU.
metadata:
  {
    "openclaw":
      {
        "requires": { "env": ["SSH_HOST", "SSH_PORT", "SSH_USER", "SSH_PASS"], "bins": ["python3"] }
      },
  }
---

# Meta Voice Skill (Seamless / MMS)

This skill provides state-of-the-art voice synthesis and translation using Meta's models. It automatically offloads the heavy computation to the remote GPU server.

## Actions

### 1. TTS (Text-to-Speech)
Generates high-quality speech from text.

```bash
python3 skills/meta-voice/meta_voice.py --action tts --text "Hello from Meta Voice" --output output.wav
```

### 2. V2V (Voice-to-Voice)
Translates or re-synthesizes an input voice file.

```bash
python3 skills/meta-voice/meta_voice.py --action v2v --input input.wav --output output.wav
```

## Engineering Standards
- **Remote Offloading**: All model inference happens on the GPU server.
- **Model Caching**: Models are cached in `/root/.cache/huggingface` on the server.
- **Error Handling**: Full SSH/Network resilience and dependency checks.
