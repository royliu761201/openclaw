---
name: kokoro-tts
description: High-fidelity, zero-footprint local Text-to-Speech (TTS) engine based on the 82M Kokoro ONNX model, optimized for Apple Silicon and completely offline. Support for Mandarin, English, and Mixed.
---

# Kokoro TTS (Local On-Device Engine)

This is the designated primary Text-to-Speech engine for the OpenClaw architecture on Mac Nodes (Node 01 / Node 02).
It is specifically chosen for its ability to produce highly realistic, emotive voice synthesis matching ChatTTS, while maintaining an ultra-lightweight memory footprint (< 150MB) and requiring zero network connectivity to external GPU servers.

## ⚡ TRIGGER RULE
- Use this skill whenever a user requests an agent to "speak", "read aloud", or when a system needs to synthesize an audio alert, warning, or voice message locally (e.g. Node 02 radar alarm, reading arXiv abstracts).
- This completely supersedes the older `remote-tts` skill which hit severe latency and deployment walls.

## 📦 Zero-Friction Environment
This skill runs purely on `onnxruntime` and does NOT require massive PyTorch setups or Conda environments.
- **Dependencies**: `kokoro-onnx`, `soundfile`, `numpy==1.26.4`, `espeakng_loader`
- **Models**: The models (`kokoro-v1.0.onnx`, `voices-v1.0.bin`) are strictly held within the `models/` directory of this skill. They **must not** be pushed to Git. They are fetched from Node 03 (The Vault) during initial setup.

## 🛠️ Usage

Trigger the CLI directly. It does not spawn background daemons.

```bash
python3 scripts/kokoro_tts_tool.py --text "长官，雷达扫描完毕，一切正常。" --output /tmp/alert.wav
```

### Options
- `--text`: The text to synthesize. (Supports pure English, pure Mandarin, and Mixed sentences natively).
- `--output`: The destination `.wav` file path.
- `--voice`: (Optional) The voice profile to use. E.g., `af_heart` (Default English), `zf_xiaoxiao` (Default Chinese). Note: The engine auto-detects Chinese characters and will route to `cmn` language parsing and fallback to Chinese voices automatically.
- `--speed`: (Optional) Speech speed multiplier. Default is `1.0`.
- `--dry-run`: Evaluate synthesis performance (RTF) and OS compatibility instantly without actually leaving an audio file trace (saves to `/tmp/` and deletes immediately).

## ⚠️ L3 Compliance (Anti-Bloat & Zero-Interference)
1. **CPU Nice Level**: Running this script automatically drops its execution priority to `os.nice(19)`, ensuring it never interrupts the host's foreground IDE or browser experience.
2. **No Constant Audio Hook**: It strictly generates `.wav` outputs. If you need it to be heard, pass the `.wav` to an audio player (e.g. `afplay` on macOS) rather than keeping an audio handle open in python.
