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
    
    # --- Agent 1: The Filter (Triage) ---
    filter_prompt = f"""
You are the Radar Filter Agent. 
Scan the raw data below. Discard anything that is low-quality, purely theoretical without path to code, or unrelated to our core constraints.
OUTPUT ONLY THE TITLES AND ABSTRACTS of maximum 3 papers that are true breakthroughs (O(N) complexity reduction, absolute physical conservation) OR direct threats to our PI Profile.
If none pass the bar, output exactly: NO_HIGH_VALUE_TARGETS.

[Raw Data]:
{raw_data}
"""
    filtered_intel = call_gemini(filter_prompt)
    if "NO_HIGH_VALUE_TARGETS" in filtered_intel or not filtered_intel.strip():
        return "NO_HIGH_VALUE_TARGETS"

    # --- Agent 2: Red Team (Math Critic) ---
    red_prompt = f"""
You are the Red Team Math Critic.
Analyze these high-value papers: {filtered_intel}
Your ONLY job is to aggressively scrutinize their mathematical claims. 
Are their Hamiltonian conservations rigorous? Is their O(N) complexity claim hiding massive constants? 
If there's a flaw, point it out mathematically. If it's solid, propose a SymPy/PyTorch ablation script to verify their exact boundary conditions.
Output a highly technical Red Team brief.
"""
    red_analysis = call_gemini(red_prompt)

    # --- Agent 3: Blue Team (Code Builder) ---
    blue_prompt = f"""
You are the Blue Team Builder.
Analyze these high-value papers: {filtered_intel}
Against our PI profile: {pi_profile}
Your ONLY job is integration. How do we steal their best operators and graft them into our CaLaM, Frenet, or PESSO pipelines TODAY?
Output exact file modification strategies and PyTorch pseudocode for integrating their core algorithm.
"""
    blue_analysis = call_gemini(blue_prompt)

    # --- Agent 4: The Ranger (Cross-Domain Serendipity) ---
    ranger_prompt = f"""
You are the Ranger.
Analyze these high-value papers: {filtered_intel}
Against our Idea List: {idea_list}
Your ONLY job is cross-domain serendipity. Do not talk about AI. What does this remind you of in Statistical Mechanics, Cell Biology, or Differential Geometry?
Propose ONE completely unhinged but mathematically isomorphic idea that maps their breakthrough to a totally different discipline to secure a new Nature/Science angle.
"""
    ranger_analysis = call_gemini(ranger_prompt)

    final_report = f"## 🔴 Red Team (Math & Validity Critic)\n{red_analysis}\n\n---\n## 🔵 Blue Team (Code & Synergy Builder)\n{blue_analysis}\n\n---\n## 🟢 Ranger (Cross-Domain Serendipity)\n{ranger_analysis}\n"
    return final_report

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
