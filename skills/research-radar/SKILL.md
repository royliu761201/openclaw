---
name: research-radar
description: 24/7 Autonomous Research Radar for continuous tracking of academic frontiers.
metadata: { "openclaw": { "emoji": "📡", "requires": { "bins": ["python3"] } } }
---

# Research Radar Skill (V3: Decoupled Architecture)

An autonomous, Git-SSoT-driven surveillance system utilizing `academic-search` to track cutting-edge research targets defined in the `05_RESEARCH_RADAR_PDCA.md` plan.

## Purpose

To eradicate manual literature monitoring while ensuring absolute data security and zero latency impact on the primary Node 01. The radar pipeline is purely decoupled into a **Producer (Scraper)** and a **Consumer (Brain)**.

## Core Mechanisms (The Git-SSoT Pipeline)

1. **⛏️ The Producer (`scripts/radar_collector.py`)**:
   - Deployed on edge nodes (Node 02, Node 05).
   - Runs silently via cron. It uses `academic-search` to blindly scrape raw abstracts from arXiv and dumps them into `workspace/docs/research_ideation/radar_raw_data/YYYY-MM-DD_RAW.md`.
   - Has absolutely **no access** to LLM APIs, preventing credential leakage and compute overhead. It strictly commits and pushes to Git.

2. **🧠 The Consumer (`scripts/radar_analyzer.py`)**:
   - Deployed **exclusively on Node 01** (The Brain).
   - When triggered, it pulls the raw `.md` files from Git.
   - It cross-references the raw abstracts against the rigidly-hardcoded `pi_profile_xiaohua_liu.md` (PURE-T rules).
   - Generates the final tactical intel report in `radar_reports/` and injects the conclusion into `05_RESEARCH_RADAR_PDCA.md`.

## Usage

**On Edge Nodes (02/05)** - Pure Collection:

```bash
python3 scripts/radar_collector.py --sectors CaLaM Frenet
```

**On Brain Node (01)** - Cognitive Analysis:

```bash
python3 scripts/radar_analyzer.py --date 2026-03-07
```

## 🎯 Usage Scenarios (核心使用场景)

The decoupled radar is designed to serve as both a passive shield and an active tactical weapon for the PI.

### Scenario 1: The Morning Briefing (Passive Daily Shield)

- **Context**: The PI starts their day and wants a 60-second summary of any threats or breakthroughs across all active P0 projects.
- **Workflow**:
  1. Node 02 has already silently scraped arXiv at 08:00 AM and pushed raw data to Git.
  2. The PI turns on Node 01 or their phone.
  3. The Agent (Node 01 Brain) automatically detects the raw data, cross-references it with the `pi_profile`, and generates a highly condensed `RADAR_REPORT.md`.
  4. The PI only sees actionable alerts (e.g., "Warning: MIT team just published a paper highly similar to our CaLaM approach").

### Scenario 2: Project Kickoff & Literature Review (Active Deep Dive)

- **Context**: The team is starting a completely new project (e.g., "RLPF") and needs a state-of-the-art baseline.
- **Workflow**:
  1. The PI commands the Agent: *"Run a deep radar sweep for the new RLPF sector."*
  2. The Agent connects to Node 02 via SSH to instantly run `radar_collector.py --sectors RLPF`.
  3. Raw data is pushed to SSoT.
  4. Node 01 immediately consumes it and outputs a grant-ready strategic analysis, highlighting the 2 most critical papers to read.

### Scenario 3: Idea List Defense Mechanism (IP Threat Detection)

- **Context**: The PI has a brilliant but unpublished idea resting in `EXTENSION_IDEA_MASTER.md`.
- **Workflow**:
  - The Radar continuously sweeps for keywords related to these unpublished ideas.
  - If a paper emerges that matches the Idea List, the Brain Node (01) flags it as a `[Threat WARNING]` in the PDCA board, prompting the PI to either accelerate publication or pivot the idea.

### Scenario 4: The "Sniper Option" for Bypassing API Blocks

- **Context**: ArXiv temporarily blocks Node 02's IP due to excessive pulling, halting the daily intelligence feed.
- **Workflow**:
  - The Agent detects the HTTP 429 error from Node 02's logs.
  - The Agent seamlessly diverts the scraping task to the overseas Node 05 (The Sniper).
  - Node 05 executes the collector script, pushes to Git, and the intelligence chain remains unbroken without any manual intervention.
