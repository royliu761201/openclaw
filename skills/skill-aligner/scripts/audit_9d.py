#!/usr/bin/env python3
import os
import re
from pathlib import Path

# ==========================================
# OPENCLAW: 9D SKILL AUDIT SCANNER
# ==========================================

SKILLS_DIR = os.path.expanduser("~/openclaw/skills")

# Whitelist files or directories that are allowed to bypass certain checks
WHITELIST_DIRS = [
    ".git",
    "__pycache__",
    "node_modules", # Although we scan for node_modules presence, we don't scan their internals
    "lark-integration", # Core Node 01 Webhook Gateway, intrinsically requires Node.js
]

def scan_file(filepath: Path):
    violations = []
    
    # Only scan executable script types
    ext = filepath.suffix
    if ext not in ['.py', '.sh', '.js', '.mjs', '.cjs', '.ts']:
        if filepath.name != 'package.json':
            return []
    
    if not filepath.exists() or not filepath.is_file():
        return []

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            lines = content.split('\n')
    except UnicodeDecodeError:
        return [] # Skip binary files

    filename = filepath.name
    ext = filepath.suffix

    # Check 1: Node.js/NPM Bloat (.mjs, .js, package.json)
    if ext in ['.js', '.mjs', '.cjs', '.ts'] or filename == 'package.json':
        violations.append("[DIM_1: NPM Bloat] Pure-Python skills should not contain Node.js source files or package.json.")

    for i, line in enumerate(lines):
        line_num = i + 1
        
        # Check 2: Subprocess Wrapper / curl bloat
        # Look for literal 'curl ' in subprocess calls or shell scripts
        if ext in ['.sh', '.py'] and re.search(r'\bcurl\s+http', line, re.IGNORECASE):
            # Allow healthcheck curl, but flag as warning
            if "healthcheck" not in str(filepath):
                 violations.append(f"[DIM_2: Wrapper Bloat] (L{line_num}) Bare curl detected. Use native Python requests/urllib.")

        # Check 3/6: Hardcoded Secrets (Bearer, API_KEY)
        if re.search(r'Bearer\s+[a-zA-Z0-9\-_]{15,}', line, re.IGNORECASE) or \
           re.search(r'(API_KEY|SECRET|TOKEN|PASSWORD)\s*=\s*["\'][a-zA-Z0-9\-_]{10,}["\']', line, re.IGNORECASE):
            violations.append(f"[DIM_6: Hardcoded Secrets] (L{line_num}) Suspected hardcoded key/token. Use ~/.openclaw_env injection.")

        # Check 7: Destructive Ops
        if re.search(r'\b' + 'rm' + r'\s+-r[fF]?\s+', line):
            if "/tmp" not in line and "cache" not in line.lower():
                violations.append(f"[DIM_7: Destructive Ops] (L{line_num}) Recursive remove detected. Ensure compliance with Invulnerability Law.")

        # Check 8: Shell Injection
        if ext == '.py' and 'subprocess.' in line and 'shell' + '=True' in line.replace(' ', ''):
             violations.append(f"[DIM_8: Shell Injection] (L{line_num}) Shell injection risk detected in subprocess. Must use safe array args.")

        # Check 9: Egress / Telemetry (Suspicious non-SSoT domains)
        # Search for tracking, telemetry, or analytics domains
        if re.search(r'https?://[a-zA-Z0-9.-]*(telemetry|analytics|track)[a-zA-Z0-9.-]*', line, re.IGNORECASE):
             violations.append(f"[DIM_9: Egress Control] (L{line_num}) Suspected telemetry or tracking endpoint detected.")

    return violations

def find_skills_nodes():
    nodes = []
    for root, dirs, files in os.walk(SKILLS_DIR):
        # Exclude whitelisted directories
        dirs[:] = [d for d in dirs if d not in WHITELIST_DIRS]
        
        for file in files:
            nodes.append(Path(root) / file)
            
        # Detect node_modules
        if "node_modules" in dirs:
            nodes.append(Path(root) / "node_modules")

    return nodes

def run_audit():
    print(f"⚖️ Scanning {SKILLS_DIR} for 9D Violations...")
    all_files = find_skills_nodes()
    
    total_violations = 0
    clean_files = 0
    flagged_files = 0
    
    for filepath in all_files:
        if filepath.name == "node_modules" and filepath.is_dir():
            print(f"❌ [FAIL] {filepath.relative_to(SKILLS_DIR)}")
            print("   -> [DIM_1: NPM Bloat] Found 'node_modules' directory. Must be removed from Edge skills.")
            total_violations += 1
            flagged_files += 1
            continue

        violations = scan_file(filepath)
        if violations:
            print(f"❌ [FAIL] {filepath.relative_to(SKILLS_DIR)}")
            for v in violations:
                print(f"   -> {v}")
            total_violations += len(violations)
            flagged_files += 1
        else:
            clean_files += 1

    print("\n" + "="*50)
    print(f"AUDIT COMPLETE. {clean_files + flagged_files} entities scanned.")
    if total_violations == 0:
        print("✅ [ALL PASSED] Zero Extraneous/Unsafe logic found.")
        return True
    else:
        print(f"⚠️  [SYSTEM ALIGNMENT FAILED] {total_violations} violations found in {flagged_files} files.")
        return False

if __name__ == "__main__":
    success = run_audit()
    if not success:
        exit(1)
    exit(0)
