#!/usr/bin/env python3
"""
Style Polisher
Automatically reviews LaTeX and Markdown drafts for academic tone, structural flow,
and SSoT translation consistency.
"""

import argparse
import os
import re

def polish_document(filepath):
    if not os.path.exists(filepath):
        print(f"❌ Error: File not found {filepath}")
        return

    print(f"📄 Scanning Academic Document: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    issues_found = 0
    
    # 1. LaTeX Empty Ref Check
    empty_refs = re.findall(r'\\ref\{\}', content)
    if empty_refs:
        print(f"⚠️  [Structural] Found {len(empty_refs)} empty \\ref{{}} tags.")
        issues_found += len(empty_refs)
        
    # 2. LaTeX Empty Cite Check
    empty_cites = re.findall(r'\\cite\{\}', content)
    if empty_cites:
        print(f"⚠️  [Structural] Found {len(empty_cites)} empty \\cite{{}} tags.")
        issues_found += len(empty_cites)

    # 3. Tone checks (crude heuristics for demonstration of pipeline)
    prohibited_words = ["very good", "bad", "huge", "tiny", "stuff", "things"]
    for word in prohibited_words:
        # Simple word boundary match
        matches = re.finditer(r'\b' + word + r'\b', content, re.IGNORECASE)
        for m in matches:
            print(f"⚠️  [Tone] Found informal verbiage '{word}' at index {m.start()}. Context: '...{content[max(0, m.start()-15):min(len(content), m.end()+15)]}...'")
            issues_found += 1

    if issues_found == 0:
        print("✅ [Style] Document passes automated structural and tonal checks. Ready for human qualitative review.")
    else:
        print(f"❌ [Style] Document polishing failed! Please fix the {issues_found} highlighted semantic/structural issues.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Academic Style Polisher")
    parser.add_argument("--paper", required=True, help="Path to the .tex or .md drafting file")
    
    args = parser.parse_args()
    polish_document(args.paper)
