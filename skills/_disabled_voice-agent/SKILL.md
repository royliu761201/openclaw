---
name: voice-agent
emoji: 🗣️
description: A suite of extremely low-latency Voice AI tools. Includes ChatTTS for generating expressive speech from text, and V2V (SeamlessM4T) for translating audio files (e.g., foreign language voice messages) directly into Mandarin speech while preserving the original speaker's emotional tone.
metadata:
  {
    "openclaw":
      {
        "requires": { "bins": ["python"] }
      },
  }
---

# Voice Agent Toolset

This skill provides two ultra-fast, local-tunnel backed voice generation commands. The heavy lifting is done on a remote GPU, but the commands act completely locally via the `127.0.0.1:18100` and `18200` proxy tunnels.

## 1. Text-to-Speech (ChatTTS)
Converts a text string into an expressive spoken audio file.

**Usage:**
```bash
python skills/voice-agent/tts_client.py --text "Your text here" --output /tmp/output.wav
```
*Optional argument:* `--speed 3` to adjust speaking rate. 

## 2. Voice-to-Voice Translation (SeamlessM4T Streaming)
Translates an input audio file (e.g., an English or French `.wav` or `.m4a` file) directly into a Chinese speaking `.wav` file, matching the original intonation.

**Usage:**
```bash
python skills/voice-agent/v2v_stream_client.py --input /path/to/foreign_audio.wav --output /tmp/chinese_translated.wav
```
*Note: Make sure the input file is an accessible audio file. If the user sends a Feishu voice message, download it to disk first and pass the path to `--input`.*
