#!/bin/bash
# safe_reload.sh: 物理挂载环境变量并安全重载 OpenClaw PM2 进程的终极脚本
# --- 
# 🩸 【血泪教训 / BLOOD & TEARS WARNING】 🩸
# 仅仅在 2026 年初，我们就因为遗漏 PM2 的独立环境变量缓存机制而引发了超过 10 次以上的“幽灵故障”！
# 当你在 ~/.openclaw_env 里修改了 API 密钥、白名单、或配置文件路径后，
# 单纯的 `pm2 restart` 或 `pm2 reload` 是 **绝对无效** 的！
# PM2 进程会像僵尸一样，继续死死抱着它第一次启动时读取的旧环境变量（这会陷入长达数小时的静默失败，各种 400 错误，甚至不报错）。
# 
# 核心目的: 永远固化 `pm2 reload --update-env` 指令流。
# 任何人修改集群层面的环境变量配置文件后，必须、且只能通过本脚本重载网关，强制触发 --update-env 刷新底层物理映射！
# 必须让它成为肌肉记忆：改配置 -> 执行 safe_reload.sh！完全禁止思考和手抖！
#
# 使用方法: ./safe_reload.sh [pm2_process_name] (默认: 重载所有进程)

PROCESS_NAME="${1:-all}"

echo "🔄 [Safe Reload] 🩸 血泪防护机制启动：准备强力注入大盘环境变量，并热重载 PM2 进程: $PROCESS_NAME"

# 1. 挂载原生 NVM 环境 (防御系统层级节点跨越克隆差异)
if [ -f "$HOME/.nvm/nvm.sh" ]; then
    source "$HOME/.nvm/nvm.sh"
    echo "✅ [NVM] 成功挂载纯净的 Node 环境层."
else
    echo "⚠️ [NVM] 未检测到 ~/.nvm/nvm.sh，将降级使用系统环境."
fi

# 2. 强力挂载 `.openclaw_env` 核心密钥大盘 (防止 PM2 继续裸奔)
if [ ! -f ~/.openclaw_env ]; then
    echo "❌ [CRITICAL] 严重违规！底层大盘环境变量库 ~/.openclaw_env 不存在！不准重载！"
    exit 1
fi
source ~/.openclaw_env
echo "✅ [ENV] 成功解析 ~/.openclaw_env 环境变量映射."

# 3. 终结令: pm2 reload 携带 --update-env (彻底粉碎 10+ 次的历史陷阱)
echo "🚀 [PM2] 强制刷新守护运行时上下文，执行: pm2 reload $PROCESS_NAME --update-env ..."
pm2 reload "$PROCESS_NAME" --update-env

if [ $? -eq 0 ]; then
    echo "✅ [SUCCESS] 🩸 带有新鲜血液（最新配置）的 PM2 守护进程已成功归来！"
else
    echo "❌ [ERROR] PM2 重载抛出异常。请检查 PM2 状态！"
    exit 1
fi
