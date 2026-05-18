---
name: codex-cli
description: Official OpenAI Codex CLI agent integration. Allows OpenClaw to spawn parallel AI coding agents to perform massive code refactoring, context-aware analysis, and workspace editing utilizing the Mac native Keychain session.
---

# Codex CLI Skill for OpenClaw

## Overview

The `codex` CLI is a native OpenClaw skill powered by OpenAI. It is an agentic coding tool that can autonomously explore codebases, modify files, and run terminal commands.

Because this Mac already has an active ChatGPT/OpenAI native session, the CLI uses the system Keychain and requires ZERO login configuration.

> **[AB-053] ⚠️ 安装与恢复指引 (Critical Installation SSoT)**
> If the `codex` command goes missing or fails to initialize globally, DO NOT try to repair using `brew install codex` (often suffers from 404 upstreams) and absolutely DO NOT use `registry.npmmirror.com` (suffers from alias resolution bugs masking internal downloads).
> **The only legally compliant and AMFI-safe installation method is:**
> `npm install -g @openai/codex --registry=https://registry.npmjs.org`

## Agent Invocation Guide (How OpenClaw should use this)

> [!CAUTION]
> **[15_TRIAD_ORCHESTRATION_LAW] THE TRIAD PROTOCOL IS MANDATORY.**
> OpenClaw Agents (Antigravity/Dandan) are strictly forbidden from rewriting massive structural code locally. You MUST act as the **Commander**, while Codex acts as the **Executor**. 
> For any multi-step complex restructuring, you MUST invoke the **Headless Dispatch (Option B)** to parse its JSONL telemetry dynamically, injecting strict environment isolations (`mps` vs `cuda`).

When requested by the Boss to use Codex, OpenClaw should delegate the execution to the globally installed `codex` binary using one of two core paradigms:

### Option A: Native Spawning with Interactive UI (Highly Recommended)
This is the safest and most robust execution path. It uses AppleScript (`osascript`) to spawn a real, independent macOS Terminal window on the user's desktop.
**Why use Option A?**
- Bypasses background PTY instability and hanging.
- The user can visually monitor Codex's TUI (Terminal User Interface) and reasoning process in real-time.
- If Codex panics or requires user approval, the user can manually intervene.

**Engineering Protocol for Option A:**
Create a temporary bash script and launch it via AppleScript.
```bash
cat << 'EOF' > /tmp/run_codex_interactive.sh
#!/bin/bash
cd /path/to/workspace
PROMPT=$(cat prompt.txt)
codex --dangerously-bypass-approvals-and-sandbox -C /path/to/workspace "$PROMPT"
# Keep terminal open upon exit
exec zsh
EOF

chmod +x /tmp/run_codex_interactive.sh
osascript -e 'tell app "Terminal" to do script "/tmp/run_codex_interactive.sh"'
```

### Option B: Agent-to-Agent Headless Dispatch (Native `codex exec`)

When **another AI agent** (e.g., OpenClaw/Antigravity) needs to spawn Codex as a parallel sub-agent to perform autonomous code audits, code generation, or bug fixing without disrupting the user, use the native `codex exec` non-interactive mode.

**Why use `codex exec`?**
- Bypasses the TUI completely, preventing terminal hang problems and messy ANSI stdout artifacts.
- No need for fragile `script -q` PTY wrappers.
- Supports `--json` for clean, parseable events.
- Writes the final output cleanly to a destination file via `-o`.

**Engineering Protocol for Headless Dispatch:**

1. **Write the prompt to a temp file** (avoids shell escaping nightmares):
```bash
cat << 'EOF' > /tmp/codex_task_prompt.txt
Perform a comprehensive audit of this codebase focusing on:
1. Fail-fast enforcement
2. Memory safety
Patch files directly. Once finished, write a short summary of the changes to `audit_report.md`.
EOF
```

2. **Launch `codex exec` as a background process**:
```bash
codex exec \
  --dangerously-bypass-approvals-and-sandbox \
  -C /path/to/workspace \
  --json \
  --color never \
  -o /tmp/codex_final_msg.txt \
  "$(cat /tmp/codex_task_prompt.txt)" \
  > /tmp/codex_events.jsonl 2>&1 &
  
CODEX_PID=$!
```

3. **Monitor from parent agent**:
Poll the process status using `kill -0 $CODEX_PID` or check if the target output file (e.g. `audit_report.md` or `/tmp/codex_final_msg.txt`) has been written.
Alternatively, tail the `/tmp/codex_events.jsonl` file to parse structured progress markers (like `"type":"turn.started"`).

4. **Robust Termination / Cleanup**:
Once the task is verified complete, or if it hangs unconditionally (which is rare with `codex exec`), politely terminate the background agent:
```bash
kill -15 $CODEX_PID && sleep 2 && kill -0 $CODEX_PID 2>/dev/null && kill -9 $CODEX_PID
```

> [!IMPORTANT]
> **Do NOT use `--prompt`** — this flag does not exist in modern Codex CLI. The prompt is a **positional argument**.
> **Always add the Mac/CUDA static analysis guard** if auditing GPU code locally (see Section 4).

### Live Web Search Integration
If the task requires up-to-date documentation or searching the internet, append the `--search` flag to the `codex exec` options.

### 3. Bypassing API Tier Limits for Frontier Models (e.g. GPT-5.4 / o1)

**CRITICAL WARNING:** Do NOT use explicit model override flags (`-m gpt-5.4` or `/model gpt-5.4`) when the user is authenticated via a standard ChatGPT Plus consumer account. The server will automatically map the strongest authorized context available to the Keychain token (e.g. `gpt-5.4 default`) without tripping the separate API funding blocks.

### 6. Hardware Semantic Gap (Mac vs CUDA)

If OpenClaw is running on a Mac (which uses Apple Silicon `mps`), but the target code is engineered for a remote Linux GPU cluster (`cuda`), **Codex will crash** if allowed to execute PyTorch tensor probes dynamically, because it will encounter `mps:0 vs cpu` mismatches.

**Mandatory Defense**: When auditing CUDA code locally on Mac, you MUST explicitly inject the following directive into the Codex prompt:
`"CRITICAL RULE: Perform PURE STATIC AST ANALYSIS ONLY. Do NOT execute Python code or instantiate PyTorch tensors dynamically to test shapes, or you will cause an MPS/CPU hardware crash."`

---

**Note to OpenClaw Agents**:
Do NOT attempt to run `codex login` or `codex auth`. The Mac M4 environment natively injects the authentication token via Keychain.

### 7. Project-Aware Branding (Standardized Headers)

When launching an **Interactive Codex Session (Option A)**, agents MUST use the standardized launcher to ensure a High-Aesthetic "Pro-Design" experience. This creates clear terminal titles and a mission-focused header.

**Standard Invocation Protocol:**
```bash
/Users/roy-jd/openclaw/skills/codex-cli/scripts/codex_launcher.sh "PROJECT_NAME" "WORKSPACE_PATH" "PROMPT_FILE_PATH"
```

**What this does:**
1.  **Sets Window Title**: The terminal title will precisely reflect the project context (e.g., `[PIQ] AI Agent Session`).
2.  **Breadcrumb Header**: Generates a stylized visual header with the project path and mission summary.
3.  **Persists Session**: Uses `exec zsh` to keep the shell open after completion, allowing the user to audit results manually.

### 8. Multi-Step Execution (Resuming context via `resume`)

When running headless `codex exec` processes, the session cannot be interrupted mid-flight. To build multi-step Agent reasoning pipelines, you must wait for the first execution to complete, and then use `codex exec resume <THREAD_ID>` to inherit the exact context.

> [!CAUTION]
> **THE CONTEXT HIJACKING VULNERABILITY (DO NOT USE `--last`)**
> In a multi-agent environment (Antigravity/OpenClaw), multiple parallel Codex instances (e.g., Data Prep, Checkpointing, Networking) might be running concurrently in the background. If you blindly use `codex exec resume --last`, you are mathematically guaranteed to hijack the session of whichever pipeline spawned most recently, causing catastrophic hallucination and context pollution.
> **RULE:** You are STRICTLY FORBIDDEN from using `--last`. You MUST explicitly declare the architectural `thread_id`.

**Engineering Protocol for Multi-Agent Workflows:**

```bash
# Round 1: Initial task (Output JSON log to a unique file)
codex exec --dangerously-bypass-approvals-and-sandbox -C /path/to/project --json -o /tmp/r1.md "Analyze..." >> /tmp/my_task.jsonl 2>&1 &
# ... Wait for Round 1 to exit ...

# Round 1.5: Grep the exact Thread ID created by Round 1
THREAD_ID=$(grep "thread.started" /tmp/my_task.jsonl | head -n 1 | grep -o '"thread_id":"[^"]*"' | cut -d'"' -f4)

# Round 2: Resume EXACT state safely
codex exec resume $THREAD_ID --dangerously-bypass-approvals-and-sandbox --json -o /tmp/r2.md "Based on your findings, patch the file." >> /tmp/my_task_r2.jsonl 2>&1 &
```

Alternatively, use the globally solidified integration script which handles this perfectly:
```bash
/Users/roy-jd/openclaw/skills/codex-cli/scripts/resume_thread.sh "019d4102-..." "/path/to/prompt.txt" "/tmp/output.md"
```
