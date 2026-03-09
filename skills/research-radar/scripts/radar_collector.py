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
    # 🚨 PREEMPTIVE SSoT SYNC 🚨
    # Force Node 02 to pull the latest radar_targets.json before reading. Guaranteed non-blocking.
    print("🔄 [Pre-Flight] Synchronizing latest SSoT Targets from Git (Non-blocking)...")
    try:
        env = os.environ.copy()
        env["GIT_TERMINAL_PROMPT"] = "0"
        # Use atomic autostash and force 'theirs' strategy to silently override any Node 02 local drift
        subprocess.run(["git", "pull", "--rebase", "--autostash", "-X", "theirs"], cwd=str(WORKSPACE_DIR), check=True, timeout=30, env=env)
    except subprocess.TimeoutExpired:
        print("⚠️ [Pre-Flight] Warning: Git pull TIMED OUT after 30s. Triggering abort and falling back.")
        subprocess.run(["git", "rebase", "--abort"], cwd=str(WORKSPACE_DIR), capture_output=True)
    except subprocess.CalledProcessError as e:
        print(f"⚠️ [Pre-Flight] Warning: Git pull FAILED. Triggering abort and falling back. Error: {e.stderr if e.stderr else e}")
        subprocess.run(["git", "rebase", "--abort"], cwd=str(WORKSPACE_DIR), capture_output=True)

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
    
    import re
    
    def extract_identifiers(text):
        # ArXiv ID format broadly: yymm.number or old style
        arxiv_ids = set(re.findall(r'(\d{4}\.\d{4,5})', text))
        urls = set(re.findall(r'(https?://[A-Za-z0-9\.\-\_\/\?\&\=\%]+)', text))
        return arxiv_ids, urls

    def filter_new_content(raw_text, engine_name):
        if not raw_text or "*Error" in raw_text:
            return raw_text, False
            
        a_ids, urls = extract_identifiers(raw_text)
        
        # If no identifiers found, we assume it's new (can't prove it's a duplicate)
        if not a_ids and not urls:
            return raw_text, True
            
        new_items_found = False
        # Check ArXiv
        for aid in a_ids:
            if aid not in seen_db['arxiv']:
                seen_db['arxiv'].append(aid)
                new_items_found = True
        
        # Check URLs
        for u in urls:
            if u not in seen_db['web_urls']:
                seen_db['web_urls'].append(u)
                new_items_found = True
                
        # If json from ArXiv, we could precisely filter, but for raw markdown, 
        # dropping the entire chunk if NO new items are found is the safest physical block.
        if not new_items_found:
            return "", False
            
        return raw_text, True

    for category, query in RADAR_KEYWORDS.items():
        print(f"  -> [Tri-Engine] Scraping raw data for: {category}")
        
        # Determine if this category should bypass strict AI4S top-venue filtering
        strict_venues = ["Nature", "Science", "ICLR", "NeurIPS", "ICML", "CVPR", "ICCV", "KDD", "Q1"]
        bypass_strict = any(keyword.lower() in category.lower() for keyword in ["Medical", "Safety", "NLP", "OrgGPT", "Society", "Game", "Math", "LifeScience", "Cancer", "Affective", "Embodied", "Education"])
        
        category_buffer = []
        
        # 1. ArXiv (Academic)
        print("     |_ arXiv...")
        arxiv_res = run_search_arxiv(query, max_results=5)
        arxiv_res, has_new_arxiv = filter_new_content(arxiv_res, "arxiv")
        if has_new_arxiv:
            category_buffer.append("### 📚 1. ArXiv (Academic)")
            category_buffer.append(arxiv_res)
        
        # 2. Tavily (Web/News)
        print("     |_ Tavily...")
        tavily_query = query
        if not bypass_strict:
            tavily_query += " (" + " OR ".join(strict_venues) + " OR Q2) recent breakthroughs AI"
        else:
            tavily_query += " recent breakthroughs"
            
        tavily_res = run_search_tavily(tavily_query, max_results=3)
        tavily_res, has_new_tavily = filter_new_content(tavily_res, "tavily")
        if has_new_tavily:
            category_buffer.append("### 🌐 2. Tavily (Web & Industry News)")
            category_buffer.append(tavily_res)
        
        # 3. Exa (Code/Neural)
        print("     |_ Exa...")
        exa_query = query
        if not bypass_strict:
            exa_query += " (" + " OR ".join(strict_venues) + ") github repo official code"
        else:
            exa_query += " github repo official code"
            
        exa_res = run_search_exa(exa_query, max_results=3)
        exa_res, has_new_exa = filter_new_content(exa_res, "exa")
        if has_new_exa:
            category_buffer.append("### 💻 3. Exa (Code & Neural Intel)")
            category_buffer.append(exa_res)
        
        if category_buffer:
            raw_content.append(f"## 📦 Raw Sector: {category}")
            raw_content.extend(category_buffer)
            raw_content.append("\n---\n")
        
        # 🛡️ Absolute Physical Rate Limit (Anti-Ban Armor)
        # Protects Node 02/05 from being blacklisted by arXiv/IEEE
        print("  -> [Anti-Ban] Sleeping for 15 seconds before next burst...")
        time.sleep(15)

    # === Omni-Scope Intelligence Integration ===
    OMNI_SECTORS = targets_data.get("omni_intel_sectors", {})
    if OMNI_SECTORS:
        raw_content.append(f"## 🏛️ Omni-Scope Intelligence (Policies, Crants, Deadlines)")
        for omni_cat, omni_query in OMNI_SECTORS.items():
            print(f"  -> [Omni-Scope] Scraping: {omni_cat}")
            raw_content.append(f"### 🎯 Sector: {omni_cat}")
            
            # For Policies and Grants, we rely heavily on Tavily to hit Gov/Funding sites
            tavily_res = run_search_tavily(omni_query, max_results=3)
            tavily_res, has_new_tavily = filter_new_content(tavily_res, "tavily")
            if has_new_tavily:
                raw_content.append("#### 🌐 Tavily (Web/Gov Intel)")
                raw_content.append(tavily_res)
                
            time.sleep(10)
            
    # === Institutional Blogs ===
    INST_BLOGS = targets_data.get("institutional_blogs", [])
    if INST_BLOGS:
        raw_content.append(f"## 📰 Institutional Top Blogs")
        print(f"  -> [Blogs] Sweeping Top AI Lab Blogs...")
        blog_query = " OR ".join([f"site:{b}" for b in INST_BLOGS]) + " latest news breakthrough AI"
        blog_res = run_search_tavily(blog_query, max_results=5)
        blog_res, has_new_blogs = filter_new_content(blog_res, "tavily")
        if has_new_blogs:
             raw_content.append("#### 🌐 Tavily (Blog Intel)")
             raw_content.append(blog_res)
        time.sleep(10)

    # === Reference List ===
    targets = targets_data
    if targets:
        print(f"  -> [Authoritative Check] Sweeping Top Labs & Scholars...")
        raw_content.append(f"## 🎓 Reference Top-Tier Targets")
        
        # Split large scholar lists to avoid shell command too long errors
        scholars = targets.get("top_scholars", [])
        if scholars:
            # Chunking scholars into groups of 10
            chunk_size = 10
            scholar_chunks = [scholars[i:i + chunk_size] for i in range(0, len(scholars), chunk_size)]
            
            for idx, chunk in enumerate(scholar_chunks):
                combined_scholars = " OR ".join(chunk)
                scholar_query = f"({combined_scholars}) New publications AI"
                sch_res = run_search_tavily(scholar_query, max_results=3)
                sch_res, has_new_sch = filter_new_content(sch_res, "tavily")
                if has_new_sch:
                    raw_content.append(f"### 🎓 Top Scholars Intel (Batch {idx+1})")
                    raw_content.append(sch_res)
                time.sleep(10)

    # === Asynchronous Feishu Inbox Processing ===
    FEISHU_INBOX_PATH = RAW_DATA_DIR / "_inbox.md"
    if FEISHU_INBOX_PATH.exists():
        print("  -> [Feishu Asynchronous Handoff] Processing Inbox...")
        raw_content.append(f"## 💬 Feishu Intercepted Intel (Asynchronous Handoff)")
        try:
            with open(FEISHU_INBOX_PATH, "r", encoding="utf-8") as f:
                inbox_text = f.read()
            
            # Extract all URLs from the markdown
            inbox_urls = set(re.findall(r'(https?://[A-Za-z0-9\.\-\_\/\?\&\=\%]+)', inbox_text))
            
            new_inbox_items = []
            for url in inbox_urls:
                # Check deduplication by simulating a raw text block containing the URL
                _, is_new = filter_new_content(url, "inbox_check")
                
                if is_new:
                    print(f"     |_ Extracting new Feishu URL: {url}")
                    raw_content.append(f"### 🔗 Link: {url}")
                    raw_content.append(f"*(This URL was intercepted from a live chat session via _inbox.md. The Analyzer will cross-reference this URL with the chat context.)*\n\n")
                    new_inbox_items.append(url)
                else:
                    print(f"     |_ [Skip] Feishu URL already processed: {url}")
                    
            if not new_inbox_items:
                raw_content.append("*No new intercepts found today.*")
                
        except Exception as e:
            print(f"     |_ [Error processing Feishu Inbox] {e}")

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
        # Use atomic autostash to silently override any Node 02 local drift before pushing
        subprocess.run(["git", "pull", "--rebase", "--autostash", "-X", "theirs"], cwd=str(WORKSPACE_DIR), check=True)
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
