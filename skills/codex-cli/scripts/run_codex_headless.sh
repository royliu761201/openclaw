#!/bin/bash
# Component 1: Codex Headless Autopilot Daemon

WORKSPACE_DIR=$1
PROMPT_FILE=$2

if [[ -z "$PROMPT_FILE" || -z "$WORKSPACE_DIR" ]]; then
    echo "Usage: ./run_codex_headless.sh <workspace_dir> <prompt_file_path>"
    exit 1
fi

if [[ ! -d "$WORKSPACE_DIR" ]]; then
    echo "Error: Workspace $WORKSPACE_DIR does not exist."
    exit 1
fi

if [[ ! -f "$PROMPT_FILE" ]]; then
    echo "Error: Prompt file $PROMPT_FILE does not exist."
    exit 1
fi

cd "$WORKSPACE_DIR" || exit 1

echo "[OpenClaw Autopilot] Initiating headless Codex spawn in $WORKSPACE_DIR..."
echo "[OpenClaw Autopilot] Reading prompt from $PROMPT_FILE..."

# Component 1: Codex Headless Autopilot Daemon Using Native `codex exec`
# This avoids TUI crashing and zombie background PTYs.
codex exec --dangerously-bypass-approvals-and-sandbox \
  -C "$WORKSPACE_DIR" \
  --json \
  --color never \
  -o .codex_final_output.log \
  "$(cat $PROMPT_FILE)" > .codex_execution_events.jsonl 2>&1

# Flush and ensure Codex writes the audit report before we hand control back to python
sync
echo "[OpenClaw Autopilot] Sub-agent Codex process completed."
