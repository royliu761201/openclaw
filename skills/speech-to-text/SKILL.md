---
name: speech-to-text
emoji: 👂
description: High-precision ASR using M1-optimized whisper.cpp on Mac 02. Features on-demand execution (Zero-footprint) to preserve system memory.
metadata: { "openclaw": { "requires": { "bins": ["python3", "ssh"] } } }
---

# Speech-to-Text (ASR) Skill

OpenClaw's specialized auditory sense, tailored for Apple Silicon (Mac 02).

## Tools

### `transcribe`

Converts an audio file into text using localized Whisper.cpp acceleration.

- **audio_path** (string, required): Local path to the `.wav` file.
- **model** (string, optional): Whisper model to use (default: `large-v3-turbo-q5`).
- **language** (string, optional): Source language hints (e.g., `zh`, `en`).

**Usage**:

```bash
./scripts/asr_tool.py "/tmp/meeting_notes.wav" --language "zh"
```
