#!/bin/bash
# OpenClaw Standardized Codex Safekill Script
# Usage: codex_safekill.sh <WORKSPACE_PATH>
# Description: Safely terminates ONLY the Codex AI Agent instances assigned to a specific workspace directory, protecting sibling agents.

if [ -z "$1" ]; then
    echo "❌ FATAL: Workspace path must be provided."
    echo "Usage: ./codex_safekill.sh /path/to/workspace"
    exit 1
fi

TARGET_WORKSPACE=$(realpath "$1")
echo "🔍 Initiating surgical termination protocol for workspace: $TARGET_WORKSPACE"

# Find all processes running codex_launcher.sh or codex that include the exact workspace path in their arguments
TARGET_PIDS=$(pgrep -f "codex.*$TARGET_WORKSPACE")

if [ -z "$TARGET_PIDS" ]; then
    echo "✅ No active Codex processes found for workspace: $TARGET_WORKSPACE"
    exit 0
fi

echo "⚠️ Found active Codex PIDs tied to $TARGET_WORKSPACE: $TARGET_PIDS"
echo "🔪 Surgically terminating..."

# Terminate only the matched PIDs
for pid in $TARGET_PIDS; do
    kill -15 "$pid" 2>/dev/null
    echo "   Sent SIGTERM to PID $pid"
done

sleep 2

# Force kill any stubborn ones
for pid in $TARGET_PIDS; do
    if kill -0 "$pid" 2>/dev/null; then
        kill -9 "$pid" 2>/dev/null
        echo "   Sent SIGKILL to stubborn PID $pid"
    fi
done

echo "✅ Surgical termination complete. All sibling agents (PESSO, PIQ, etc.) are safe."
