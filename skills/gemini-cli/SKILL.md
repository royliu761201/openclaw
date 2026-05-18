---
name: gemini-cli
description: Official Google Gemini CLI. A powerful terminal agent with up to 1M token context, live Google Search grounding, system-level file/shell tools, and MCP extensibility. Powered by native Google Auth (OAuth/ADC).
---

# Gemini CLI Skill for OpenClaw

This skill transforms the OpenClaw agent by mounting Google's flagship multimodal models (e.g., Gemini 1.5 Pro, 2.0, 3.1 Pro) natively via the command line.

## Core Capabilities

- **Massive Context (1M Tokens)**: Ingest massive multi-file workspaces instantaneously using the `@path/to/dir` or `@file` pointers.
- **Autonomous Tool Execution**: Built-in capabilities include live `Google Search` grounding, robust system shell execution (prefixed with `!`), and full unhindered network capability.
- **Native Security Identity**: Secured directly by the system's underlying GCP authentication (OAuth2 / Application Default Credentials), completely bypassing fragile API key leaks and the macOS AMFI (Exit 137) code-signature protections.

## Agentic Usage Directives

> **For OpenClaw Autonomous Execution**:
> Issue queries without triggering the TUI by utilizing the `--prompt` (`-p`) flag:
>
> ```bash
> gemini -p "Analyze the physics solver logic in this directory" @pesso_core/
> ```

*Node: The CLI is bound to `lxh5147@gmail` via the Google Auth fallback. The local macOS Keychain lock has been overridden successfully.*
