#!/bin/bash
# Initialize NVM for non-interactive shell execution (e.g., via direct SSH execution)
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# Natively source pre-distributed secrets on the sandbox node
source ~/.openclaw_env
export OPENCLAW_CONFIG_PATH=~/workspace/config/openclaw_core.json

cd ~/openclaw || exit 1
npm run build
pm2 start scripts/run-node.mjs --name "openclaw-gateway" -- gateway
