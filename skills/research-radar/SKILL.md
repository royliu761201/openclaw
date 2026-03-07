---
name: research-radar
description: 24/7 Autonomous Research Radar for continuous tracking of academic frontiers.
metadata: { "openclaw": { "emoji": "📡", "requires": { "bins": ["python3"] } } }
---

# Research Radar Skill

An autonomous, cron-driven surveillance system utilizing `academic-search` to track cutting-edge research targets defined in the `05_RESEARCH_RADAR_PDCA.md` plan.

## Purpose

To eradicate manual literature monitoring. The radar automatically pulls down the latest scholarly works (via ArXiv) against a matrix of High-Value Keywords (Batch 2 mainlines and Ideas Radar extensions).

## Core Mechanisms

1. **The Pulse**: The daemon script (`radar_daemon.py`) runs quietly from cron.
2. **The Weapon**: Uses the pre-existing, L1 Constitution-compliant `academic-search` tool. No custom web scrapers are allowed.
3. **The Ledger**: Updates the daily intelligence reports into `workspace/docs/research_ideation/radar_reports/` and signals the `05_RESEARCH_RADAR_PDCA.md` board.

## Usage

Normally executed directly via cron:
```bash
python3 scripts/radar_daemon.py
```

To run a manual sweep and view output immediately:
```bash
python3 scripts/radar_daemon.py --manual
```
