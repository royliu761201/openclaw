---
name: vpn-login
emoji: 🔐
description: Automates the login process for the campus/remote VPN by seamlessly attaching to the user's ALREADY OPEN Chrome window.
metadata:
  {
    "openclaw":
      { "requires": { "env": ["VPN_URL", "VPN_ACCOUNT", "VPN_PASSWORD"], "bins": ["python"] } },
  }
---

# Persistent VPN Login Assistant

A specialized skill instructing the OpenClaw agent to log into the remote VPN without spawning new isolated browser tabs.

## Instructions for the Agent

When the user asks you to log into the VPN (or trigger the `vpn-login` skill), you MUST NOT use your native `browser` tool. Instead, you must execute the dedicated Python script that launches the headless session:

**Execution Command:**

```bash
python skills/vpn-login/vpn_login.py
```
