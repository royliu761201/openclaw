#!/bin/bash
# safe_reload.sh: Natively and Safely Reload OpenClaw PM2 Processes with Full Environment Re-Injections
# --- 
# [BLOOD & TEARS WARNING]
# In early 2026 alone, we triggered over 10 "Ghost Failures" simply because we forgot PM2's isolated environment caching mechanism!
# When you modify API keys, whitelists, or config paths in ~/.openclaw_env, 
# a simple `pm2 restart` or `pm2 reload` is **ABSOLUTELY INEFFECTIVE**!
# The PM2 process will act like a zombie, tightly clinging to the old environment variables it read during its first boot 
# (leading to hours of silent failures, HTTP 400 errors, or completely suppressed logs).
# 
# PURPOSE: Permanently codify the `pm2 reload --update-env` command execution flow.
# Anyone modifying cluster-level environment variables MUST exclusively use this script to reload the gateway, 
# forcing the --update-env flag to refresh the underlying physical environment mapping!
# This MUST become muscle memory: Change config -> Execute safe_reload.sh! No thinking, no typos allowed!
#
# USAGE: ./safe_reload.sh [pm2_process_name] (default: target all processes)

PROCESS_NAME="${1:-all}"

echo "🔄 [Safe Reload] Blood & Tears Defense activated: Preparing to inject master environment variables and hot-reload PM2 process: $PROCESS_NAME"

# 1. Mount Native NVM Environment (Defense against Cross-Node System Level Clone Discrepancies)
if [ -f "$HOME/.nvm/nvm.sh" ]; then
    source "$HOME/.nvm/nvm.sh"
    echo "✅ [NVM] Successfully mounted pure Node environment layer."
else
    echo "⚠️ [NVM] ~/.nvm/nvm.sh not found. Downgrading to system node path."
fi

# 2. Force Mount `.openclaw_env` Master Secret Hub (Preventing PM2 from running bare)
if [ ! -f ~/.openclaw_env ]; then
    echo "❌ [CRITICAL] SEVERE VIOLATION! Master environment vault ~/.openclaw_env does not exist! Aborting reload!"
    exit 1
fi
source ~/.openclaw_env
echo "✅ [ENV] Successfully parsed ~/.openclaw_env environment vectors."

# 3. The Execution Order: pm2 reload with --update-env (Completely crushing the 10+ historical traps)
echo "🚀 [PM2] Forcing daemon context refresh, executing: pm2 reload $PROCESS_NAME --update-env ..."
pm2 reload "$PROCESS_NAME" --update-env

if [ $? -eq 0 ]; then
    echo "✅ [SUCCESS] PM2 daemon has successfully returned with fresh configs!"
else
    echo "❌ [ERROR] PM2 reload threw an exception. Please check PM2 status!"
    exit 1
fi
