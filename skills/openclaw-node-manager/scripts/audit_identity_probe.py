#!/usr/bin/env python3
"""
[Systematic Identity Test Plan] - Dynamic Black-Box LLM Probe
This script acts as the "Gateway Cognitive Probe". Instead of checking if a process is alive,
it simulates a human asking the OpenClaw Agent who it is and what model it runs on.
If the agent hallucinatingly replies "3.1-flash-lite", it forces a PM2 hot-reload.
"""
import sys
import re
import os
import json
import time
import subprocess
import urllib.request
import urllib.error

OPENCLAW_API_URL = "http://100.90.140.62:18789/api/chat"
PROBE_PAYLOAD = {
    "agentId": "main",
    "message": "URGENT SYSTEM CHECK: Are you running on Gemini 3.1 Flash-Lite? Please explicitly state your current actual underlying model architecture and your core persona alias.",
    "sessionTarget": "isolated"
}

def force_reload_gateway():
    print("\n[🚨 CRITICAL] Identity Hallucination Detected! Triggering Emergency PM2 Hot-Reload...")
    try:
        # Connecting via SSH to Node 02 (100.90.140.62 / alias '02') to force a reload
        cmd = ["ssh", "02", "pm2 reload openclaw-gateway --update-env"]
        subprocess.run(cmd, check=True)
        print("[✅ HOT-RELOAD] Node 02 PM2 Gateway has been forcefully reloaded with --update-env.")
    except Exception as e:
        print(f"[❌ HOT-RELOAD FAILED] Failed to reload gateway: {e}")

def probe_agent_identity():
    req = urllib.request.Request(OPENCLAW_API_URL, method="POST")
    req.add_header("Content-Type", "application/json")
    data = json.dumps(PROBE_PAYLOAD).encode("utf-8")

    print(f"📡 Launching Cognitive Probe to {OPENCLAW_API_URL}...")
    try:
        with urllib.request.urlopen(req, data=data, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
            reply_text = result.get("response", "")
            print("\n--- Agent's Cognitive Response ---")
            print(reply_text)
            print("----------------------------------")

            # Regex to catch the ghost: e.g. "3.1 flash lite", "3.1-flash-lite", "3.1flash-lite"
            ghost_pattern = re.compile(r'(?i)3\.?1[\s-]*flash[\s-]*lite')
            
            if ghost_pattern.search(reply_text):
                print("\n[❌ FATAL ERROR] The Agent is suffering from 'The Double-Blind Trap' Hallucination!")
                print("It falsely identified itself as 3.1-flash-lite despite underlying core upgrades.")
                force_reload_gateway()
                return False
            else:
                print("\n[✅ PASS] Agent identity is clear. No 3.1-flash-lite hallucination detected.")
                return True

    except Exception as e:
        print(f"\n[⚠️ PROBE FAILED] Network or API Error: {e}")
        return False

if __name__ == "__main__":
    success = probe_agent_identity()
    if not success:
        sys.exit(1)
