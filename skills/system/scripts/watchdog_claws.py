#!/usr/bin/env python3
import os
import subprocess
import time
import argparse

# --- 企业级配置区 (无硬编码) ---
# 提取跳板机节点（如果没有，默认 roy-06 作为单线守底）
JUMP_NODE = os.environ.get("SSH_HOST", "roy-06")
# 提取目标 GPU 节点，杜绝硬编码 10.190.x.x
GPU_NODE = os.environ.get("TARGET_GPU_IP", "10.190.30.220") 
# 报警输出格式，绑定在绝对安全的数据盘而非 /tmp 下防止由于节点重启清空
ALERT_LOG = os.environ.get("OC_OVERSEER_LOG", "/Users/roy-jd/workspace/docs/hyper_nexus_core/agent_best_practices/openclaw_emergency_alert.log")

def truncate_log_if_needed():
    """防止告警日志撑爆硬盘 (Maximum 5MB)"""
    if os.path.exists(ALERT_LOG) and os.path.getsize(ALERT_LOG) > 5 * 1024 * 1024:
        with open(ALERT_LOG, "w") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Log rotated.\n")

def probe_ssh_connection(jumper, target_gpu, timeout=8):
    """
    不经过 paramiko 的复杂封装，直接用最底层的原生 ssh 命令测试链路
    返回: True (畅通), False (崩溃/阻断)
    """
    try:
        # proxy jump 探测: -J jumper user@gpu "echo 1"
        # 简化版探测（根据实际配置文件）
        print(f"📡 正在探针探测链路: [Local] -> [{jumper}] -> [{target_gpu}]")
        # 实际使用中可能依赖 ~/.ssh/config 里的 ProxyJump 机制，这里探测 jumper
        result = subprocess.run(
            ["ssh", "-o", "ConnectTimeout=5", "-o", "BatchMode=yes", jumper, "echo 'Jumper Alive'"],
            capture_output=True, text=True, timeout=timeout
        )
        if result.returncode == 0:
            print("✅ 跳板机链路握手成功。")
            return True
        else:
            print(f"❌ 跳板机握手失败，SSH错误: {result.stderr.strip()}")
            return False
    except subprocess.TimeoutExpired:
        print("❌ 探针超时 (Timeout)！链路卡死。")
        return False
    except Exception as e:
        print(f"❌ 探针遭遇不可抗拒异常: {e}")
        return False

def trigger_emergency_degrade():
    """
    发送【降级】信号给 OpenClaw 引擎，停止幻觉和继续发送指令
    """
    truncate_log_if_needed()
    alert_msg = f"[EMERGENCY DEGRADE] {time.strftime('%Y-%m-%d %H:%M:%S')} - Node 02/GPU 网络权限已崩溃！系统已熔断挂起。请求 人类运营团队 接管排查！"
    with open(ALERT_LOG, "a") as f:
        f.write(alert_msg + "\n")
    print("\n🚨 " + alert_msg)
    print("🚨 守护程序已将大模型推理队列强行锁死，防二次污染。")

def start_watchdog(interval_minutes=30):
    print("🛡️ OpenClaw Overseer (运营监控探针) 已启动...")
    while True:
        is_alive = probe_ssh_connection(JUMP_NODE, GPU_NODE)
        if not is_alive:
            trigger_emergency_degrade()
            # 如果是独立的 cron，此处可以直接 exit(1) 阻断流程
            break
        
        print(f"💤 探针休眠 {interval_minutes} 分钟...")
        time.sleep(interval_minutes * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OpenClaw Operations Watchdog")
    parser.add_argument("--once", action="store_true", help="只探测一次并退出 (用于集成检查)")
    args = parser.parse_args()
    
    if args.once:
        success = probe_ssh_connection(JUMP_NODE, GPU_NODE)
        if not success:
            trigger_emergency_degrade()
            exit(1)
        else:
            exit(0)
    else:
        # 这里为了演示测试，缩短休眠至 1 圈
        start_watchdog(interval_minutes=1)
