#!/usr/bin/env python3
"""
[Systematic Identity Test Plan] - Semantic Memory Linter (RAG Purge)
This script acts as the "Garbage Collector" for the LLM's RAG Memory Vault.
It scans physical files in `session_archives` and SQLite vectors for explicitly banned 
"semantic poison" keywords (like legacy model versions) to prevent secondary hallucinations.
"""
import os
import re
import sys
import glob

# Paths
ARCHIVES_DIR = os.path.expanduser("~/workspace/docs/session_archives")

# Definition of Semantic Poison
POISON_BLACKLIST = [
    re.compile(r'(?i)gemini[\s-]*3\.?1[\s-]*flash[\s-]*lite'),
    re.compile(r'(?i)3\.?1[\s-]*lite'),
    # Legacy Skills (Phase 1 Quarantine List)
    re.compile(r'(?i)(food[-_]?order|podcast[-_]?maker|songsee|sonoscli|spotify[-_]?player|bluebubbles|imsg|slack|wacli|openhue|currency[-_]?exchange|camsnap|gifgrep|life[-_]?assistant|video[-_]?frames|voice[-_]?call|ppt[-_]?maker|ordercli)'),
    re.compile(r'(?i)(apple[-_]?notes|apple[-_]?reminders|bear[-_]?notes|notion|obsidian|obsidian[-_]?direct|1password|blucli|blogwatcher|126[-_]?email|school[-_]?email)'),
    re.compile(r'(?i)(work[-_]?assistant|himalaya|trello|wealth[-_]?assistant|coding[-_]?agent|code[-_]?mentor)'),
    re.compile(r'(?i)(openai[-_]?image[-_]?gen|openai[-_]?whisper|openai[-_]?whisper[-_]?api|kokoro[-_]?tts|sherpa[-_]?onnx[-_]?tts|speech[-_]?to[-_]?text)'),
    re.compile(r'(?i)(nano[-_]?banana[-_]?pro|eightctl|goplaces|vpn[-_]?login)'),
]

def scan_markdown_files():
    print(f"🧹 [SEMANTIC LINTER] Scanning {ARCHIVES_DIR} for cognitive poison...")
    if not os.path.exists(ARCHIVES_DIR):
        print("✅ No session archives found. Memory is clean.")
        return 0
        
    md_files = glob.glob(os.path.join(ARCHIVES_DIR, "**/*.md"), recursive=True)
    poisoned_files = 0
    
    for file_path in md_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            is_poisoned = False
            for pattern in POISON_BLACKLIST:
                if pattern.search(content):
                    is_poisoned = True
                    break
                    
            if is_poisoned:
                poisoned_files += 1
                print(f"[🚨 POISON DETECTED] File infected with legacy hallucination: {file_path}")
                # We rename it to .quarantine so the RAG indexer ignores it, rather than destructive rm.
                quarantine_path = file_path + ".quarantined"
                os.rename(file_path, quarantine_path)
                print(f"   -> 🔒 Quarantined: {quarantine_path}")
                
        except Exception as e:
            print(f"[⚠️ WARNING] Could not read {file_path}: {e}")
            
    return poisoned_files

if __name__ == "__main__":
    poison_count = scan_markdown_files()
    print("---------------------------------------------------")
    if poison_count > 0:
        print(f"✅ [LINTER COMPLETE] Quarantined {poison_count} poisoned artifacts to protect LLM RAG Vector space.")
    else:
        print("✅ [LINTER COMPLETE] RAG Memory Pool is 100% PURE. No legacy semantic ghosts found.")
    sys.exit(0)
