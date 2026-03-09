import os
import asyncio
import re
import json
from typing import List, Optional

"""
Atomic LaTeX Operations.
Pure functions for file manipulation, cleaning, and compilation.
"""

def clean_latex(text: str) -> str:
    """Post-processing to remove Markdown artifacts from LLM output."""
    text = text.replace("**", "").replace("__", "")
    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE) # Remove MD headers
    text = text.replace('\"', '') # Simple quote fix
    text = text.replace("```latex", "").replace("```", "").strip()
    return text

def inject_results_macros(project_dir: str):
    """
    Reads results.json and appends macros to macros.tex.
    """
    json_path = os.path.join(project_dir, "results.json")
    macros_path = os.path.join(project_dir, "macros.tex")
    
    if not os.path.exists(json_path):
        return
        
    with open(json_path, "r") as f:
        data = json.load(f)
        
    latex_cmds = []
    # Metrics
    for key, val in data.get("metrics", {}).items():
        # camelCase conversion
        cmd_name = "res" + "".join([w.capitalize() for w in key.split("_")]) 
        latex_cmds.append(f"\\newcommand{{\\{cmd_name}}}{{{val}}}")
        
    # Parameters
    for key, val in data.get("parameters", {}).items():
        cmd_name = "param" + "".join([w.capitalize() for w in key.split("_")])
        latex_cmds.append(f"\\newcommand{{\\{cmd_name}}}{{{val}}}")
        
    if os.path.exists(macros_path):
        with open(macros_path, "a") as f:
            f.write("\n% --- Auto-Injected Results (Data Bridge) ---\n")
            f.write("\n".join(latex_cmds))
            f.write("\n")

def inject_figures(content_path: str, figures_dir: str):
    """
    Scans figures_dir and appends LaTeX figure blocks to content_path.
    """
    if not os.path.exists(figures_dir): return
        
    figures = [f for f in os.listdir(figures_dir) if f.endswith(".png")]
    if not figures: return

    latex_figs = ""
    for fig in figures:
        caption = fig.replace("plot_", "").replace(".png", "").replace("_", " ").title()
        latex_figs += f"""
\\begin{{figure}}[t]
  \\centering
  \\vspace{{1em}}
  \\includegraphics[width=0.98\\linewidth]{{{fig}}}
  \\vspace{{0.5em}}
  \\caption{{{caption} Analysis}}
  \\label{{fig:{fig.replace('.png','')}}}
\\end{{figure}}
"""
    
    with open(content_path, "a") as f:
        f.write("\n% --- Auto-Injected Figures ---\n")
        f.write(latex_figs)

async def compile_pdf_xetex(work_dir: str, tex_file: str, template_root: str = None) -> bool:
    """
    Compiles LaTeX using xelatex with environment awareness.
    Returns True if success.
    """
    env = os.environ.copy()
    env["PATH"] = env.get("PATH", "") + ":/Library/TeX/texbin:/usr/texbin:/usr/local/bin"
    
    if template_root and os.path.exists(template_root):
        # TEXINPUTS: Current . : Template Root // : System Defaults
        env["TEXINPUTS"] = f".:{template_root}//:" + env.get("TEXINPUTS", "")
        
    try:
        cmd = ["xelatex", "-interaction=nonstopmode", tex_file]
        proc = await asyncio.create_subprocess_exec(
            *cmd, cwd=work_dir, env=env,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        return proc.returncode == 0
    except Exception:
        return False
