import argparse
import subprocess
import os
import shutil
import re
import sys

def run_command(cmd, work_dir, timeout=300):
    """Run a subprocess command with timeout and error capture."""
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

def check_for_errors(stdout):
    """Parse LaTeX stdout for critical errors."""
    errors = []
    lines = stdout.splitlines()
    for line in lines:
        if line.startswith('! '):
            errors.append(line)
        elif line.startswith('l.'): # Line number context
            errors.append(line)
    return errors

def compile_tex(file_path, clean=True, timeout=300):
    # Ensure absolute path
    file_path = os.path.abspath(file_path)
    work_dir = os.path.dirname(file_path)
    basename = os.path.basename(file_path)
    base_no_ext = os.path.splitext(basename)[0]
    
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return False

    # Define commands
    pdflatex_cmd = [
        "pdflatex",
        "-interaction=nonstopmode",
        f"-output-directory={work_dir}",
        basename # Run in work_dir, so just basename
    ]
    
    bibtex_cmd = [
        "bibtex",
        base_no_ext
    ]

    print(f"Starting multi-pass compilation for {basename} in {work_dir}...")

    # Pass 1: pdflatex (Generate .aux)
    print("[1/4] Running pdflatex (Pass 1)...")
    res1 = run_command(pdflatex_cmd, work_dir, timeout)
    if not res1: return False
    
    # Check if BibTeX is needed
    # Look for \bibdata or \bibstyle in the .aux file
    aux_file = os.path.join(work_dir, f"{base_no_ext}.aux")
    needs_bibtex = False
    if os.path.exists(aux_file):
        with open(aux_file, 'r', errors='ignore') as f:
            content = f.read()
            if "\\bibdata" in content or "\\bibstyle" in content:
                needs_bibtex = True
    
    # Pass 2: bibtex (if needed)
    if needs_bibtex:
        print("[2/4] Running bibtex...")
        res_bib = run_command(bibtex_cmd, work_dir, timeout)
        if not res_bib: 
            print("Warning: BibTeX failed, but continuing...")
        elif res_bib.returncode != 0:
            print("Warning: BibTeX returned non-zero exit code.")
            print("\n".join(res_bib.stdout.splitlines()[-20:]))
    else:
        print("[2/4] Skipping bibtex (no bibliography found).")

    # Pass 3: pdflatex (Link citations)
    print("[3/4] Running pdflatex (Pass 2)...")
    res3 = run_command(pdflatex_cmd, work_dir, timeout)
    if not res3: return False

    # Pass 4: pdflatex (Finalize refs)
    print("[4/4] Running pdflatex (Pass 3)...")
    res4 = run_command(pdflatex_cmd, work_dir, timeout)
    if not res4: return False

    # Final Check
    if res4.returncode == 0:
        pdf_file = os.path.join(work_dir, f"{base_no_ext}.pdf")
        if os.path.exists(pdf_file):
            print(f"SUCCESS: Output generated at {pdf_file}")
            
            # Check for unresolved references in final log
            log_file = os.path.join(work_dir, f"{base_no_ext}.log")
            if os.path.exists(log_file):
                with open(log_file, 'r', errors='ignore') as f:
                    log_content = f.read()
                    if "undefined reference" in log_content or "undefined citation" in log_content: # Broad check
                        print("WARNING: There are still undefined references or citations.")
        else:
            print("Error: Exit code 0, but PDF not found.")
            return False
    else:
        print("COMPILATION FAILED!")
        errors = check_for_errors(res4.stdout)
        if errors:
            print("\nCritical Errors:")
            for err in errors:
                print(err)
        else:
            print("\nLast 20 lines of output:")
            print("\n".join(res4.stdout.splitlines()[-20:]))
        return False

    # Cleanup
    if clean:
        print("Cleaning auxiliary files...")
        extensions = ['.aux', '.log', '.out', '.bbl', '.blg', '.toc', '.lof', '.lot']
        for ext in extensions:
            file_to_remove = os.path.join(work_dir, base_no_ext + ext)
            if os.path.exists(file_to_remove):
                try:
                    os.remove(file_to_remove)
                    # print(f"Removed {ext}")
                except OSError:
                    pass
    
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="Path to .tex file")
    parser.add_argument("--clean", action="store_true", default=True, help="Clean aux files")
    parser.add_argument("--timeout", type=int, default=300, help="Compilation timeout in seconds")
    args = parser.parse_args()
    
    success = compile_tex(args.file, args.clean, args.timeout)
    if not success:
        sys.exit(1)
