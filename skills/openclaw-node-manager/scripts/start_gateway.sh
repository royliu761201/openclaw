#!/bin/bash
# Initialize NVM for non-interactive shell execution (e.g., via direct SSH execution)
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# --- ENVIRONMENT INJECTION (The True SSoT) ---
# Natively source pre-distributed secrets and core paths on the node
if [ ! -f ~/.openclaw_env ]; then
    echo "❌ [CRITICAL] 严重违规！底层密钥库 ~/.openclaw_env 不存在！进程已启动自毁..."
    exit 1
fi
source ~/.openclaw_env

# --- SSoT DEFENSE MATRIX (Fail-Fast Scorched Earth) ---
# 1. 存在断言：严禁脱离大盘环境自启。完全信任上方的 source 注入。
if [ -z "$OPENCLAW_CONFIG_PATH" ] || [ ! -f "$OPENCLAW_CONFIG_PATH" ]; then
    echo "❌ [CRITICAL] 严重违规！SSoT 主干配置路径 \$OPENCLAW_CONFIG_PATH ($OPENCLAW_CONFIG_PATH) 解析失败或物理文件遗失！进程已自毁..."
    exit 1
fi

# 2. 物理焦土：粉碎所有试图引起降级误读的兜底点位
rm -f ~/.openclaw/openclaw.json ~/openclaw/config/openclaw_core.json ~/.openclaw/auth-profiles.json 2>/dev/null || true

cd ~/openclaw || exit 1

# Inject an official skip-build flag! 
# Under PM2 daemon environments, if run-node.mjs attempts to spawn pnpm to build but pnpm is not in PATH,
# child_process.spawn throws an 'error' without 'exit', causing the wrapper Promise to hang indefinitely at 720KB ram!
export OPENCLAW_SKIP_BUILD=1

# --- PROCESS IGNITION ---
echo "🧹 执行彻底的物理进程级清理 (Scorched Earth Process Wipe)..."
pm2 delete openclaw-gateway 2>/dev/null || true
# PM2 delete 只能取消守护状态，如果有悬空 (detached) 的僵尸进程，必须依靠 pkill 斩草除根
pkill -9 -f "openclaw.mjs" 2>/dev/null || true

pm2 start ~/openclaw/openclaw.mjs --interpreter node --name "openclaw-gateway" --update-env -- gateway
pm2 save
