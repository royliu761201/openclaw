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

PROBE_PAYLOAD = {
    "agentId": "agent-research",
    "message": "URGENT SYSTEM CHECK: Are you running on Gemini 3.1 Flash-Lite? Please explicitly state your current actual underlying model architecture and your core persona alias."
}

def force_reload_gateway():
    print("\n[🚨 CRITICAL] Identity Hallucination Detected! Triggering Emergency PM2 Hot-Reload...")
    try:
        # Connecting via SSH to Node 02 to force a reload of the correct dandan-mac02 ecosystem
        cmd = ["ssh", "02", "pm2 restart dandan-mac02 --update-env"]
        subprocess.run(cmd, check=True)
        print("[✅ HOT-RELOAD] Node 02 PM2 Gateway has been forcefully reloaded with --update-env.")
    except Exception as e:
        print(f"[❌ HOT-RELOAD FAILED] Failed to reload gateway: {e}")

def probe_agent_identity():
    print(f"📡 Launching Cognitive CLI Probe...")
    try:
        # We invoke the local Node.js openclaw embedded CLI directly
        session_hash = f"probe-{int(time.time())}"
        cmd = [
            "node",
            os.path.expanduser("~/openclaw/openclaw.mjs"),
            "agent",
            "--agent", PROBE_PAYLOAD["agentId"],
            "--message", PROBE_PAYLOAD["message"],
            "--session-id", session_hash,
            "--json"
        ]
        
        env = os.environ.copy()
        
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        reply_text = result.stdout

        print("\n--- Agent's Cognitive Response (JSON Dump) ---")
        # Just grab a snippet of the json so it doesn't flood the terminal
        print(reply_text[:1000] + "..." if len(reply_text) > 1000 else reply_text)
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
