#!/usr/bin/env python3
import argparse
import subprocess
import os
import sys
import re

SKILL_NAME = "robust-latex"
SKILL_VERSION = "1.0.0"

def run_command(cmd, work_dir, timeout=300):
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=work_dir,
            timeout=timeout,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        return result
    except subprocess.TimeoutExpired:
        print(f"Error: Command timed out after {timeout} seconds: {' '.join(cmd)}")
        return None
    except Exception as e:
        print(f"Error executing command {' '.join(cmd)}: {e}")
        return None

def detect_engine(file_path):
    """Automatically detect whether to use pdflatex or xelatex based on document content."""
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
        
    if re.search(r'\\usepackage(\[.*?\])?\{xeCJK\}', content) or \
       re.search(r'\\documentclass(\[.*?\])?\{ctexart\}', content) or \
       re.search(r'\\documentclass(\[.*?\])?\{ctexrep\}', content):
        return "xelatex"
    return "pdflatex"

def audit_log_files(log_path):
    """Deep scan of the LaTeX .log file for silent failures like Missing Characters."""
    if not os.path.exists(log_path):
        return ["Log file not found, compilation might have crashed completely."]
        
    critical_errors = []
    with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            if "Missing character:" in line:
                critical_errors.append(line.strip())
            elif "! LaTeX Error:" in line:
                critical_errors.append(line.strip())
            elif "Fatal error" in line:
                critical_errors.append(line.strip())
            elif "! Critical" in line:
                critical_errors.append(line.strip())
                
    return critical_errors

def perform_compile(file_path, timeout=300, engine=None):
    file_path = os.path.abspath(file_path)
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return False
        
    work_dir = os.path.dirname(file_path)
    basename = os.path.basename(file_path)
    base_no_ext = os.path.splitext(basename)[0]
    
    if not engine:
        engine = detect_engine(file_path)
        
    print(f"[{SKILL_NAME}] Compiling document: {basename}")
    print(f"[{SKILL_NAME}] Auto-detected Engine: {engine}")
    
    latex_cmd = [
        engine,
        "-interaction=nonstopmode",
        "-halt-on-error",
        f"-output-directory={work_dir}",
        basename 
    ]
    bibtex_cmd = ["bibtex", base_no_ext]

    print(">> Pass 1: Syntax & Hierarchy")
    res1 = run_command(latex_cmd, work_dir, timeout)
    if not res1: return False
    
    aux_file = os.path.join(work_dir, f"{base_no_ext}.aux")
    needs_bibtex = False
    if os.path.exists(aux_file):
        with open(aux_file, 'r', errors='ignore') as f:
            content = f.read()
            if "\\bibdata" in content or "\\bibstyle" in content:
                needs_bibtex = True
                
    if needs_bibtex:
        print(">> Pass 2: Bibliography Resolving")
        run_command(bibtex_cmd, work_dir, timeout)
        print(">> Pass 3: Cross-Ref Linking")
        run_command(latex_cmd, work_dir, timeout)

    print(">> Pass 4: Final Document Generation")
    res_final = run_command(latex_cmd, work_dir, timeout)
    if not res_final: return False

    # QUALITY INSPECTION (The Master Gate)
    log_file = os.path.join(work_dir, f"{base_no_ext}.log")
    pdf_file = os.path.join(work_dir, f"{base_no_ext}.pdf")
    
    print(f"[{SKILL_NAME}] Initiating deep log audit on {base_no_ext}.log...")
    fatal_flaws = audit_log_files(log_file)
    
    if fatal_flaws:
        print(f"❌ COMPILATION REJECTED: {len(fatal_flaws)} critical flaws found in the log.")
        for flaw in fatal_flaws:
            print(f"   -> {flaw}")
        print("\nAgent Action Required: Address the missing fonts/dependencies and recompile.")
        return False

    if res_final.returncode != 0 or not os.path.exists(pdf_file):
        print("❌ COMPILATION FAILED: Compiler returned non-zero or PDF is missing.")
        return False
        
    print(f"✅ SUCCESS: PDF generated at {pdf_file} with PERFECT zero-error log validation.")
    return True

def main():
    parser = argparse.ArgumentParser(description=f"OpenClaw Robust LaTeX Agent Target v{SKILL_VERSION}")
    parser.add_argument("file", help="Path to the .tex main file")
    parser.add_argument("--engine", help="Force engine (pdflatex, xelatex)", default=None)
    parser.add_argument("--timeout", type=int, default=300, help="Timeout in seconds")

    args = parser.parse_args()
    success = perform_compile(args.file, args.timeout, args.engine)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
