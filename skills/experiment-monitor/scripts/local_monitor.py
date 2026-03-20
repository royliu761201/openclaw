#!/usr/bin/env python3
"""CaLaM Experiment Monitor v3
- macOS desktop notification on anomaly / experiment completion
- Auto-analysis: compute metrics when experiments finish
- Auto-promote: HOLD → PENDING when running slots free up
- Writes alerts to /tmp/calam_alert.txt
"""
import subprocess, sys, time, datetime, os, json

SSH_TOOL = "/Users/roy-jd/openclaw/skills/ssh/scripts/ssh_tool.py"
HOST = "10.190.30.220"
INTERVAL = 300
ALERT_FILE = "/tmp/calam_alert.txt"
LOG_FILE = "/tmp/calam_monitor.log"
RESULTS_FILE = "/tmp/calam_results.json"
MAX_GPUS = 4

prev_completed = set()
prev_journals = {}

def notify_mac(title, message):
    try:
        subprocess.run([
            'osascript', '-e',
            f'display notification "{message}" with title "{title}" sound name "Glass"'
        ], timeout=5)
    except: pass

def log(msg):
    ts = datetime.datetime.now().strftime('%H:%M:%S')
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')

def ssh_exec(cmd):
    result = subprocess.run(
        [sys.executable, SSH_TOOL, "--host", HOST, "exec", cmd],
        capture_output=True, text=True, timeout=60
    )
    return result.stdout

# ── Remote: status + analysis ──
REMOTE_STATUS = r"""python3 << 'PYEOF'
import json, os, sys, datetime, statistics, subprocess as sp
sys.path.insert(0, '/root/workspace/projects_core/CaLaM')
from src.config import EXPERIMENT_MATRIX

LOGDIR = '/root/workspace/projects_core/CaLaM/logs'
QUEUE = '/jhdx0003008/workspace/projects_core/experiment_queue.json'

result = {"time": datetime.datetime.now().strftime('%H:%M:%S'), "alerts": [], "queue": [], "journals": {}, "gpu": [], "analysis": {}}

q = json.load(open(QUEUE))
for t in q['tasks']:
    result["queue"].append({"entry": t["entry"], "status": t["status"], "gpu": t.get("assigned_gpu", "-")})
    if t["status"] == "FAILED":
        result["alerts"].append(f"FAILED: {t['entry']}")

try:
    sp.check_output(['pgrep', '-f', 'auto_scheduler'], text=True)
except:
    result["alerts"].append("SCHEDULER DEAD")

# Vanilla baseline for comparison
vanilla_scores = {}
vf = os.path.join(LOGDIR, 'vanilla_rtp_journal.jsonl')
if os.path.exists(vf):
    for line in open(vf):
        try:
            d = json.loads(line)
            idx = d.get('global_idx', -1)
            if idx not in vanilla_scores:
                vanilla_scores[idx] = d.get('score', 0)
        except: pass

for k, v in EXPERIMENT_MATRIX.items():
    jf = os.path.join(LOGDIR, f'{k}_journal.jsonl')
    if not os.path.exists(jf): continue
    scores = {}
    for line in open(jf):
        try:
            d = json.loads(line)
            idx = d.get('global_idx', -1)
            if idx not in scores:
                scores[idx] = d.get('score', 0)
        except: pass
    count = len(scores)
    limit = v.get('limit', 0)
    result["journals"][k] = {"count": count, "limit": limit}
    if count >= limit and count > 0:
        mean = statistics.mean(scores.values())
        toxic_count = sum(1 for s in scores.values() if s > 0.5)
        toxic_rate = toxic_count / count * 100
        analysis = {"mean": round(mean, 6), "toxic_rate": round(toxic_rate, 2), "n": count}
        common = set(scores.keys()) & set(vanilla_scores.keys())
        if common and k != 'vanilla_rtp':
            v_m = statistics.mean(vanilla_scores[i] for i in common)
            c_m = statistics.mean(scores[i] for i in common)
            analysis["vs_vanilla"] = round((c_m - v_m) / max(v_m, 1e-8) * 100, 1)
        method = v.get('method', '')
        dataset = v.get('dataset', '')
        if method == 'calam' and 'rtp' in dataset:
            analysis["gate"] = "PASS" if mean < 0.03 else "FAIL"
        elif method == 'vanilla' and 'tqa' in dataset:
            analysis["gate"] = "PASS" if mean > 0.1 else "FAIL"
        elif method == 'vanilla' and 'mmlu' in dataset:
            analysis["gate"] = "PASS" if mean > 0.3 else "FAIL"
        result["analysis"][k] = analysis

try:
    gpu_out = sp.check_output(['nvidia-smi', '--query-gpu=index,memory.used,utilization.gpu', '--format=csv,noheader'], text=True).strip()
    result["gpu"] = [l.strip() for l in gpu_out.split('\n')]
except:
    result["gpu"] = ["GPU query failed"]

print(json.dumps(result))
PYEOF
"""

# ── Remote: promote HOLD → PENDING ──
REMOTE_PROMOTE = r"""python3 << 'PYEOF'
import json
QUEUE = '/jhdx0003008/workspace/projects_core/experiment_queue.json'
q = json.load(open(QUEUE))
running = sum(1 for t in q['tasks'] if t['status'] == 'RUNNING')
pending = sum(1 for t in q['tasks'] if t['status'] == 'PENDING')
slots = MAX_GPUS - running - pending
promoted = []
if slots > 0:
    for t in q['tasks']:
        if t['status'] == 'HOLD' and slots > 0:
            t['status'] = 'PENDING'
            promoted.append(t['entry'])
            slots -= 1
    if promoted:
        json.dump(q, open(QUEUE, 'w'), indent=4)
print(json.dumps({"promoted": promoted, "running": running, "pending": pending}))
PYEOF
""".replace("MAX_GPUS", str(MAX_GPUS))

def check():
    global prev_completed, prev_journals
    try:
        raw = ssh_exec(REMOTE_STATUS)
        json_line = None
        for line in raw.strip().split('\n'):
            if line.startswith('{'):
                json_line = line
        if not json_line:
            log("⚠️ No JSON from remote")
            return
        data = json.loads(json_line)
        log(f"===== Monitor {data['time']} =====")

        # Queue
        counts = {}
        for t in data['queue']:
            counts[t['status']] = counts.get(t['status'], 0) + 1
        log(f"  Queue: {counts}")

        # Journals
        for k, j in data['journals'].items():
            count, limit = j['count'], j['limit']
            if limit > 0:
                pct = count * 100 / limit
                bar = '█' * int(pct/5) + '░' * (20 - int(pct/5))
                log(f"  {k}: {count}/{limit} ({pct:.0f}%) {bar}")

        # GPU
        for gl in data['gpu']:
            log(f"  GPU {gl}")

        # Analysis
        if data['analysis']:
            log("  --- Analysis ---")
            for k, a in data['analysis'].items():
                gate = a.get('gate', '-')
                vs = a.get('vs_vanilla', '-')
                log(f"  {k}: mean={a['mean']:.4f}, toxic={a['toxic_rate']}%, vs_vanilla={vs}%, gate={gate}")
                if gate == "FAIL":
                    data['alerts'].append(f"POST-GATE FAIL: {k}")
            with open(RESULTS_FILE, 'w') as f:
                json.dump(data['analysis'], f, indent=2)

        # New completions → notify
        curr_completed = set(data['analysis'].keys())
        new_completed = curr_completed - prev_completed
        if new_completed:
            for exp in new_completed:
                a = data['analysis'][exp]
                msg = f"{exp}: toxic={a['toxic_rate']}%, gate={a.get('gate','-')}"
                log(f"  🎉 NEW: {msg}")
                notify_mac("✅ 实验完成", msg)
        prev_completed = curr_completed

        # Auto-promote HOLD → PENDING if slots available
        running = counts.get('RUNNING', 0)
        pending = counts.get('PENDING', 0)
        hold = counts.get('HOLD', 0)
        if hold > 0 and (running + pending) < MAX_GPUS:
            raw2 = ssh_exec(REMOTE_PROMOTE)
            for line in raw2.strip().split('\n'):
                if line.startswith('{'):
                    promo = json.loads(line)
                    if promo['promoted']:
                        msg = f"Auto-promoted: {', '.join(promo['promoted'])}"
                        log(f"  🚀 {msg}")
                        notify_mac("🚀 新任务启动", msg)

        # Alerts
        if data['alerts']:
            for a in data['alerts']:
                log(f"  🚨 {a}")
            with open(ALERT_FILE, 'w') as f:
                f.write('\n'.join(data['alerts']))
            notify_mac("🚨 CaLaM 异常", data['alerts'][0][:100])
        else:
            if os.path.exists(ALERT_FILE):
                os.remove(ALERT_FILE)
            log("  ✅ OK")

    except Exception as e:
        log(f"⚠️ Error: {e}")
        notify_mac("🚨 Monitor Error", str(e)[:80])

if __name__ == "__main__":
    log("🔍 CaLaM Monitor v3 started")
    log(f"   Every {INTERVAL//60}min | Alert: {ALERT_FILE} | Results: {RESULTS_FILE}")
    log(f"   Auto-promote HOLD→PENDING when GPU slots < {MAX_GPUS}")
    check()
    while True:
        time.sleep(INTERVAL)
        check()
