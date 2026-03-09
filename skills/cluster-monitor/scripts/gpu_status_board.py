#!/usr/bin/env python3
import subprocess
import sys

def main():
    print("="*60)
    print("🖥️  GPU SERVER (10.190.30.220) REAL-TIME STATUS (Remote)")
    print("="*60)

    # Encode the python script to run on the GPU side
    remote_script = """
import os, subprocess, time, urllib.request, ssl
# CPU Load
try:
    with open('/proc/loadavg', 'r') as f: load = f.read().split()[:3]
    print(f"⚙️  [CPU Load]   : 1m: {load[0]} | 5m: {load[1]} | 15m: {load[2]}  (Cores: {os.cpu_count()})")
except: pass
# Mem
try:
    with open('/proc/meminfo', 'r') as f:
        lines = f.readlines()
        mt = int(lines[0].split()[1]) / (1024*1024)
        ma = int(lines[2].split()[1]) / (1024*1024)
        print(f"🧠 [Memory]     : {mt-ma:.1f} GB / {mt:.1f} GB ({(mt-ma)/mt*100:.1f}%)")
except: pass
# GPU
try:
    smi = subprocess.check_output(["nvidia-smi", "--query-gpu=index,name,utilization.gpu,memory.used,memory.total", "--format=csv,noheader,nounits"]).decode().strip().split('\\n')
    for line in smi:
        idx, name, util, mem_u, mem_t = [x.strip() for x in line.split(',')]
        print(f"🎮 [GPU {idx}]     : {name:<12} | Util: {util:>2}% | Mem: {mem_u:>5} / {mem_t} MB")
except: print("🎮 [GPU]        : Service Unavailable")
# Disk
print("-" * 60)
for p, l in [("/", "Root"), ("/jhdx0003008", "IPFS Vault")]:
    try:
        st = os.statvfs(p)
        total = (st.f_blocks * st.f_frsize) / (1024**4)
        free = (st.f_bavail * st.f_frsize) / (1024**4)
        print(f"💽 [{l:<14}] : {total-free:.1f} TB / {total:.1f} TB ({(total-free)/total*100:.1f}% Use)")
    except: pass
# Bandwidth
print("-" * 60)
print("🌐 [Outbound Bandwidth - Aliyun Tunnel]")
try:
    ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request("https://mirrors.aliyun.com", headers={'User-Agent': 'curl'})
    start = time.time(); res = urllib.request.urlopen(req, context=ctx, timeout=3); data = res.read()
    print(f"🚀 Aliyun Endpoint Ping: {(time.time() - start)*1000:.0f} ms (Connected)")
except Exception as e: print(f"❌ Aliyun Unreachable: {e}")
"""

    try:
        proc = subprocess.run(
            ["ssh", "-o", "ConnectTimeout=5", "-o", "BatchMode=yes", "gpu", "python3", "-"],
            input=remote_script.encode('utf-8'),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=10
        )
        if proc.returncode != 0:
            print("❌ FAIL-FAST: SSH Auth or Network failure. (Verify 06 Jump or VPN)")
        else:
            print(proc.stdout.decode().strip())
    except subprocess.TimeoutExpired:
        print("❌ FAIL-FAST: GPU probe timed out (>10s). Server hanging or overloaded.")
    except Exception as e:
        print(f"❌ FAIL-FAST: SSH Auth or Network failure: {e}. (Verify 06 Jump or VPN)")

    print("="*60)

if __name__ == "__main__":
    main()
