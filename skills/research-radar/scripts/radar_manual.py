#!/usr/bin/env python3
import os
import sys
import subprocess
import datetime
from pathlib import Path

# Imbue current path to import radar_analyzer
script_dir = Path(__file__).parent
sys.path.append(str(script_dir))

try:
    from radar_analyzer import generate_dandan_prompt, REPORTS_DIR
except ImportError:
    print("❌ Error: Could not import radar_analyzer.py. Ensure this script is in the skills/research-radar/scripts/ directory.")
    sys.exit(1)

def extract_content(target: str) -> str:
    print(f"🔍 [Phase 1] Extracting raw content from: {target}...")
    
    # 尝试使用 summarize 技能提起内容
    try:
        # summarize 工具如果有 --extract-only 选项则只提取纯文本
        result = subprocess.run(
            ["summarize", target, "--extract-only"],
            capture_output=True, text=True, check=True
        )
        content = result.stdout.strip()
        if content:
            print(f"✅ Successfully extracted {len(content)} characters via `summarize`.")
            return content
    except FileNotFoundError:
        print("⚠️ `summarize` CLI not found. Falling back to direct file read...")
    except subprocess.CalledProcessError as e:
        print(f"⚠️ `summarize` failed: {e.stderr}. Falling back to direct file read...")
        
    # 如果 summarize 不能用，回退到本地直接读文件
    if os.path.isfile(target):
        try:
            with open(target, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"✅ Successfully read {len(content)} characters from local file.")
            return content
        except Exception as e:
            print(f"❌ Failed to read file {target}: {e}")
            sys.exit(1)
    else:
        print("❌ Target is not a valid local file and `summarize` failed to fetch it as a URL/PDF.")
        sys.exit(1)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="On-Demand Research Radar (Manual Trigger)")
    parser.add_argument("target", type=str, help="URL or local path (PDF, TXT, MD) to analyze")
    args = parser.parse_args()

    # 1. 获取文本内容
    content = extract_content(args.target)
    if not content:
        print("❌ Extracted content is empty. Aborting.")
        sys.exit(1)
        
    # 2. 调用大脑兵团处理
    print("🧠 [Phase 2] Formatting Radar Inbox Prompt for Dandan...")
    date_str = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    prompt_content = generate_dandan_prompt(content, date_str)
    
    # 3. 存储战报 Inbox
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    inbox_path = REPORTS_DIR / f"{date_str}_MANUAL_RADAR_INBOX.md"
    
    with open(inbox_path, "w", encoding='utf-8') as f:
        f.write(prompt_content)
        
    print(f"✅ Inbox Prompt generated at {inbox_path}")
    print(f"🔥 AGENTIC HANDOFF: Please ask Dandan to read this file and execute the analysis for `{args.target}`!")

if __name__ == "__main__":
    main()
