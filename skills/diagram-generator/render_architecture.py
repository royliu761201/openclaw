import sys
import os

# --- L1 SANDBOX INCARCERATION PROBE ---
in_venv = sys.prefix != sys.base_prefix
if not in_venv:
    print("⚠️ [L1 PROBE] Global scope detected. Self-incarcerating into VENV...")
    venv_python = os.path.join(os.path.dirname(os.path.abspath(__file__)), "venv/bin/python3")
    if os.path.exists(venv_python):
        os.execv(venv_python, [venv_python] + sys.argv)
    else:
        print("❌ Fatal: Sandbox VENV not found. Please create one.")
        sys.exit(1)
# ------------------------------------------

import subprocess
import argparse

def render_graphviz(dot_code, output_path, format="png"):
    """Render Graphviz (DOT) code to an image file."""
    # Write DOT code to a temporary file
    tmp_dot = "/tmp/architecture_diagram.dot"
    with open(tmp_dot, "w") as f:
        f.write(dot_code)
        
    print(f"Executing Graphviz to render diagram to {output_path}...")
    try:
        # Run the `dot` command-line tool (requires Graphviz to be installed)
        subprocess.run(
            ["dot", f"-T{format}", tmp_dot, f"-o{output_path}"], 
            check=True,
            capture_output=True,
            text=True
        )
        print(f"Successfully generated diagram: {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"Graphviz error:\n{e.stderr}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("Error: 'dot' command not found. Please ensure Graphviz is installed (e.g., 'brew install graphviz').", file=sys.stderr)
        sys.exit(1)
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Render academic architecture diagrams using Graphviz.")
    parser.add_argument("--code", required=True, help="Graphviz DOT code specifying the architecture.")
    parser.add_argument("--output", required=True, help="Absolute path to save the generated image file (e.g., /path/to/diagram.png).")
    parser.add_argument("--format", default="png", choices=["png", "pdf", "svg"], help="Output format (default: png).")
    
    args = parser.parse_args()
    
    render_graphviz(args.code, args.output, args.format)
