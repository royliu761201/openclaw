#!/bin/bash
set -a
source /Users/roy-jd/.openclaw_secrets/.env
set +a
export OPENCLAW_PROFILE=dev
export OPENCLAW_STATE_DIR=/Users/roy-jd/.openclaw-dev
export OPENCLAW_CONFIG_PATH=/Users/roy-jd/.openclaw-dev/openclaw.json
export OPENCLAW_GATEWAY_PORT=19001
export OPENCLAW_GATEWAY_TOKEN=dev-token-123
exec /opt/homebrew/Cellar/node/25.6.1/bin/node /Users/roy-jd/Documents/projects/openclaw/dist/index.js gateway --port 19001
