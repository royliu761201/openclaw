#!/usr/bin/env python3
import subprocess
import json
import sys
import datetime

def run_ssh_cmd(cmd):
    try:
        result = subprocess.run(
            ["ssh", "02", f"source ~/.nvm/nvm.sh && {cmd}"],
            capture_output=True, text=True, check=True
        )
        return result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return e.stdout, e.stderr

def check_pm2():
    print("📡 [Radar] 探活 Node 02 PM2 守护进程...")
    stdout, stderr = run_ssh_cmd("pm2 jlist")
    try:
        data = json.loads(stdout)
        gateway = next((p for p in data if p.get('name') == 'openclaw-gateway'), None)
        if not gateway:
            print("❌ [Radar] 未找到 openclaw-gateway 进程！")
            return False
            
        status = gateway.get('pm2_env', {}).get('status')
        uptime = gateway.get('pm2_env', {}).get('pm_uptime')
        memory = gateway.get('monit', {}).get('memory', 0) / (1024 * 1024)
        
        if status == 'online':
            print(f"✅ [Radar] openclaw-gateway 存活 (状态: {status}, 内存: {memory:.1f} MB)")
            return True
        else:
            print(f"❌ [Radar] openclaw-gateway 异常 (状态: {status})")
            return False
    except Exception as e:
        print(f"❌ [Radar] 无法解析 PM2 状态: {e}")
        return False

def check_native_logs():
    print("📡 [Radar] 探活 OpenClaw 原生底层日志 (最近 100 行)...")
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    stdout, stderr = run_ssh_cmd(f"grep -i 'error\\|warn\\|fatal\\|exception' /tmp/openclaw/openclaw-{date_str}.log | tail -n 10")
    if stdout.strip():
        print("⚠️ [Radar] 发现新近异常日志:")
        for line in stdout.strip().split('\n'):
            try:
                log_obj = json.loads(line)
                time = log_obj.get("time", "")
                level = log_obj.get("logLevelName", "")
                msg = log_obj.get("0", "")
                print(f"   [{time}] {level}: {msg}")
            except:
                print(f"   {line}")
    else:
        print("✅ [Radar] 底层日志未发现近期的严重错误或崩溃。")

def check_port():
    print("📡 [Radar] 探活 18789 网关监听端口...")
    stdout, stderr = run_ssh_cmd("lsof -i :18789 | grep node || true")
    if "LISTEN" in stdout or "node" in stdout:
        print("✅ [Radar] 端口 18789 正常监听中。")
    else:
        print("❌ [Radar] 端口 18789 未被监听，发生脱网！")

def main():
    print("==================================================")
    print("🛸 OpenClaw Agent Radar (Node 02 Health Probe) 🛸")
    print("==================================================")
    pm2_ok = check_pm2()
    check_port()
    check_native_logs()
    
    if pm2_ok:
        print("\n🟢 [Radar Conclusion] 靶机 Node 02 边际网关状态健康。")
    else:
        print("\n🔴 [Radar Conclusion] 靶机 Node 02 边际网关发生故障，呼叫人工接入！")

if __name__ == "__main__":
    main()
