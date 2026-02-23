---
name: podcast-maker
description: Generate a two-person authentic podcast discussion (Audio Overview) from any academic document or text, similar to Google NotebookLM.
metadata:
  openclaw:
    requires:
      python: ">=3.9"
      packages:
        - "requests"
        - "paramiko"
    env:
      - SSH_HOST
      - SSH_PORT
      - SSH_USER
      - SSH_PASS
---

# Podcast Maker Skill (NotebookLM Alternative)

This skill allows you (OpenClaw) to generate an authentic, two-person dialogue (an "Audio Overview") from a provided document or text, and synthesize it into high-fidelity human speech using a remote GPU server.

## Workflow

When the user asks you to "make a podcast", "generate an audio overview", or "create a dialog from this paper":

1. **Understand the Content**: Read the requested document or the text provided by the user.
2. **Generate the Script**: Write a natural, highly engaging, conversational script between two speakers (e.g., Host A and Guest B). They should discuss the key insights, findings, and implications of the document, making it accessible but intelligent.
3. **Format as JSON**: Format your script into a strict JSON file containing the dialogue.
   - Each turn must have a `"speaker"` (either `"host"` or `"guest"`) and the spoken `"text"`.
   - Ensure the text uses natural punctuation (commas, question marks) to help the TTS engine pause correctly.
4. **Save the JSON**: Save the JSON to a physical file in the workspace (e.g., `/Users/roy-jd/Documents/projects/openclaw/workspace/podcast_script.json`).
5. **Execute the Generator**: Use the `run_command` tool to execute `gen_podcast.py`, passing the input script and output path.

```bash
python skills/podcast-maker/gen_podcast.py --input /Users/roy-jd/Documents/projects/openclaw/workspace/podcast_script.json --output /Users/roy-jd/Documents/projects/openclaw/workspace/podcast.ogg
```

6. **Return the Audio**: Tell the user the absolute path to the generated `.ogg` or `.mp3` file so Feishu can send it as an audio message.

## JSON Script Example

```json
{
  "dialogue": [
    {
      "speaker": "host",
      "text": "Welcome back! Today we're diving into an incredibly fascinating new paper on Multi-Agent architectures."
    },
    {
      "speaker": "guest",
      "text": "Yeah, and what struck me immediately in this paper is how they solved the context-window bottleneck using asynchronous memory pools."
    },
    {
      "speaker": "host",
      "text": "Exactly. Let's break down how that memory pool actually functions..."
    }
  ]
}
```

## Backend Mechanism

The `gen_podcast.py` script automatically reads the `.env` credentials to establish an SSH tunnel to the `10.190.30.220` GPU server. It sends the JSON payload to the remote ChatTTS API, which renders the high-fidelity voices and returns the final synthesized `.ogg` file. You do not need to manually SSH into the server to trigger the TTS; the script handles it.
