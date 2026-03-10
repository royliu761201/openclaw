#!/bin/bash
# Initialize NVM for non-interactive shell execution (e.g., via direct SSH execution)
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# Natively source pre-distributed secrets on the sandbox node
source ~/.openclaw_env
export OPENCLAW_CONFIG_PATH=~/workspace/config/openclaw_core.json

cd ~/openclaw || exit 1
npm run build

# Inject an official skip-build flag! 
# Under PM2 daemon environments, if run-node.mjs attempts to spawn pnpm to build but pnpm is not in PATH,
# child_process.spawn throws an 'error' without 'exit', causing the wrapper Promise to hang indefinitely at 720KB ram!
export OPENCLAW_SKIP_BUILD=1
pm2 start scripts/run-node.mjs --name "openclaw-gateway" -- gateway
