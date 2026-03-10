#!/bin/bash
# Initialize NVM for non-interactive shell execution (e.g., via direct SSH execution)
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# Natively source pre-distributed secrets on the sandbox node
source ~/.openclaw_env
export OPENCLAW_CONFIG_PATH=~/workspace/config/openclaw_core.json

cd ~/openclaw || exit 1
npm run build
# ALWAYS directly spawn openclaw.mjs under PM2. 
# NEVER use scripts/run-node.mjs as it spawns child nodes without signal forwarding causing zombie orphans!
pm2 start openclaw.mjs --name "openclaw-gateway" -- gateway
