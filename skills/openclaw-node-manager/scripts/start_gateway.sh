#!/bin/bash
# Initialize NVM for non-interactive shell execution (e.g., via direct SSH execution)
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# --- SSoT DEFENSE MATRIX (Fail-Fast Scorched Earth) ---
export OPENCLAW_CONFIG_PATH="$HOME/workspace/config/openclaw_core.json"

# 1. 物理焦土：粉碎所有试图引起降级误读的兜底点位
rm -f ~/.openclaw/openclaw.json ~/openclaw/config/openclaw_core.json ~/.openclaw/auth-profiles.json 2>/dev/null || true

# 2. 存在断言：严禁脱离大盘环境自启
if [ ! -f "$OPENCLAW_CONFIG_PATH" ]; then
    echo "❌ [CRITICAL] 严重违规！SSoT 主干配置文件未正确指向 $OPENCLAW_CONFIG_PATH 或文件遗失！进程已启动自毁..."
    exit 1
fi

# --- ENVIRONMENT & ENV INJECTION ---
# Natively source pre-distributed secrets on the sandbox node
source ~/.openclaw_env

cd ~/openclaw || exit 1

# Inject an official skip-build flag! 
# Under PM2 daemon environments, if run-node.mjs attempts to spawn pnpm to build but pnpm is not in PATH,
# child_process.spawn throws an 'error' without 'exit', causing the wrapper Promise to hang indefinitely at 720KB ram!
export OPENCLAW_SKIP_BUILD=1

# --- PROCESS IGNITION ---
pm2 delete openclaw-gateway 2>/dev/null || true
pm2 start ~/openclaw/openclaw.mjs --interpreter node --name "openclaw-gateway" --update-env -- gateway
pm2 save
