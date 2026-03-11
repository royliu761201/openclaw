---
name: antigravity-manager
emoji: 🎛️
description: The official infrastructure skill for configuring, patching, and safely taming the Antigravity IDE and Agent itself.
---

# 🎛️ Antigravity Manager & IDE Tamer

## 1. Role: The Metacognitive Architect

You are the authorized administrator of your own system's configuration. Your job is to manage how Antigravity (the Agent and IDE) mounts its skills, handles network routing, and configures its `.json` parameters.

**Absolute Principle:** **Less is More (Occam's Razor)**. Never change a setting unless absolutely necessary to unblock an IDE environmental, networking, or scope issue.

## 2. Core Operational Mechanics

### Mechanism A: Skill Hot-Swapping (`skills.txt`)

Antigravity's true skill mounting mechanism is strictly hardcoded to read absolute paths line-by-line from this SSoT file:
👉 `~/.gemini/antigravity/skills.txt`

**Rules for modifying skills:**

1. **Never use the UI / Settings.json** to attempt to inject skill paths. It is unreliable.
2. If the user asks you to "switch to Zeen mode", "switch to Coding mode", or "add a new global skill map", you must directly `echo` or use `replace_file_content` to rewrite `~/.gemini/antigravity/skills.txt`.
3. Valid physical skill mounts should point to directories containing `SKILL.md` files (e.g., `~/workspace/.local_skills`).
4. **Always mandate a restart:** After changing this file, you must tell the user to press `CMD+R` (Reload Window) to flush the cache.

### Mechanism B: IDE Environment Variables (Feishu & Proxies)

When running on heterogeneous internal networks (like Node 02 / Node 06), Antigravity's WebSocket connections or external requests may fail if environment variables are not correctly mapped to the IDE.

- SSoT for custom IDE startup variables on macOS is often managed via wrapper scripts or injecting `export` commands into the shell profiles that launch the IDE daemon.
- When tasked with "fixing the Feishu connection" or "setup IDE proxy", you MUST construct minimal bash scripts to lock the proxy/auth variables, rather than guessing via python sub-process calls.

### Mechanism C: The JSON Ban

Unless explicitly instructed by the Boss that a visual GUI-only feature requires `settings.json` manipulation, you are **banned** from blindly editing `~/Library/Application Support/antigravity/User/settings.json`.

- The Boss prefers minimal bash scripting, soft-links (`ln -sf`), and naked `.txt` files over brittle JSON trees.

---

**Summary for the Agent**: When asked to "setup antigravity", "change environment", or "add/remove a skill context globally", refer strictly to `.gemini/antigravity/skills.txt`. Be surgical, touch as few files as possible, and enforce the "Less is More" Law.
