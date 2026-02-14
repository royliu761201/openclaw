---
name: browser
description: Automate web browser interactions using **Stagehand** and **Google Gemini**. Navigate pages, extract data, and interact with web elements using natural language.
allowed-tools: Bash
---

# Browser Automation Skill

This skill allows agents to control a headless Chrome browser to browse the web, extract structured data, and perform actions.

## 🚀 Key Features
- **Powered by Gemini**: Uses your global `google/gemini-2.5-flash-lite` (or fallback) configuration.
- **Natural Language Actions**: "Click the login button", "Type 'hello' into the search bar".
- **Structured Extraction**: Extract data into JSON using simple schema definitions.
- **Global Availability**: Installed globally for all OpenClaw agents on this machine.

## 🛠️ Configuration

No per-agent configuration is required. The skill uses your global OpenClaw settings:
- **Model**: Defined in `~/.openclaw/openclaw.json` (Default: `google/gemini-2.5-flash-lite`).
- **API Key**: `GEMINI_API_KEY` in `~/.openclaw/.env`.

## 💻 Commands

### 1. Navigate
Open a URL.
```bash
browser navigate <url>
# Example:
browser navigate https://news.ycombinator.com
```

### 2. Act
Perform an interaction on the current page.
```bash
browser act "<natural language instruction>"
# Example:
browser act "click on the first article"
```

### 3. Extract
Extract structured data from the page. Supports a simplified schema syntax: `key:type,key2:type2`.
```bash
browser extract "<instruction>" "<schema>"
# Example:
browser extract "get the top 3 stories" "title:string,points:number,url:string"
```

### 4. Observe
Get a list of interactable elements related to an instruction.
```bash
browser observe "<instruction>"
# Example:
browser observe "buttons specifically related to login"
```

### 5. Screenshot
(Coming Soon: Currently disabled for V3 API compatibility)
```bash
browser screenshot
```

## ❓ FAQ

**Q: Is this skill available for all agents?**
A: **Yes.** Once installed in the `skills/` directory, any OpenClaw agent can invoke it via the `browser` command (or `npx tsx browser-cli.ts`). Use the `task.md` or `implementation_plan.md` of a specific agent to instruct it to use this skill.

**Q: Do I need separate config for each agent?**
A: **No.** The skill reads from the central `~/.openclaw` configuration. All agents share this browser instance and configuration.
