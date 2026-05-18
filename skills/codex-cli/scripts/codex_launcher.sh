#!/bin/bash
# OpenClaw Standardized Codex Launcher
# Usage: codex_launcher.sh <PROJECT_NAME> <WORKSPACE_PATH> <PROMPT_FILE_PATH>

PROJECT="$1"
WORKSPACE="$2"
PROMPT_FILE="$3"

# 1. Set terminal window title (ANSI escape + breadcrumb)
echo -ne "\033]0;[${PROJECT}] AI Agent Session - $(date +%H:%M)\007"

# 2. Print Aegis-Header (Rich Aesthetics)
clear
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " 🏗️  PROJECT: ${PROJECT}"
echo " 🌐 PATH: ${WORKSPACE}"
echo " 🎯 MISSION: $(basename ${PROMPT_FILE})"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 3. Enter Workspace
cd "${WORKSPACE}" || exit 1

# 4. Load Prompt
if [ ! -f "${PROMPT_FILE}" ]; then
    echo "❌ FATAL: Prompt file ${PROMPT_FILE} not found!"
    sleep 5
    exit 1
fi

PROMPT=$(cat "${PROMPT_FILE}")

# 5. Launch Codex in Bypass Mode
codex --dangerously-bypass-approvals-and-sandbox "${PROMPT}"

# 6. Preserve session for inspection
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " ✅ SESSION COMPLETE. Terminal held for manual review."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
exec zsh
