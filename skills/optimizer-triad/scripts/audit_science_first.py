import os
import sys
import re
from pathlib import Path

def print_err(msg):
    print(f"\\033[91m[FATAL] {msg}\\033[0m")

def print_ok(msg):
    print(f"\\033[92m[OK] {msg}\\033[0m")

def audit_file(filepath):
    code = filepath.read_text(encoding="utf-8")
    
    # Check 1: The 'nan_to_num' toxicity test
    if "nan_to_num" in code:
        print_err(f"Violation in {filepath}: Found 'nan_to_num'.")
        print_err("Masking NaNs is strictly forbidden under the Science-First Law. Fix the exploding gradients through scaling or layer tuning, do NOT mask them!")
        return False
        
    return True

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 audit_science_first.py <target_directory_or_file>")
        sys.exit(1)
        
    target = Path(sys.argv[1])
    if not target.exists():
        print_err(f"Target path does not exist: {target}")
        sys.exit(1)

    files_to_check = []
    if target.is_dir():
        files_to_check = list(target.rglob("*.py"))
    else:
        files_to_check = [target]
        
    passed = True
    for f in files_to_check:
        if not audit_file(f):
            passed = False
            
    if not passed:
        print_err("SCIENCE-FIRST LAW AUDIT FAILED. DO NOT DISPATCH.")
        sys.exit(1)
        
    print_ok("Static Physics/Math Integrity Scan Passed. No masked divergence detected.")
    sys.exit(0)

if __name__ == "__main__":
    main()
