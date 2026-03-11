#!/usr/bin/env python3
"""
[Systematic Identity Test Plan] - Static Skill Bindings Linter
This script checks all `SKILL.md` configurations against the actual physical `.openclaw_env`.
It ensures that EVERY environment variable legally declared in a skill actually exists and hasn't drifted.
"""
import os
import re
import sys

# Core paths
OPENCLAW_SKILLS_DIR = os.path.expanduser("~/openclaw/skills")
ENV_FILE = os.path.expanduser("~/.openclaw_env")

def load_system_env():
    valid_keys = set()
    if not os.path.exists(ENV_FILE):
        print(f"[❌ FATAL] Physical env file missing: {ENV_FILE}")
        sys.exit(1)

    with open(ENV_FILE, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            # Handle export KEY=VALUE
            if line.startswith('export '):
                line = line[len('export '):]
            
            if '=' in line:
                key = line.split('=')[0].strip()
                valid_keys.add(key)
    return valid_keys

def parse_skill_requirements(skill_path):
    required_keys = []
    with open(skill_path, 'r') as f:
        in_requires_block = False
        for line in f:
            stripped = line.strip()
            # Catch YAML style:
            # requires:
            #   - NEXT_PUBLIC_SUPABASE_URL
            # Or inline style
            if stripped.startswith('requires:'):
                in_requires_block = True
                continue
            elif in_requires_block:
                if stripped.startswith('- '):
                    key = stripped[2:].strip()
                    required_keys.append(key)
                elif stripped == "" or not stripped.startswith('-'):
                    # if it hits a property, block ends
                    if ":" in stripped:
                        in_requires_block = False
                        
            # Catch env:
            # env:
            #   - TAVILY_API_KEY
            if stripped.startswith('env:'):
                in_requires_block = True
                continue
            elif in_requires_block:
                if stripped.startswith('- '):
                    key = stripped[2:].strip()
                    required_keys.append(key)
                elif stripped == "" or not stripped.startswith('-'):
                    if ":" in stripped:
                        in_requires_block = False
                        
    # Filter things that clearly look like descriptions or strings rather than pure ENV KEYS
    clean_keys = [k for k in required_keys if re.match(r'^[A-Z0-9_]+$', k)]
    return clean_keys

def lint_skills():
    print("🛡️ [LINTER] Starting SKILL.md Meta-Linter (The Blind-Piercing Probe)...")
    system_keys = load_system_env()
    print(f"✅ Loaded {len(system_keys)} valid physical environment variables from native OS layer.")
    
    total_skills_checked = 0
    drift_violations = 0
    
    for root, _, files in os.walk(OPENCLAW_SKILLS_DIR):
        for file in files:
            if file == "SKILL.md":
                total_skills_checked += 1
                skill_path = os.path.join(root, file)
                skill_name = os.path.basename(root)
                
                req_keys = parse_skill_requirements(skill_path)
                for key in req_keys:
                    if key not in system_keys:
                        drift_violations += 1
                        print(f"\n[🚨 DRIFT DETECTED] Skill '{skill_name}' dictates dependency:")
                        print(f"  --> Requires LLM Env Key: '{key}'")
                        print(f"  --> State: ❌ GHOST MAPPING! Does not physically exist in .openclaw_env!")

    print("\n---------------------------------------------------")
    if drift_violations > 0:
        print(f"❌ [LINTER FAILED] Discovered {drift_violations} silent capability drifts. Agents will hallucinate competence.")
        sys.exit(1)
    else:
        print(f"✅ [OMNI-GREEN] Scanned {total_skills_checked} physical skills. 100% SSoT Auth Linkage aligned.")
        sys.exit(0)

if __name__ == "__main__":
    lint_skills()
