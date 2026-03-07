#!/usr/bin/env python3
import os
import sys
import time
import subprocess
import datetime
from pathlib import Path

WORKSPACE_DIR = Path(os.path.expanduser("~/workspace"))
RAW_DATA_DIR = WORKSPACE_DIR / "docs" / "research_ideation" / "radar_raw_data"
ACADEMIC_SEARCH_PATH = os.path.expanduser("~/Documents/projects/openclaw/skills/academic-search/scripts/search_arxiv.py")
TAVILY_SEARCH_PATH = os.path.expanduser("~/Documents/projects/openclaw/skills/tavily-search/scripts/search.mjs")
EXA_SEARCH_PATH = os.path.expanduser("~/Documents/projects/openclaw/skills/exa-search/scripts/exa_search.py")

SEEN_INTEL_PATH = WORKSPACE_DIR / "docs" / "research_ideation" / "seen_intel.json"
TARGETS_LIST_PATH = WORKSPACE_DIR / "docs" / "research_ideation" / "radar_targets.json"

def load_targets():
    import json
    if TARGETS_LIST_PATH.exists():
        with open(TARGETS_LIST_PATH, "r") as f:
            return json.load(f)
    print("❌ Error: targets list not found at", TARGETS_LIST_PATH)
    sys.exit(1)

def load_seen_intel():
    import json
    if SEEN_INTEL_PATH.exists():
        with open(SEEN_INTEL_PATH, "r") as f:
            return json.load(f)
    return {"arxiv": [], "web_urls": []}

def save_seen_intel(data):
    import json
    with open(SEEN_INTEL_PATH, "w") as f:
        json.dump(data, f)

def run_search_arxiv(query: str, max_results: int = 5) -> str:
    try:
        result = subprocess.run(
            ["python3", ACADEMIC_SEARCH_PATH, "search", "--query", query, "--max_results", str(max_results), "--sort_by", "date"],
            capture_output=True, text=True, check=True
        )
        return result.stdout
    except subprocess.CalledProcessError:
        return f"*Error retrieving ArXiv results.*"
    except FileNotFoundError:
        return f"*Error: academic-search script not found.*"

def run_search_tavily(query: str, max_results: int = 3) -> str:
    try:
        result = subprocess.run(
            ["node", TAVILY_SEARCH_PATH, query, "-n", str(max_results)],
            capture_output=True, text=True, check=True
        )
        return result.stdout
    except subprocess.CalledProcessError:
        return f"*Error retrieving Tavily (Web) results.*"
    except FileNotFoundError:
        return f"*Error: tavily-search script not found.*"

def run_search_exa(query: str, max_results: int = 3) -> str:
    try:
        result = subprocess.run(
            ["python3", EXA_SEARCH_PATH, "web", query, "--num", str(max_results)],
            capture_output=True, text=True, check=True
        )
        return result.stdout
    except subprocess.CalledProcessError:
        return f"*Error retrieving Exa (Neural) results.*"
    except FileNotFoundError:
        return f"*Error: exa-search script not found.*"

def collect_raw_data():
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    raw_path = RAW_DATA_DIR / f"{today_str}_RAW.md"
    
    print(f"⛏️ Initiating Radar Raw Collection (Producer Mode) - {today_str}...")
    
    seen_db = load_seen_intel()
    targets_data = load_targets()
    RADAR_KEYWORDS = targets_data.get("radar_keywords", {})
    
    raw_content = [
        f"# ⛏️ Radar Raw Data: {today_str}",
        "> **Auto-harvested by Research-Radar (Collector)**\n"
    ]
    
    for category, query in RADAR_KEYWORDS.items():
        print(f"  -> [Tri-Engine] Scraping raw data for: {category}")
        
        raw_content.append(f"## 📦 Raw Sector: {category}")
        
        # 1. ArXiv (Academic)
        print("     |_ arXiv...")
        arxiv_res = run_search_arxiv(query, max_results=5)
        raw_content.append("### 📚 1. ArXiv (Academic)")
        raw_content.append(arxiv_res)
        
        # 2. Tavily (Web/News - Strictly Top Venues & CAS Q1/Q2)
        print("     |_ Tavily...")
        tavily_query = query + " (Nature OR Science OR ICLR OR NeurIPS OR ICML OR CVPR OR ICCV OR KDD OR Q1 OR Q2) recent breakthroughs AI"
        tavily_res = run_search_tavily(tavily_query, max_results=3)
        raw_content.append("### 🌐 2. Tavily (Web & Industry News)")
        raw_content.append(tavily_res)
        
        # 3. Exa (Code/Neural - Strictly Top Venues & CAS Q1/Q2)
        print("     |_ Exa...")
        exa_query = query + " (Nature OR Science OR ICLR OR NeurIPS OR ICML OR CVPR OR ICCV OR KDD OR Q1) github repo official code"
        exa_res = run_search_exa(exa_query, max_results=3)
        raw_content.append("### 💻 3. Exa (Code & Neural Intel)")
        raw_content.append(exa_res)
        
        # (Assuming the LLM Consumer later will handle the deduplicated IDs from the raw text, 
        # or we just let it fetch, but since this is raw bash output, full-text deduplication is left to Brain 
        # for semantic filtering, but we explicitly note it here).
        
        raw_content.append("\n---\n")
        
        # 🛡️ Absolute Physical Rate Limit (Anti-Ban Armor)
        # Protects Node 02/05 from being blacklisted by arXiv/IEEE
        print("  -> [Anti-Ban] Sleeping for 15 seconds before next burst...")
        time.sleep(15)

    # 4. Reference List (Authoritative Targets / 参考文献定标清单)
    import json
    if TARGETS_LIST_PATH.exists():
        with open(TARGETS_LIST_PATH, "r") as f:
            targets = json.load(f)
            print(f"  -> [Authoritative Check] Sweeping Top Labs & Scholars...")
            raw_content.append(f"## 🏛️ Reference Top-Tier Targets")
            
            combined_labs = " OR ".join(targets.get("top_institutions", []))
            if combined_labs:
                lab_query = f"({combined_labs}) Breakthroughs AI4S"
                raw_content.append("### 🧪 Top Institutions Intel")
                raw_content.append(run_search_tavily(lab_query, 3))
                time.sleep(10)
                
            combined_scholars = " OR ".join(targets.get("top_scholars", []))
            if combined_scholars:
                scholar_query = f"({combined_scholars}) New publications AI4S Nature Science"
                raw_content.append("### 🎓 Top Scholars Intel")
                raw_content.append(run_search_tavily(scholar_query, 3))
                time.sleep(10)

    save_seen_intel(seen_db)
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
    
    # Validation handled inside collect_raw_data, but kept sectors filtering out if needed.
    collect_raw_data()
    git_sync_workspace()
