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
