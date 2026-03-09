import os
import shutil
import re
from typing import Dict, Any, Optional
import asyncio

# Lazy import to avoid circular dependencies if any, though likely fine here
# from core.model_client import ModelClient
# from config import ModelTier

class LatexArchitect:
    """
    The 'Paper Architect'.
    Responsible for scaffolding the LaTeX project structure based on a template.
    Does NOT write content, only structural files and macros.
    """
    def __init__(self, template_dir: str = "research_vault/templates", model_client = None):
        self.template_dir = template_dir
        self.model_client = model_client
        self.healer = None
        
        # Lazy load if not provided
        if not self.model_client:
            try:
                from core.model_client import ModelClient
                self.model_client = ModelClient()
            except ImportError:
                print("[Architect] ⚠️ Could not import ModelClient. LLM healing disabled.")

        if self.model_client:
            try:
                from skills.healer import UniversalHealer
                self.healer = UniversalHealer(self.model_client)
            except ImportError:
                 print("[Architect] ⚠️ Could not import UniversalHealer.")

    def scaffold_paper(self, idea_id: str, title: str, output_dir: str, template_name: str = "neurips_2026.tex") -> Dict[str, str]:
        """
        Creates a new LaTeX project structure for the given Idea ID.
        """
        print(f"[Architect] Scaffolding paper for {idea_id} in {output_dir} using {template_name}...")
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        sections_dir = os.path.join(output_dir, "sections")
        os.makedirs(sections_dir, exist_ok=True)
        
        # Define Sections (Single Source of Truth)
        # Note: We enforce sequential numbering here
        exp_content = r"""
\section{Experiments}
\subsection{Experimental Setup}
Description of datasets and metrics.

\subsection{Baselines}
Comparison with standard methods.

\subsection{Ablation Study}
Analysis of component contributions.

\subsection{Case Study}
Qualitative analysis of specific examples.
"""
        disc_content = r"""
\section{Discussion}
\subsection{Limitations}
Honest discussion of failure cases.

\section{Conclusion}
Summary and future work.
"""
        
        sections_map = [
            ("00_abstract.tex", "Abstract goes here..."),
            ("01_introduction.tex", "Introduction goes here..."),
            ("02_related_work.tex", "Related Work goes here..."),
            ("03_method.tex", "Method description..."),
            ("04_experiments.tex", exp_content),
            ("05_discussion.tex", disc_content)
        ]
        
        # Create Section Files
        created_files = []
        for fname, content in sections_map:
            self._create_section(sections_dir, fname, content)
            created_files.append(fname)
        
        # 2. macros.tex (Centralized definition of metrics/results)
        macros_path = os.path.join(output_dir, "macros.tex")
        self._create_macros_tex(macros_path)
        
        # 1. main.tex (Now dynamic based on created_files)
        main_tex_path = os.path.join(output_dir, "main.tex")
        self._create_main_tex(main_tex_path, title, template_name, created_files)
        
        return {
            "main": main_tex_path,
            "macros": macros_path,
            "dir": output_dir
        }

    def _create_main_tex(self, path: str, title: str, template_name: str, section_files: list[str]):
        # Allow switching templates. Default: neurips_2024
        # Construct dynamic input block
        input_block = "\n".join([f"\\input{{sections/{f.replace('.tex', '')}}}" for f in section_files])
        
        content = ""
        # 1. Try to load from template file
        template_path = os.path.join(self.template_dir, template_name)
        
        # Recursive Search if not in root
        if not os.path.exists(template_path):
             for root, dirs, files in os.walk(self.template_dir):
                 if template_name in files:
                     template_path = os.path.join(root, template_name)
                     print(f"[Architect] 🔍 Found template in subdir: {template_path}")
                     break
        
        if os.path.exists(template_path):
             print(f"[Architect] Loading template: {template_name}")
             with open(template_path, "r") as f:
                 content = f.read()
             # Replace Placeholders
             content = content.replace("<<TITLE>>", title)
             
             # Smart Input Replacement: Attempt to replace existing section inputs with ours
             # Heuristic: Replace the block between \maketitle and \bibliographystyle, or find \input{sections/00...}
             # For now, if we match the standard fallback pattern, we replace it.
             # Ideally, we should regex replace `\\input\{sections\/.*?\}`
             import re
             if "sections/00_abstract" in content:
                 # Assume standard block. Replace all inputs to sections/
                 content = re.sub(r'\\input\{sections/.*?\}', '', content)
                 # Re-inject after maketitle
                 content = content.replace(r'\maketitle', f'\\maketitle\n{input_block}')
        else:
             # 2. Fallback to hardcoded if template missing
             print(f"[Architect] ❌ Template {template_name} not found in {self.template_dir}. Using fallback.")
             content = r"""
\documentclass{article}
% User Request: Anonymous Submission by Default
\usepackage[utf8]{inputenc} 
\usepackage[T1]{fontenc}
\usepackage{graphicx}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{algorithm}
\usepackage{algorithmic}
\usepackage{booktabs}
\usepackage{neurips_2026}
\usepackage{geometry}

\input{macros}

\title{""" + title + r"""}
\author{Anonymous Author(s)}
\date{}

\begin{document}
\maketitle
""" + input_block + r"""
\bibliographystyle{plain}
\bibliography{refs}
\end{document}
"""
        with open(path, "w") as f:
            f.write(content)

    def _create_macros_tex(self, path: str):
        content = r"""
% Defines the "Dynamic Truth" of the paper.
% These values are updated automatically by the LatexWriter based on experimental results.

\newcommand{\OurMethodName}{NexusNet}
\newcommand{\AccuracyResult}{PENDING}
\newcommand{\SpeedupResult}{PENDING}
"""
        with open(path, "w") as f:
            f.write(content)

    def _create_section(self, dir_path: str, filename: str, placeholder: str):
        with open(os.path.join(dir_path, filename), "w") as f:
            f.write(f"% {filename}\n{placeholder}")

    def lint_project(self, output_dir: str) -> list[str]:
        """
        Performs static analysis on LaTeX files.
        Checks for:
        1. Straight quotes (") instead of smart quotes (`` '').
        2. Missing .bib entries.
        """
        warnings = []
        tex_files = [f for f in os.listdir(output_dir) if f.endswith(".tex")] or \
                    [f for f in os.listdir(os.path.join(output_dir, "sections")) if f.endswith(".tex")]
        
        # 1. Quote Check
        for fname in tex_files:
            path = os.path.join(output_dir, fname) if os.path.exists(os.path.join(output_dir, fname)) \
                   else os.path.join(output_dir, "sections", fname)
            
            if not os.path.exists(path): continue
            
            with open(path, "r") as f:
                content = f.readlines()
                
            for i, line in enumerate(content):
                if '"' in line and not line.strip().startswith("%"):
                    # Exclude macro definitions or some commands
                    warnings.append(f"⚠️ Typo: Straight quote found in {fname}:{i+1}. Use `` or ''.")

        return warnings

    def auto_polish_tex(self, output_dir: str):
        """
        Auto-corrects common LaTeX issues:
        1. Straight quotes (") -> Smart quotes (`` '').
        2. Unescaped percentages (95%) -> (95\%).
        3. Simple ellipses (...) -> \dots.
        """
        import re
        tex_files = []
        for root, _, files in os.walk(output_dir):
            for file in files:
                if file.endswith(".tex"):
                    tex_files.append(os.path.join(root, file))

        for path in tex_files:
            with open(path, "r") as f: content = f.read()
            
            # 1. Quotes State Machine (Preserved)
            new_content = []
            open_quote = False
            for i, char in enumerate(content):
                if char == '"':
                    if i > 0 and content[i-1] == '\\':
                         new_content.append('"')
                         continue
                    if not open_quote:
                        new_content.append("``")
                        open_quote = True
                    else:
                        new_content.append("''")
                        open_quote = False
                else:
                    new_content.append(char)
            content = "".join(new_content)

            # 2. Percentages (digits followed by %, not already escaped)
            # Regex: Look behind for digit, look ahead for %, ensure not escaped
            content = re.sub(r'(?<=\d)%', r'\\%', content)

            # 3. Ellipses
            content = content.replace("...", r"\dots")

            with open(path, "w") as f: f.write(content)
            print(f"[Architect] ✨ Polished {os.path.basename(path)}")


    def _heal_from_log(self, output_dir: str, log: str) -> bool:
        """
        Parses LaTeX log for common errors and attempts corrections.
        Returns True if a fix was applied.
        """
        main_tex = os.path.join(output_dir, "main.tex")
        with open(main_tex, "r") as f: content = f.read()
        fixed = False

        # Error 1: Missing Package (Environment undefined)
        # Log: ! LaTeX Error: Environment algorithm undefined.
        if "Environment algorithm undefined" in log:
            if "\\usepackage{algorithm}" not in content:
                content = content.replace("\\usepackage{geometry}", "\\usepackage{geometry}\n\\usepackage{algorithm}\n\\usepackage{algorithmic}")
                print("[Architect] 🚑 Healing: Added algorithm package")
                fixed = True

        # Error 2: Missing Package (Undefined control sequence \mathbb)
        if "Undefined control sequence" in log and "\\mathbb" in log and "amssymb" not in content:
             content = content.replace("\\usepackage{geometry}", "\\usepackage{geometry}\n\\usepackage{amssymb}")
             print("[Architect] 🚑 Healing: Added amssymb for \\mathbb")
             fixed = True

        # Error 3: Bad UTF-8 chars
        # ! Package inputenc Error: Unicode char
        if "inputenc Error: Unicode char" in log:
             # Force clean non-ascii if strictly needed, or ensure inputenc is there
             pass 

        # Error 4: Undefined URL (Missing package)
        # Log: ! Undefined control sequence. ... \url
        if ("Undefined control sequence" in log and "\\url" in log) or ("File `url.sty' not found" in log):
             if "\\usepackage{url}" not in content:
                 content = content.replace("\\usepackage{geometry}", "\\usepackage{geometry}\n\\usepackage{url}\n\\usepackage{hyperref}")
                 print("[Architect] 🚑 Healing: Added url/hyperref packages")
                 fixed = True

        if "\\bibliographystyle{" not in content:
            # Default to plainnat if not specified, or fix the broken icml2026 style
            content = content.replace("\\end{document}", "\\bibliographystyle{plainnat}\n\\bibliography{refs}\n\\end{document}")
        else:
             # Fix the broken style reference if present
             content = content.replace("\\bibliographystyle{icml2026}", "\\bibliographystyle{plainnat}")
        
        # Ensure natbib is loaded for \citep
        if "\\usepackage{natbib}" not in content:
             content = content.replace("\\usepackage{icml2026}", "\\usepackage{natbib}\n\\usepackage{icml2026}")

        with open(main_tex, "w") as f: f.write(content)
        
        # Error 5: Missing Figures (File not found)
        # Log: ! LaTeX Error: File `figures/plot.pdf' not found.
        # Log: ! Unable to load picture or PDF file 'figures/plot.pdf'.
        missing_file_matches = re.findall(r"File `(.*?)' not found", log) + re.findall(r"file '(.*?)'", log)
        if "unable to load picture" in log.lower() or "not found" in log.lower():
             for match in missing_file_matches:
                 # Check if it looks like an image
                 if any(match.lower().endswith(ext) for ext in ['.pdf', '.png', '.jpg', '.jpeg']):
                     missing_path = os.path.join(output_dir, match)
                     
                     if not os.path.exists(missing_path):
                         print(f"[Architect] 🚑 Healing: Generating placeholder for missing figure: {match}")
                         os.makedirs(os.path.dirname(missing_path), exist_ok=True)
                         
                         # Create minimal valid PNG (1x1 white pixel)
                         # Signature: \x89PNG\r\n\x1a\n ...
                         # This allows compilation to succeed even if the visual is a dot.
                         minimal_png = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
                         
                         # If original was PDF, we just save as .pdf but with png content? 
                         # LaTeX might complain about headers if extension mismatch.
                         # Safer: Try to create an empty PDF text file if PDF, or binary PNG if PNG.
                         
                         if match.lower().endswith('.pdf'):
                             # Minimal PDF 1.0
                             minimal_pdf = b'%PDF-1.0\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 3 3]/Resources<<>>/Parent 2 0 R>>endobj\nxref\n0 4\n0000000000 65535 f\n0000000010 00000 n\n0000000060 00000 n\n0000000157 00000 n\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n249\n%%EOF'
                             with open(missing_path, "wb") as f: f.write(minimal_pdf)
                         else:
                             with open(missing_path, "wb") as f: f.write(minimal_png)
                             
                         fixed = True

        # Error 6: Layout Overflow (Overfull \hbox)
        if "Overfull \\hbox" in log:
             print("[Architect] 📏 Detected layout overflow. Attempting Auto-Fix...")
             if self._auto_fix_overflow(output_dir, log):
                 fixed = True
        
        # Error 6: Layout Overflow (Overfull \hbox)
        if "Overfull \\hbox" in log:
             print("[Architect] 📏 Detected layout overflow. Attempting Auto-Fix...")
             if self._auto_fix_overflow(output_dir, log):
                 fixed = True
        
        # Fallback: General LLM Healing via UniversalHealer
        if not fixed and self.healer:
            print("[Architect] 🧠 Hardcoded fixes failed. Consulting UniversalHealer...")
            import asyncio
            try:
                # Synchronous wrapper for async call
                main_tex_path = os.path.join(output_dir, "main.tex")
                with open(main_tex_path, "r") as f: main_content = f.read()
                
                new_content = asyncio.run(self.healer.heal_content(
                    content=main_content,
                    error_log=log,
                    file_type="LaTeX",
                    context="Fix compilation errors in main.tex"
                ))
                
                if new_content and "\\documentclass" in new_content:
                    shutil.copy(main_tex_path, main_tex_path + ".bak")
                    with open(main_tex_path, "w") as f: f.write(new_content)
                    print("[Architect] 🚑 UniversalHealer Applied Fix.")
                    fixed = True
                    
            except Exception as e:
                 print(f"[Architect] ❌ UniversalHealer Failed: {e}")

        return fixed

    def _auto_fix_overflow(self, output_dir: str, log: str) -> bool:
        """
        Scans log for 'Overfull \hbox' and wraps offending LaTeX layouts.
        Target: Tables (resizebox), Images (width), Code (breaklines).
        """
        import re
        
        # Pattern: Overfull \hbox (15.5pt too wide) in paragraph at lines 105--106
        matches = re.findall(r"Overfull \\hbox .*? lines (\d+)--(\d+)", log)
        if not matches: 
            return False
            
        fixed_any = False
        
        # Group by file? Complex. For now, assume errors are in main.tex or included sections.
        # We need to find WHICH file the lines correspond to. 
        # Making a simplification: grep the line content from log context if possible, 
        # OR scan all tex files for tabulars/images and proactively resize them if they lack it.
        
        # PROACTIVE APPROACH: Wrap all tabulars that lack resizebox
        tex_files = []
        for root, _, files in os.walk(output_dir):
            for file in files:
                if file.endswith(".tex"):
                    tex_files.append(os.path.join(root, file))
                    
        for path in tex_files:
            with open(path, "r") as f: content = f.read()
            original_len = len(content)
            
            # Fix 1: Wrap \begin{tabular} in \resizebox if not present
            # Look for: \begin{tabular}{...} ... \end{tabular}
            # This regex is simple and might fail on nested braces, but works for standard generated tables.
            # We use a safer replacement helper.
            
            lines = content.split('\n')
            new_lines = []
            in_table = False
            table_buffer = []
            
            for line in lines:
                if "\\begin{tabular}" in line and "\\resizebox" not in line:
                    new_lines.append("\\resizebox{\\columnwidth}{!}{%")
                    new_lines.append(line)
                    in_table = True
                elif "\\end{tabular}" in line and in_table:
                    new_lines.append(line)
                    new_lines.append("}%")
                    in_table = False
                else:
                    new_lines.append(line)
                    
            content = "\n".join(new_lines)
            
            # Fix 2: Wrap verbatims/texttt in sloppypar or scriptsize? 
            # Often URLs causes this. 
            # We can globally add \sloppy to the preamble if not present.
            
            if len(content) != original_len:
                with open(path, "w") as f: f.write(content)
                print(f"[Architect] 📐 Resize-Fixed Tables in {os.path.basename(path)}")
                fixed_any = True
                
        return fixed_any

    def switch_template(self, output_dir: str, template_name: str) -> bool:
        """
        Switches the LaTeX template (e.g., 'icml2026' -> 'neurips_2026').
        Handles package conflicts (natbib) and missing dependencies (algorithm).
        """
        print(f"[Architect] 🔄 Switching template to {template_name}...")
        
        # 1. Locate Source Template
        # Try finding .sty in templates dir (recursively or standard paths)
        # For simplicity, we assume standard paths based on recent usage
        if "neurips" in template_name:
            src_style = os.path.join(self.template_dir, "paper/neurips", f"{template_name}.sty")
        elif "icml" in template_name:
            src_style = os.path.join(self.template_dir, "paper/icml", f"{template_name}.sty")
        else:
            print(f"[Architect] ⚠️ Unknown template category: {template_name}")
            return False

        if not os.path.exists(src_style):
             # Try flat search
             src_style = os.path.join(self.template_dir, f"{template_name}.sty")
        
        if not os.path.exists(src_style):
            print(f"[Architect] ❌ Template file not available: {src_style}")
            return False
            
        # 2. Copy Style File -> DISABLED (Using TEXINPUTS)
        # import shutil
        # dest_style = os.path.join(output_dir, f"{template_name}.sty")
        # shutil.copy(src_style, dest_style)
        # print(f"[Architect] 📄 Installed {dest_style}")
        print(f"[Architect] 🔗 configured to use {template_name} (via ENV)")
        
        # 3. Update main.tex
        main_tex = os.path.join(output_dir, "main.tex")
        with open(main_tex, 'r') as f: content = f.read()
        
        # A. Remove old style packages (heuristic)
        import re
        content = re.sub(r'\\usepackage\{icml\d+\}', '', content)
        content = re.sub(r'\\usepackage\{neurips\_\d+\}', '', content)
        
        # B. Inject new style
        # Inject before title or after standard packages
        if "\\title{" in content:
            content = content.replace("\\title{", f"\\usepackage{{{template_name}}}\n\\title{{")
        else:
            content = content.replace("\\begin{document}", f"\\usepackage{{{template_name}}}\n\\begin{{document}}")
            
        # C. Handle Conflicts (Smart Heuristics)
        if "neurips" in template_name:
            # NeurIPS includes natbib options, so comment out explicit natbib to avoid "Option clash"
            content = content.replace("\\usepackage{natbib}", "% \\usepackage{natbib} % Handled by neurips style")
            # NeurIPS often lacks algorithm envs by default unless using 'algorithm' package
            if "\\usepackage{algorithm}" not in content:
                content = content.replace(f"\\usepackage{{{template_name}}}", f"\\usepackage{{{template_name}}}\n\\usepackage{{algorithm}}\n\\usepackage{{algorithmic}}")
        elif "icml" in template_name:
            # ICML needs explicit natbib usually, or handles it differently
            content = content.replace("% \\usepackage{natbib}", "\\usepackage{natbib}")
            
        with open(main_tex, 'w') as f: f.write(content)
        print("[Architect] 📝 Updated main.tex inclusions.")
        return True

    def compile_pdf(self, output_dir: str) -> Dict[str, Any]:
        """
        Compiles the LaTeX project into a PDF using 'latexmk' (Smart/Incremental).
        Uses TEXINPUTS to link templates without copying.
        """
        import subprocess
        
        # 0. Pre-Flight Polish & Bib Fix
        self.auto_polish_tex(output_dir)
        self._heal_from_log(output_dir, "FORCE_CHECK")
        
        main_tex = "main.tex"
        
        # A. Configure Environment (Smart Templates)
        env = os.environ.copy()
        env["PATH"] = env["PATH"] + ":/Library/TeX/texbin:/usr/texbin:/usr/local/bin"
        
        # Set TEXINPUTS to include template dir
        # Structure: . : {template_dir}// : System
        template_root = os.path.abspath(self.template_dir)
        env["TEXINPUTS"] = f".:{template_root}//:" + env.get("TEXINPUTS", "")
        
        print(f"[Architect] 🔧 TEXINPUTS={env['TEXINPUTS']}")

        def run_latexmk():
            try:
                # -pdf: Generate PDF
                # -interaction=nonstopmode: Don't halt on error
                # -outdir=.: Output to same dir
                # -f: Force compilation even if errors
                cmd = ["latexmk", "-pdf", "-interaction=nonstopmode", "-f", main_tex]
                
                proc = subprocess.run(
                    cmd,
                    cwd=output_dir, env=env,
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, check=True
                )
                return True, proc.stdout
            except subprocess.CalledProcessError as e:
                return False, e.stdout

        # 1. Compilation (Single Smart Pass)
        print(f"[Architect] 🚀 Compiling PDF (Incremental Mode via latexmk)...")
        success, output = run_latexmk()
        
        # 🚨 WARNING FIX (Active Repair on Warnings)
        # Even if success, check for layout issues and fix them
        if success and "Overfull \\hbox" in output:
             print("[Architect] ⚠️ Compilation Success, but Layout Warnings detected.")
             if self._auto_fix_overflow(output_dir, output):
                 print("[Architect] 🚑 Layout fixes applied. Recompiling for perfection...")
                 # Force recompile to bake in the fixes
                 success, output = run_latexmk()

        if success:
            print("[Architect] ✅ Compilation Successful.")
        else:
             print("[Architect] ⚠️ Compilation failed. Analyzing log for Auto-Fix...")
             # Try one heal pass
             healed = self._heal_from_log(output_dir, output)
             
             # Also try layout fix
             if "Overfull \\hbox" in output:
                 if self._auto_fix_overflow(output_dir, output):
                     healed = True
                     
             # Try BibTeX Healing
             if self._heal_bibliography(output_dir, output):
                 healed = True
            
             if healed:
                 print("[Architect] 🚑 Fixes applied. Retrying compilation...")
                 success, output = run_latexmk()

        pdf_path = os.path.join(output_dir, "main.pdf")
        
        if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
            print(f"[Architect] ✅ PDF Generated: {pdf_path}")
            return {"success": True, "pdf_path": pdf_path}
        else:
             return {"success": False, "error": "PDF generation failed", "log": output}

    def _heal_bibliography(self, output_dir: str, log: str) -> bool:
        """
        Parses bibtex log (.blg) for syntax errors and attempts repairs in refs.bib.
        Handles: "I was expecting a ','", "Too many commas", "Syntax error"
        """
        import re
        blg_path = os.path.join(output_dir, "main.blg")
        if not os.path.exists(blg_path):
            return False
            
        with open(blg_path, "r") as f: blg_content = f.read()
        bib_path = os.path.join(output_dir, "refs.bib")
        if not os.path.exists(bib_path): return False
        
        with open(bib_path, "r") as f: bib_lines = f.readlines()
        
        fixed = False
        
        # Error Pattern 1: "I was expecting a `,' or a `}'---line 117 of file refs.bib"
        matches = re.findall(r"line (\d+) of file refs.bib", blg_content)
        for line_num_str in matches:
            idx = int(line_num_str) - 1 # 0-indexed
            if 0 <= idx < len(bib_lines):
                # Heuristic: Check for common issues like unescaped chars or missing commas
                line = bib_lines[idx]
                
                # Fix: Missing comma at end of field
                if "=" in line and not line.strip().endswith(",") and not line.strip().endswith("}"):
                    bib_lines[idx] = line.rstrip() + ",\n"
                    print(f"[Architect] 🚑 BibTeX Healing: Added missing comma at line {line_num_str}")
                    fixed = True
                    
                # Fix: Unbalanced braces (simple check)
                if line.count("{") != line.count("}"):
                    # Often caused by unescaped chars. Hard to fix blindly, but we can try to close it?
                    # Safer: Just report it or try standard substitutions
                    pass

        # Error Pattern 2: "Too many commas in name 1 of..."
        # This usually means "Author Name, Jr., and..." format issues.
        if "Too many commas" in blg_content:
             # Global Fix: Scan for author fields and normalize delimiters
             for i, line in enumerate(bib_lines):
                 if "author={" in line or "author = {" in line:
                     # Replace ", and" -> " and" inside braces? 
                     # Or fix specific "Name, Jr.," cases?
                     # Heuristic: Remove trailing commas in author lists if present
                     pass

        if fixed:
            with open(bib_path, "w") as f:
                f.writelines(bib_lines)
                
        return fixed
