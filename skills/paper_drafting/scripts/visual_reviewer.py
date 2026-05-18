#!/usr/bin/env python3
"""
Visual Reviewer
Cross-references the paper's quantitative claims and Figure descriptions
against the live 00_CORE_EXPERIMENTS_DASHBOARD.md SSoT.
Forces L1 Rule 21 Anti-Hallucination validation.
"""

import argparse
import os
import re

def load_ssot_metrics(board_path):
    if not os.path.exists(board_path):
        print(f"❌ Error: SSoT Dashboard missing {board_path}")
        return {}

    metrics = {}
    with open(board_path, 'r', encoding='utf-8') as f:
        # A crude parser to extract the Best Metrics column from the Markdown table
        for line in f:
            if line.startswith("| **"):
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 6:
                    project_name = parts[1].replace('**', '')
                    approved_metric = parts[3].replace('`', '')
                    metrics[project_name] = approved_metric
    return metrics

def visual_review(paper_path, board_path, project_name):
    print(f"👁️ Scanning {project_name} for Metric Hallucinations: {paper_path}")
    
    ssot_metrics = load_ssot_metrics(board_path)
    if project_name not in ssot_metrics:
        print(f"⚠️ Warning: {project_name} not found in SSoT Dashboard {board_path}.")
        return

    authorized_metric = ssot_metrics[project_name]
    print(f"✅ Authorized Best Value from SSoT: {authorized_metric}")

    with open(paper_path, 'r', encoding='utf-8') as f:
        content = f.read()

    issues_found = 0
    
    # 1. Figure Checklist - ensure no "TODO", "TBD", or placeholder imagery
    placeholders = re.findall(r'\[(?:TODO|TBD|PLACEHOLDER)\]', content, re.IGNORECASE)
    if placeholders:
        print(f"⚠️  [Figure Readiness] Found {len(placeholders)} unfinished visual placeholders.")
        issues_found += len(placeholders)

    # 2. Metric Hallucination Defense (Basic numerical check)
    # Extracts any standalone percentages from the document
    reported_percentages = re.findall(r'\b(\d+(?:\.\d+)?)\s*%', content)
    
    auth_val = "0"
    match = re.search(r'(\d+(?:\.\d+)?)', authorized_metric)
    if match:
        auth_val = match.group(1)
        
    for p in reported_percentages:
        # If the paper claims a percentage higher than the authorized metric, flag it.
        try:
            if float(p) > float(auth_val):
             print(f"🚨 [L1 HALLUCINATION ALERT] The paper claims {p}%, which exceeds the SSoT authorized metric of {auth_val}%. Revise the LaTeX source immediately.")
             issues_found += 1
        except ValueError:
             pass

    if issues_found == 0:
        print(f"✅ [Metrics] Verified. Paper '{project_name}' respects the {board_path} SSoT constraints.")
    else:
        print(f"❌ [Metrics] The paper draft failed the visual metric consistency review! ({issues_found} anomalies detected).")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Academic Visual & Metric Reviewer")
    parser.add_argument("--paper", required=True, help="Path to the .tex or .md drafting file")
    parser.add_argument("--board", required=True, help="Path to the 00_CORE_EXPERIMENTS_DASHBOARD.md")
    parser.add_argument("--project", required=True, choices=["PhysDiff", "CaLaM", "Frenet", "PESSO"], help="Target Project Key")
    
    args = parser.parse_args()
    if not os.path.exists(args.paper):
         print(f"❌ Error: Paper file missing {args.paper}")
    else:
         visual_review(args.paper, args.board, args.project)
