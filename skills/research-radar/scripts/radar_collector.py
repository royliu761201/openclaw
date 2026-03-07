#!/usr/bin/env python3
import os
import sys
import time
import subprocess
import datetime
from pathlib import Path

RADAR_KEYWORDS = {
    "CaLaM": "Topological Data Analysis OR Topological Analysis",
    "Frenet": "SE(3) Equivariance OR Hamiltonian Neural Networks",
    "PESSO": "Spectral FlashAttention OR Neural Operator",
    "PhysDiff": "Energy-Conserving Quantization OR Physics-Informed",
    "RLPF": "Reinforcement Learning Fluid OR PDE RL Reward",
    "Composition": "Neural Operator Composition OR Zero-shot Multiphysics",
    "MultiAgent": "Multi-Agent Math Reasoning OR LLM Arbitrage"
}

WORKSPACE_DIR = Path(os.path.expanduser("~/workspace"))
RAW_DATA_DIR = WORKSPACE_DIR / "docs" / "research_ideation" / "radar_raw_data"
ACADEMIC_SEARCH_PATH = os.path.expanduser("~/Documents/projects/openclaw/skills/academic-search/scripts/search_arxiv.py")

def run_search(query: str, max_results: int = 5) -> str:
    try:
        result = subprocess.run(
            ["python3", ACADEMIC_SEARCH_PATH, "search", "--query", query, "--max_results", str(max_results)],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"*Error retrieving results for this query.*"
    except FileNotFoundError:
        return f"*Error: academic-search script not found.*"

def collect_raw_data():
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    raw_path = RAW_DATA_DIR / f"{today_str}_RAW.md"
    
    print(f"⛏️ Initiating Radar Raw Collection (Producer Mode) - {today_str}...")
    
    raw_content = [
        f"# ⛏️ Radar Raw Data: {today_str}",
        "> **Auto-harvested by Research-Radar (Collector)**\n"
    ]
    
    for category, query in RADAR_KEYWORDS.items():
        print(f"  -> Scraping raw arXiv abstracts for: {category}")
        raw_results = run_search(query, max_results=5)
        raw_content.append(f"## 📦 Raw Sector: {category}")
        raw_content.append(raw_results)
        raw_content.append("\n---\n")
        
        # 🛡️ Absolute Physical Rate Limit (Anti-Ban Armor)
        # Protects Node 02/05 from being blacklisted by arXiv/IEEE
        print("  -> [Anti-Ban] Sleeping for 15 seconds before next burst...")
        time.sleep(15)

    with open(raw_path, "w") as f:
        f.write("\n".join(raw_content))
    
    print(f"✅ Collection complete. Raw data written to {raw_path}")

def git_sync_workspace():
    print("🔄 Synchronizing Raw Data to Global Workspace (Git-as-SSoT)...")
    try:
        subprocess.run(["git", "add", str(RAW_DATA_DIR)], cwd=str(WORKSPACE_DIR), check=True)
        status = subprocess.run(["git", "status", "--porcelain"], cwd=str(WORKSPACE_DIR), capture_output=True, text=True)
        if not status.stdout.strip():
            print("   [Skip] No new files to commit.")
            return
        subprocess.run(["git", "commit", "-m", "[Auto] Radar Raw Data Collection"], cwd=str(WORKSPACE_DIR), check=True)
        subprocess.run(["git", "pull", "--rebase"], cwd=str(WORKSPACE_DIR), check=True)
        subprocess.run(["git", "push"], cwd=str(WORKSPACE_DIR), check=True)
        print("✅ Git Sync Complete. Pure raw data deposited to SSoT.")
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Git Sync Warning: {e}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Radar Raw Data Collector (Producer)")
    parser.add_argument("--sectors", nargs="+", help="Specific sectors to scan", default=[])
    args = parser.parse_args()
    
    if args.sectors:
        RADAR_KEYWORDS = {k: v for k, v in RADAR_KEYWORDS.items() if k in args.sectors}
        if not RADAR_KEYWORDS:
            print(f"❌ Error: Provided sectors {args.sectors} do not exist in the radar registry.")
            sys.exit(1)
            
    collect_raw_data()
    git_sync_workspace()
