#!/usr/bin/env python3
import os
import re
import sys
from pathlib import Path

# Explicit Paths
SKILLS_DIR = Path(__file__).parent.parent.parent
if not SKILLS_DIR.exists():
    print(f"[FATAL] Cannot locate skills directory at {SKILLS_DIR}")
    sys.exit(1)

# Definitions of Constitutional Violations
VIOLATIONS = [
    {
        "id": "V1-GHOST_PATH",
        "name": "Ghost Path Eradication (03_RESEARCH_PROJECT_LAW)",
        "desc": "Found deprecated legacy paths (e.g., /roo" + "t/resear" + "ch_bot/)",
        "pattern": re.compile(r'/root/' + r'research_bot/'),
        "severity": "CRITICAL"
    },
    {
        "id": "V2-HEAVY_ASSET_MISSING",
        "name": "Heavy Asset Visa Missing (02_ASSET_LIFECYCLE_LAW)",
        "desc": "Missing [L1 Constitution Block] for heavy asset downloaders",
        # We only check this conditionally later, but keep it here for structure
        "severity": "CRITICAL"
    },
    {
        "id": "V3-WANDB_GLOBAL_POLLUTION",
        "name": "Wandb Global Pollution (Anti-Bloat Law)",
        "desc": "Missing warning about WANDB_DIR routing",
        "severity": "CRITICAL"
    }
]

# Skills that MUST implement the Heavy Asset Visa
HEAVY_ASSET_SKILLS = ["kaggle", "huggingface"]
# Skills that MUST implement Wandb Isolation Warning
WANDB_SKILLS = ["wandb"]

def audit_skill(skill_path: Path) -> list:
    issues = []
    skill_name = skill_path.parent.name
    try:
        content = skill_path.read_text(encoding="utf-8")
        
        # 1. Check Ghost Paths globally
        if VIOLATIONS[0]["pattern"].search(content):
            issues.append(VIOLATIONS[0])
            
        # 2. Check Heavy Asset Visa (Targeted)
        if skill_name in HEAVY_ASSET_SKILLS:
            if "[L1 Constitution Block]" not in content:
                issues.append(VIOLATIONS[1])
                
        # 3. Check Wandb Pollution (Targeted)
        if skill_name in WANDB_SKILLS:
            if "Anti-Bloat Law" not in content and "WANDB_DIR" not in content:
                 issues.append(VIOLATIONS[2])
                 
    except Exception as e:
        print(f"  [ERROR] Failed to read {skill_path.name}: {e}")
    return issues

def main():
    print(f"========== ⚖️ SKILL ALIGNER AUDIT ==========")
    print(f"Targeting directory: {SKILLS_DIR}")
    
    total_skills = 0
    failed_skills = 0
    
    for root, _, files in os.walk(SKILLS_DIR):
        if "SKILL.md" in files:
            skill_md = Path(root) / "SKILL.md"
            total_skills += 1
            issues = audit_skill(skill_md)
            
            if issues:
                failed_skills += 1
                print(f"\n[❌ FAILED] Skill: {skill_md.parent.name}")
                for issue in issues:
                    print(f"    - [{issue['id']}] {issue['name']}")
                    print(f"      {issue['desc']}")
                    
    print(f"\n============================================")
    if failed_skills > 0:
        print(f"🚨 AUDIT FAILED: {failed_skills}/{total_skills} skills hold unconstitutional logic.")
        print(f"Agent Action Required: Use replace_file_content to fix the above SKILL.md files immediately.")
        sys.exit(1)
    else:
        print(f"✅ AUDIT PASSED: 100% of skills align perfectly with the Gemma L1 Constitution.")
        sys.exit(0)

if __name__ == "__main__":
    main()
