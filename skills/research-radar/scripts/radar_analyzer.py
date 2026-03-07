#!/usr/bin/env python3
import os
import sys
import subprocess
import datetime
from pathlib import Path
import urllib.request
import urllib.error
import json

WORKSPACE_DIR = Path(os.path.expanduser("~/workspace"))
RAW_DATA_DIR = WORKSPACE_DIR / "docs" / "research_ideation" / "radar_raw_data"
REPORTS_DIR = WORKSPACE_DIR / "docs" / "research_ideation" / "radar_reports"
PDCA_FILE = WORKSPACE_DIR / "docs" / "projects_pdca" / "05_RESEARCH_RADAR_PDCA.md"

PI_PROFILE_PATH = os.path.expanduser("~/Documents/projects/openclaw/skills/research-assistant/knowledge/profiles/pi_profile_xiaohua_liu.md")
IDEA_LIST_PATH = WORKSPACE_DIR / "docs" / "research_ideation" / "EXTENSION_IDEA_MASTER.md"

def read_file_safe(path):
    try:
        with open(path, "r") as f:
            return f.read()
    except Exception as e:
        return f"Error reading {path}: {e}"

def call_gemini(prompt: str) -> str:
    # 01 Brain Model - Local direct execution with Flash Lite (Very cheap/fast)
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "Error: GEMINI_API_KEY environment variable is not set on Node 01."
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-lite-preview-02-05:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    data = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2}
    }).encode('utf-8')
    
    try:
        req = urllib.request.Request(url, data=data, headers=headers)
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            return result['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return f"Error calling Gemini via REST API: {str(e)}"

def process_results_with_llm(raw_data: str) -> str:
    pi_profile = read_file_safe(PI_PROFILE_PATH)
    idea_list = read_file_safe(IDEA_LIST_PATH)
    
    prompt = f"""
You are the Cognitive Alignment Engine for Dr. Xiaohua Liu's Research Radar.
Your job is to read raw academic paper results collected by edge probes and cross-examine them against the PI's research profile, active projects, and idea lists.

### 1. PI Profile & Active P0 Projects:
{pi_profile}

### 2. Emerging Idea List (For threat/opportunity detection):
{idea_list}

### 3. Captured arXiv Papers (Raw Data):
{raw_data}

### Task:
You must strictly execute the PURE-T protocol (Trim/Filter).
Do NOT summarize every paper. Most papers are irrelevant.
Only report on MAX 3 papers total if and ONLY if they directly:
- WARNING: Pose a threat (someone is publishing our Idea List).
- SOLUTION: Offer a direct methodological solution to our active P0 projects (CaLaM, Frenet, PESSO, PhysDiff).
- OPPORTUNITY: Strongly align as a foundation for his NSFC/Grants.

If no papers meet this high bar, output EXACTLY: "NO_HIGH_VALUE_TARGETS".
Otherwise, output a highly concise strategic brief in Markdown:
For each high-value paper:
- **Title**: ...
- **Classification**: [Threat WARNING] / [Method SOLUTION] / [Grant OPPORTUNITY]
- **Actionable Insight**: 1-2 sentences on exactly why this matters and what Dr. Liu should do.
"""
    return call_gemini(prompt)

def analyze_raw_data(date_str: str = None):
    if not date_str:
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        
    raw_path = RAW_DATA_DIR / f"{date_str}_RAW.md"
    if not raw_path.exists():
        print(f"❌ Error: Raw data file {raw_path} not found. Producer has not generated data for {date_str}.")
        return

    print(f"🧠 Initiating Cognitive Analysis (Consumer Mode) on raw data from {date_str}...")
    raw_data = read_file_safe(raw_path)
    
    analysis = process_results_with_llm(raw_data)
    
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / f"{date_str}_RADAR_V2_REPORT.md"
    
    report_content = [
        f"# 📡 Radar V2 Cognitive Intel Report: {date_str}",
        "> **Auto-analyzed by Research-Radar (Node 01 Brain)**\n",
        "## Strategic High-Value Targets\n"
    ]
    
    found_leads = False
    if analysis and "NO_HIGH_VALUE_TARGETS" not in analysis and "Error:" not in analysis:
        report_content.append(analysis)
        found_leads = True
    else:
        report_content.append("\n*No critical threats or high-value breakthroughs detected today.*")

    with open(report_path, "w") as f:
        f.write("\n".join(report_content))
    
    print(f"✅ Brain Analysis complete. Intel written to {report_path}")
    update_pdca(date_str, report_path, found_leads)
    git_sync_workspace()

def update_pdca(date_str: str, report_path: Path, found_leads: bool):
    if not PDCA_FILE.exists(): return
    leads_str = "High-Value Targets Found" if found_leads else "No major leads"
    new_row = f"| {date_str} (V2-Brain) | `../research_ideation/radar_reports/{report_path.name}` | {leads_str} | ✅ Brain Analysis OK |\n"
    
    with open(PDCA_FILE, "r") as f: content = f.read()
    if "| *待首次执行*" in content: content = content.replace("| *待首次执行* | - | - | ⏳ 等待扫掠 |", new_row.strip())
    else: content += new_row
    with open(PDCA_FILE, "w") as f: f.write(content)

def git_sync_workspace():
    print("🔄 Synchronizing Brain Analysis to Global Workspace (Git-as-SSoT)...")
    try:
        subprocess.run(["git", "add", "."], cwd=str(WORKSPACE_DIR), check=True)
        status = subprocess.run(["git", "status", "--porcelain"], cwd=str(WORKSPACE_DIR), capture_output=True, text=True)
        if not status.stdout.strip():
            print("   [Skip] No new files to commit.")
            return
        subprocess.run(["git", "commit", "-m", "[Auto] Radar Brain Analysis Sync"], cwd=str(WORKSPACE_DIR), check=True)
        subprocess.run(["git", "pull", "--rebase"], cwd=str(WORKSPACE_DIR), check=True)
        subprocess.run(["git", "push"], cwd=str(WORKSPACE_DIR), check=True)
        print("✅ Git Sync Complete. Analysis deposited to SSoT.")
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Git Sync Warning: {e}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Radar Cognitive Brain (Consumer)")
    parser.add_argument("--date", type=str, help="Specific date string to analyze (YYYY-MM-DD)", default=None)
    args = parser.parse_args()
    
    analyze_raw_data(args.date)
