#!/usr/bin/env python3
"""
The Ironclad Experiment Audit Script (The Telemetry-to-LaTeX Guard)
Runs deterministic checks against the experimental SOP and Constitution.
"""
import os
import glob
import re
import sys

# Constants
WORKSPACE = os.path.expanduser('~/workspace')
PDCA_DIR = os.path.join(WORKSPACE, 'docs', 'projects_pdca')
PROJECTS_DIR = os.path.join(WORKSPACE, 'projects')
PROJECTS_CORE_DIR = os.path.join(WORKSPACE, 'projects_core')
PAPERS_DIR = os.path.join(WORKSPACE, 'papers')

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"

violations = 0

def check_pdca_compliance():
    global violations
    print(f"\n{YELLOW}[1/4] Auditing PDCA Structural Rigidity...{RESET}")
    for filepath in glob.glob(os.path.join(PDCA_DIR, '*.md')):
        basename = os.path.basename(filepath)
        if '00_' in basename: continue # Skip dashboards
        if not re.match(r'0[1-4]_', basename): continue # Only audit the CORE 4 PDCAs
        
        with open(filepath, 'r') as f:
            content = f.read()
            
            # Check Iron Triangle
            if '矩阵 1' not in content and '矩阵 A' not in content and 'Baseline' not in content:
                print(f"  {RED}[FAILED]{RESET} {basename} lacks a rigorous Baseline (Showdown) matrix.")
                violations += 1
            if '消融' not in content and 'Ablation' not in content and '矩阵 2' not in content:
                print(f"  {RED}[FAILED]{RESET} {basename} lacks an Ablation matrix. Are you omitting modules?")
                violations += 1
                
            # Check asset linking
            if 'link to src' in content or '[HuggingFace / Kaggle' in content:
                print(f"  {RED}[FAILED]{RESET} {basename} has unpopulated template links (Dead-link Sniffer).")
                violations += 1

def check_telemetry_bloat():
    global violations
    print(f"\n{YELLOW}[2/4] Auditing W&B Telemetry Bloat...{RESET}")
    search_dirs = [PROJECTS_DIR, PROJECTS_CORE_DIR]
    
    for base_dir in search_dirs:
        for root, dirs, files in os.walk(base_dir):
            if '_zombie_' in root or 'venv' in root or '.git' in root: continue
            for file in files:
                if not file.endswith('.py'): continue
                filepath = os.path.join(root, file)
                
                try:
                    with open(filepath, 'r') as f:
                        lines = f.readlines()
                        content_str = "".join(lines)
                        for i, line in enumerate(lines):
                            if 'wandb.init' in line and not line.strip().startswith('#'):
                                if 'WANDB_DIR' not in content_str and 'os.environ' not in content_str:
                                    print(f"  {RED}[WARNING]{RESET} {filepath}:{i} initializes W&B without explicit WANDB_DIR isolation. Ensure wrapper scripts export WANDB_DIR=./results.")
                                    violations += 1
                except Exception:
                    pass

def check_kaggle_ban():
    global violations
    print(f"\n{YELLOW}[3/4] Auditing Kaggle Local Fast-Pull Ban...{RESET}")
    search_dirs = [PROJECTS_DIR, PROJECTS_CORE_DIR]
    
    for base_dir in search_dirs:
        for root, dirs, files in os.walk(base_dir):
            if '_zombie_' in root or 'venv' in root or '.git' in root: continue
            for file in files:
                if file.endswith('.py') or file.endswith('.sh'):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r') as f:
                            content = f.read()
                            if 'kaggle datasets download' in content or 'kaggle.api.dataset_download_files' in content:
                                print(f"  {RED}[FAILED]{RESET} {filepath} contains banned direct Kaggle pulls. Use 'intel-fetch' or Node 05 Proxy.")
                                violations += 1
                    except Exception:
                        pass

def check_figure_consistency():
    global violations
    print(f"\n{YELLOW}[4/4] Auditing Telemetry-to-LaTeX Hardlinks...{RESET}")
    if not os.path.exists(PAPERS_DIR):
        print(f"  {YELLOW}[SKIP]{RESET} Paper directory not found.")
        return
        
    for root, dirs, files in os.walk(PAPERS_DIR):
        if 'figures' in root.split(os.sep):
            for file in files:
                if file.endswith('.pdf') or file.endswith('.png'):
                    asset_path = os.path.join(root, file)
                    basename = os.path.splitext(file)[0]
                    # Check if a generator script exists
                    generator_script = f"{basename}_generator.py"
                    script_dir = os.path.join(root, 'scripts')
                    if not os.path.exists(os.path.join(script_dir, generator_script)) and not os.path.exists(os.path.join(root, generator_script)):
                        print(f"  {RED}[FAILED]{RESET} Figure {file} lacks an automated plotting script ({generator_script}). Manual plotting is banned.")
                        violations += 1

if __name__ == '__main__':
    print("==================================================")
    print("Initiating OpenClaw Experiment Fortification Audit")
    print("==================================================")
    
    check_pdca_compliance()
    check_telemetry_bloat()
    check_kaggle_ban()
    check_figure_consistency()
    
    print("\n==================================================")
    if violations > 0:
        print(f"{RED}[AUDIT FAILED]{RESET} Found {violations} SOP violations. Fix them to proceed.")
        sys.exit(1)
    else:
        print(f"{GREEN}[AUDIT PASSED]{RESET} All experiment domains comply with the OpenClaw SSoT.")
        sys.exit(0)
