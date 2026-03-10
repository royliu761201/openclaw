#!/bin/bash
# Natively source pre-distributed secrets on the sandbox node
source ~/.openclaw_env
export OPENCLAW_CONFIG_PATH=~/workspace/config/openclaw_core.json

cd ~/openclaw || exit 1
npm run build
pm2 start scripts/run-node.mjs --name "openclaw-gateway" -- gateway
