---
name: remote-tts
emoji: 🎙️
description: A standalone Text-To-Speech (TTS) engine that securely offloads synthesis to the remote GPU server (10.190.30.220) via SSH and returns the generated audio file.
metadata:
  {
    "openclaw":
      {
        "requires": { "env": ["SSH_HOST", "SSH_PORT", "SSH_USER", "SSH_PASS"], "bins": ["python"] }
      },
  }
---

# Remote GPU Text-To-Speech (Standalone)

When the user asks you to synthesize speech from text using the remote GPU (or triggers the `remote-tts` skill), you must execute the provided Python wrapper script. This script automatically handles securing the SSH tunnel, parsing the raw string to the ChatTTS FastAPI schema, executing the inference on `10.190.30.220`, and downloading the result.

## Usage Instructions

To generate the audio, execute the following command:

```bash
python skills/remote-tts/remote_tts.py --text "The text to be synthesized goes here" --output "/path/to/save/the/audio.wav"
```

1. **Text**: Extract or clean the exact text the user wants to be spoken. If the text has newlines or quotes, make sure it is safely escaped in the shell command or save it to a temporary text file.
2. **Output**: Give the output file an intuitive name associated with the user's topic and save it in a reasonable directory (e.g. `/tmp/synthesis.wav` or their Downloads).
3. **Delivery**: Once the command completes successfully, you MUST return the absolute path of the generated `.wav` file to the user so they (or the Feishu agent attachment uploader) can play it.
