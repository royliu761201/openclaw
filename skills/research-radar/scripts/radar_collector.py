#!/usr/bin/env python3
import os
import sys
import time
import subprocess
import datetime
from pathlib import Path

import shutil
import re

def load_openclaw_env():
    # Cron environments are absolutely bare. We explicitly parse the Node's SSoT env file.
    env_file = Path(os.path.expanduser("~/.openclaw_env"))
    if env_file.exists():
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("export "):
                    parts = line[7:].split("=", 1)
                    if len(parts) == 2:
                        key, val = parts[0].strip(), parts[1].strip()
                        # Remove bounding quotes
                        val = re.sub(r'^["\']|["\']$', '', val)
                        os.environ[key] = val

load_openclaw_env()

# 🛡️ FAIL-EARLY: Pre-flight check for Engine API Keys
missing_keys = [k for k in ["TAVILY_API_KEY", "EXA_API_KEY"] if not os.environ.get(k)]
if missing_keys:
    print(f"❌ FATAL [Fail-Early]: Missing API keys for radar engines: {missing_keys}. Check ~/.openclaw_env.")
    sys.exit(1)

WORKSPACE_DIR = Path(os.path.expanduser("~/workspace"))
RAW_DATA_DIR = WORKSPACE_DIR / "docs" / "research_ideation" / "radar_raw_data"
ACADEMIC_SEARCH_PATH = os.path.expanduser("~/openclaw/skills/academic-search/scripts/search_arxiv.py")
TAVILY_SEARCH_PATH = os.path.expanduser("~/openclaw/skills/tavily-search/scripts/search.mjs")
EXA_SEARCH_PATH = os.path.expanduser("~/openclaw/skills/exa-search/scripts/exa_search.py")

# Resolve node binary for cron execution
NODE_BIN = shutil.which("node")
if not NODE_BIN:
    for path in ["/opt/homebrew/bin/node", "/usr/local/bin/node"]:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            NODE_BIN = path
            break
if not NODE_BIN:
    print("❌ FATAL [Fail-Early]: 'node' binary not found. Research Radar cannot execute Tavily.")
    sys.exit(1)

# SSoT ONLY: Use the python interpreter that invoked us
PYTHON_BIN = sys.executable

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
            [PYTHON_BIN, ACADEMIC_SEARCH_PATH, "search", "--query", query, "--max_results", str(max_results), "--sort_by", "date"],
            capture_output=True, text=True, check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"*Error retrieving ArXiv results. Returncode: {e.returncode}, Stderr: {e.stderr}*"
    except Exception as e:
        return f"*Error: academic-search script issue -> {e}*"

def run_search_tavily(query: str, max_results: int = 3) -> str:
    try:
        result = subprocess.run(
            [NODE_BIN, TAVILY_SEARCH_PATH, query, "-n", str(max_results)],
            capture_output=True, text=True, check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"*Error retrieving Tavily (Web) results. Returncode: {e.returncode}, Stderr: {e.stderr}*"
    except Exception as e:
        return f"*Error: tavily-search script issue -> {e}*"

def run_search_exa(query: str, max_results: int = 3) -> str:
    try:
        result = subprocess.run(
            [PYTHON_BIN, EXA_SEARCH_PATH, "web", query, "--num", str(max_results)],
            capture_output=True, text=True, check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"*Error retrieving Exa (Neural) results. Returncode: {e.returncode}, Stderr: {e.stderr}*"
    except Exception as e:
        return f"*Error: exa-search script issue -> {e}*"

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
    buffer_path = RAW_DATA_DIR / f"{today_str}_BUFFER.md"
    
    print(f"⛏️ Initiating Radar Raw Collection (Producer Mode) - {today_str}...")
    
    seen_db = load_seen_intel()
    targets_data = load_targets()
    RADAR_KEYWORDS = targets_data.get("radar_keywords", {})
    
    raw_content = [
        f"# ⛏️ Radar High-Fidelity Data: {today_str}",
        "> **Auto-harvested by Research-Radar (Collector)**\n"
    ]
    
    buffer_content = [
        f"# 🗑️ Radar Low-Fi Buffer: {today_str}",
        "> **Contains ALL raw intercepts (Bypassed V8 Quality Filters). Retained for 3 days.**\n"
    ]
    
    import re
    
    def extract_identifiers(text):
        # ArXiv ID format broadly: yymm.number or old style
        arxiv_ids = set(re.findall(r'(\d{4}\.\d{4,5})', text))
        urls = set(re.findall(r'(https?://[A-Za-z0-9\.\-\_\/\?\&\=\%]+)', text))
        return arxiv_ids, urls

    def filter_new_content(raw_text, engine_name):
        if not raw_text or "*Error" in raw_text:
            error_msg = f"> 🚫 **FATAL: ENGINE OFFLINE ({engine_name.upper()})**. Trace: {raw_text.strip() if raw_text else 'Empty output'}"
            return error_msg, True, error_msg # Force it through to High-Fidelity buffer so Boss sees it
            
        a_ids, urls = extract_identifiers(raw_text)
        
        # If no identifiers found, we assume it's new (can't prove it's a duplicate)
        if not a_ids and not urls:
            return raw_text, True, raw_text
            
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
                
        # [V9 EVOLUTION]: Relax front-line filtering. 
        # Even if we think it's a duplicate, we let the Swarm (Dandan) decide.
        # We only mark it as "not new" to avoid appending it as a fresh High-Fidelity item
        # if and only if EVERY identifier in the text is old. But actually, to pass 80% through,
        # we will force `new_items_found = True` for Non-ArXiv sources to ensure high recall.
        
        if engine_name != "arxiv":
            new_items_found = True  # Let Dandan do the Triage for Web/News/Exa
            
        if not new_items_found:
            return "", False, raw_text # Return raw_text for the buffer even if duplicate
            
        return raw_text, True, raw_text


    for category, query in RADAR_KEYWORDS.items():
        print(f"  -> [Tri-Engine] Scraping raw data for: {category}")
        
        # Determine if this category should bypass strict AI4S top-venue filtering
        strict_venues = ["Nature", "Science", "ICLR", "NeurIPS", "ICML", "CVPR", "ICCV", "KDD", "Q1"]
        bypass_strict = any(keyword.lower() in category.lower() for keyword in ["Medical", "Safety", "NLP", "OrgGPT", "Society", "Game", "Math", "LifeScience", "Cancer", "Affective", "Embodied", "Education"])
        
        category_buffer = []
        category_low_fi_buffer = []
        
        # 1. ArXiv (Academic)
        print("     |_ arXiv...")
        arxiv_res = run_search_arxiv(query, max_results=5)
        arxiv_res, has_new_arxiv, arxiv_raw = filter_new_content(arxiv_res, "arxiv")
        if has_new_arxiv:
            category_buffer.append("### 📚 1. ArXiv (Academic)")
            category_buffer.append(arxiv_res)
        category_low_fi_buffer.append("### 📚 1. ArXiv (Academic) [UNFILTERED]")
        category_low_fi_buffer.append(arxiv_raw)
        
        # 2. Tavily (Web/News)
        print("     |_ Tavily...")
        tavily_query = query
        if not bypass_strict:
            tavily_query += " (" + " OR ".join(strict_venues) + " OR Q2) recent breakthroughs AI"
        else:
            tavily_query += " recent breakthroughs"
            
        tavily_res = run_search_tavily(tavily_query, max_results=3)
        tavily_res, has_new_tavily, tavily_raw = filter_new_content(tavily_res, "tavily")
        if has_new_tavily:
            category_buffer.append("### 🌐 2. Tavily (Web & Industry News)")
            category_buffer.append(tavily_res)
        category_low_fi_buffer.append("### 🌐 2. Tavily (Web & Industry News) [UNFILTERED]")
        category_low_fi_buffer.append(tavily_raw)
        
        # 3. Exa (Code/Neural)
        print("     |_ Exa...")
        exa_query = query
        if not bypass_strict:
            exa_query += " (" + " OR ".join(strict_venues) + ") github repo official code"
        else:
            exa_query += " github repo official code"
            
        exa_res = run_search_exa(exa_query, max_results=3)
        exa_res, has_new_exa, exa_raw = filter_new_content(exa_res, "exa")
        if has_new_exa:
            category_buffer.append("### 💻 3. Exa (Code & Neural Intel)")
            category_buffer.append(exa_res)
        category_low_fi_buffer.append("### 💻 3. Exa (Code & Neural Intel) [UNFILTERED]")
        category_low_fi_buffer.append(exa_raw)
        
        if category_buffer:
            raw_content.append(f"## 📦 Raw Sector: {category}")
            raw_content.extend(category_buffer)
            raw_content.append("\n---\n")
            
        if category_low_fi_buffer:
            buffer_content.append(f"## 📦 Buffer Sector: {category}")
            buffer_content.extend(category_low_fi_buffer)
            buffer_content.append("\n---\n")
        
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
            tavily_res, has_new_tavily, tavily_raw = filter_new_content(tavily_res, "tavily")
            if has_new_tavily:
                raw_content.append("#### 🌐 Tavily (Web/Gov Intel)")
                raw_content.append(tavily_res)
            buffer_content.append("#### 🌐 Tavily (Web/Gov Intel) [UNFILTERED]")
            buffer_content.append(tavily_raw)
                
            time.sleep(10)
            
    # === Institutional Blogs ===
    INST_BLOGS = targets_data.get("institutional_blogs", [])
    if INST_BLOGS:
        raw_content.append(f"## 📰 Institutional Top Blogs")
        print(f"  -> [Blogs] Sweeping Top AI Lab Blogs...")
        blog_query = " OR ".join([f"site:{b}" for b in INST_BLOGS]) + " latest news breakthrough AI"
        blog_res = run_search_tavily(blog_query, max_results=5)
        blog_res, has_new_blogs, blog_raw = filter_new_content(blog_res, "tavily")
        if has_new_blogs:
             raw_content.append("#### 🌐 Tavily (Blog Intel)")
             raw_content.append(blog_res)
        buffer_content.append("#### 🌐 Tavily (Blog Intel) [UNFILTERED]")
        buffer_content.append(blog_raw)
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
                sch_res, has_new_sch, sch_raw = filter_new_content(sch_res, "tavily")
                if has_new_sch:
                    raw_content.append(f"### 🎓 Top Scholars Intel (Batch {idx+1})")
                    raw_content.append(sch_res)
                buffer_content.append(f"### 🎓 Top Scholars Intel (Batch {idx+1}) [UNFILTERED]")
                buffer_content.append(sch_raw)
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
                _, is_new, raw_url = filter_new_content(url, "inbox_check")
                
                if is_new:
                    # 🐞 [BUGFIX]: We must actually save it to the database so it's not processed forever tomorrow
                    seen_db['web_urls'].append(url)
                    
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
    with open(buffer_path, "w") as f:
        f.write("\n".join(buffer_content))
    
    # 🧹 Execute Scavenger Cleanup Logic (The 3-Day TTL Buffer)
    print("🧹 [Cleanup] Executing 3-Day TTL Physical Scavenger on Buffer Files...")
    now = time.time()
    deleted_count = 0
    for f in RAW_DATA_DIR.glob("*_BUFFER.md"):
        # Delete if older than 3 days (3 * 24 * 60 * 60 = 259200 seconds)
        if f.is_file() and f.stat().st_mtime < now - 259200:
            print(f"   |_ 🗑️ Purging expired buffer file: {f.name}")
            try:
                f.unlink()
                deleted_count += 1
            except Exception as e:
                print(f"      |_ Error deleting {f.name}: {e}")
    print(f"   |_ [GC Report] Erased {deleted_count} stale buffers.")
                
    print(f"✅ Collection complete. High-Fidelity written to {raw_path}. Low-Fi dumped to {buffer_path}")

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
