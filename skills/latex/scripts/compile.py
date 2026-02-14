import argparse
import subprocess
import os
import shutil

def compile_tex(file_path, clean=True):
    # Ensure absolute path
    file_path = os.path.abspath(file_path)
    work_dir = os.path.dirname(file_path)
    basename = os.path.basename(file_path)
    
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return

    # Run pdflatex
    # -interaction=nonstopmode prevents hanging on errors
    # -output-directory ensures output goes where we expect (same dir as source)
    cmd = [
        "pdflatex",
        "-interaction=nonstopmode",
        f"-output-directory={work_dir}",
        file_path
    ]
    
    print(f"Compiling {basename}...")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError:
        print("Error: 'pdflatex' command not found. Please install TeX Live or MiKTeX.")
        return

    if result.returncode == 0:
        print("Compilation successful!")
        pdf_file = file_path.replace(".tex", ".pdf")
        if os.path.exists(pdf_file):
            print(f"Output: {pdf_file}")
        else:
             print("Warning: Exit code 0, but PDF not found.")

        # Check for common warnings in stdout
        if "undefined reference" in result.stdout or "undefined citation" in result.stdout:
            print("Warning: There were undefined references or citations.")
            # Optional: print relevant lines
            for line in result.stdout.splitlines():
                if "undefined" in line.lower() and "Warning" in line:
                    print(line)
        
        if clean:
            # Clean aux files
            base_no_ext = os.path.splitext(file_path)[0]
            for ext in ['.aux', '.log', '.out']:
                aux = base_no_ext + ext
                if os.path.exists(aux):
                    try:
                        os.remove(aux)
                        print(f"Cleaned {aux}")
                    except OSError:
                        pass
    else:
        print("Compilation failed!")
        # Parse for specific LaTeX errors
        errors = []
        for line in result.stdout.splitlines():
            if line.startswith('! '):
                errors.append(line)
            elif line.startswith('l.'): # Line number context
                errors.append(line)
        
        if errors:
            print("\nCritical Errors:")
            for err in errors:
                print(err)
        else:
            # Fallback if no specific errors found
            print("\n".join(result.stdout.splitlines()[-20:]))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="Path to .tex file")
    parser.add_argument("--clean", action="store_true", default=True, help="Clean aux files")
    args = parser.parse_args()
    
    compile_tex(args.file, args.clean)
