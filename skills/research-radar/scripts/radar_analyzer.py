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
PDCA_FILE = WORKSPACE_DIR / "docs" / "projects_pdca" / "06_RADAR_META_SKILL_PDCA.md"

PI_PROFILE_PATH = Path(__file__).resolve().parent.parent.parent / "research-assistant" / "knowledge" / "profiles" / "pi_profile_xiaohua_liu.md"
IDEA_LIST_PATH = WORKSPACE_DIR / "docs" / "research_ideation" / "EXTENSION_IDEA_MASTER.md"

def read_file_safe(path):
    try:
        with open(path, "r") as f:
            return f.read()
    except Exception as e:
        return f"Error reading {path}: {e}"

def generate_dandan_prompt(raw_data: str, date_str: str) -> str:
    pi_profile = read_file_safe(PI_PROFILE_PATH)
    idea_list = read_file_safe(IDEA_LIST_PATH)
    
    prompt = f"""[指令：请 01 本脑 (Dandan) 狂烧算力深度阅读并研发]

## 📡 Radar System Wakeup Request ({date_str})

Dear Dandan,
The Radar Producer has fetched raw data. Under the L1 Constitution, Python scripts MUST NOT call LLMs directly. You are the Brain.
Please natively execute the 4-stage swarming analysis using your internal capabilities.

### 👑 Stage 0: The Command Override (Human Radar)
If the raw data contains "Feishu Intercepted Intel" or explicit Human-in-the-loop links, process those FIRST. They represent direct commands or explicit interests from the Boss. State clearly what they are and provide an initial academic/strategic assessment of why the Boss clipped them.

### 🔬 Stage 1: The Filter (Triage)
Scan the Raw Data. 
1. Discard purely theoretical papers without a clear path to code implementation for our specific projects.
2. DO NOT discard high-value industry dynamics (e.g., NVIDIA hardware, OpenAI/Anthropic/Meta capabilities, National policies, NSFC Grants). 
If no papers or significant industry dynamics pass, clearly state `NO_HIGH_VALUE_TARGETS` and stop here.

### 🔴 Stage 2: Red Team (Math Critic)
Scrutinize the remaining academic targets mathematically. Are Hamiltonian conservations rigorous? Any hidden constants in O(N)?

### 🔵 Stage 3: Blue Team (Code Builder)
How do we steal their operators for our current CaLaM, Frenet, or PESSO projects?

### 🟢 Stage 4: The Ranger (Cross-Domain Serendipity)
Propose one mathematically isomorphic idea mapping their breakthrough to a totally different discipline.

### 🔮 Stage 5: The Oracle (Omniscient Compute & Industry Intel)
Extract and loudly highlight ALL critical data regarding:
- **Compute Hardware:** NVIDIA clusters, B200, TPU utilization, hardware bottlenecks.
- **Corporate AI Capabilities:** OpenAI, Meta, Google DeepMind breakthroughs (e.g., o3 logic, Gemini coding).
- **Macro/Policy:** NSFC (National Natural Science Foundation of China), AI4S Funding, and global AI macro trends.
- **Top-Tier Monitored Targets:** Explicitly summarize any new intelligence involving our tracked Scholars (e.g., Kaiming He, Ilya), Top Institutions (e.g., Meta FAIR, DeepMind), or Benchmark Papers (AlphaFold 3, FNO, Score-Based, etc.).

### 📚 Stage 6: Academic Grounding (References)
For EVERY high-value research idea or innovation you propose (from Stages 2-4), you MUST output a rigorously formatted Academic Reference List containing 20 to 30 high-quality benchmark citations. 

**Definition of "High-Quality References":**
1. **Venue Prestige**: Papers MUST originate from CCF-A conferences (e.g., NeurIPS, ICML, ICLR, CVPR, ACL, KDD, IEEE S&P) or Top-Tier Journals (Nature, Science, Cell, Lancet, or CAS Q1 journals with Impact Factor > 10).
2. **Recency**: At least 70% of citations must be from the last 3-5 years (2021-present).
3. **Relevance**: The references must directly back up the methodology, the physical mechanism (e.g., Hamiltonian operators), or the empirical benchmark you are suggesting.
4. **Authority**: Prioritize papers authored by the top scholars and top institutions listed in the Knowledge Base.

Do NOT hallucinate DOIs or ArXiv IDs. If you know the paper, cite the Title, Authors, Venue, and Year.

> **CRITICAL ACTION**: After thinking, you MUST use your `write_to_file` tool to save your final analysis as a markdown file at: `{REPORTS_DIR}/{date_str}_RADAR_V2_REPORT.md`

---
### 👤 Context 1: PI Profile
{pi_profile}

### 💡 Context 2: Idea List
{idea_list}

### 📥 Context 3: Raw Data
{raw_data}
"""
    return prompt

def analyze_raw_data(date_str: str = None):
    if not date_str:
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        
    raw_path = RAW_DATA_DIR / f"{date_str}_RAW.md"
    if not raw_path.exists():
        print(f"❌ Error: Raw data file {raw_path} not found. Producer has not generated data for {date_str}.")
        return

    print(f"🧠 Formatting Radar Inbox Prompt for Dandan on {date_str}...")
    raw_data = read_file_safe(raw_path)
    
    prompt_content = generate_dandan_prompt(raw_data, date_str)
    
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    inbox_path = REPORTS_DIR / f"{date_str}_RADAR_INBOX.md"
    
    with open(inbox_path, "w", encoding='utf-8') as f:
        f.write(prompt_content)
    
    print(f"✅ Inbox Prompt generated at {inbox_path}")
    print(f"🔥 AGENTIC HANDOFF: Please ask Dandan to read this file and execute the analysis!")
    
    update_pdca(date_str, inbox_path)
    git_sync_workspace()

def update_pdca(date_str: str, report_path: Path):
    if not PDCA_FILE.exists(): return
    new_row = f"| {date_str} (Handoff) | `../research_ideation/radar_reports/{report_path.name}` | Waiting for Dandan | ⏳ Agent Pending |\n"
    
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
