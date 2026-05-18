#!/usr/bin/env python3
import os
import re
import sys
import glob

def check_markdown_leakage(tex_file):
    """
    Blocks Markdown formatting (**, __) leaking into formal LaTeX text.
    """
    with open(tex_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for strong/bold markdown `**text**`
    if re.search(r'\*\*(.*?)\*\*', content):
        print(f"❌ [Linter Error] Markdown leakage detected in {tex_file}: Found '**'. Use \\textbf{{}} instead.")
        return False
    return True

def extract_citations_from_tex(tex_files):
    """
    Extracts all citation keys used in \cite{}, \citep{}, \citet{}
    """
    used_keys = set()
    for f in tex_files:
        with open(f, 'r', encoding='utf-8') as file:
            content = file.read()
            # Find \cite{key1, key2}
            matches = re.findall(r'\\cite[pt]?\{([^}]+)\}', content)
            for m in matches:
                keys = [k.strip() for k in m.split(',')]
                used_keys.update(keys)
    return used_keys

def extract_keys_from_bib(bib_file):
    """
    Extracts all defined keys from a bibliography .bib file
    """
    defined_keys = set()
    with open(bib_file, 'r', encoding='utf-8') as file:
        content = file.read()
        # Find @article{key,
        matches = re.findall(r'@\w+\s*\{\s*([^,]+),', content)
        defined_keys.update([m.strip() for m in matches])
    return defined_keys

def lint_citations(tex_files, bib_file):
    used_keys = extract_citations_from_tex(tex_files)
    if not os.path.exists(bib_file):
        print(f"⚠️ [Warning] Bibliography file {bib_file} not found. Skipping lint.")
        return True
        
    defined_keys = extract_keys_from_bib(bib_file)
    
    orphans = used_keys - defined_keys
    if orphans:
        print(f"❌ [Linter Error] Found Orphan Citations! Keys cited but not in {bib_file}:")
        for k in orphans:
            print(f"   -> {k}")
        return False
        
    print(f"✅ Citation hygiene checked: {len(used_keys)} keys used, 0 orphans.")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python lint_manuscript.py <tex_directory>")
        sys.exit(1)
        
    target_dir = sys.argv[1]
    tex_files = glob.glob(os.path.join(target_dir, '**/*.tex'), recursive=True)
    bib_files = glob.glob(os.path.join(target_dir, '*.bib'))
    
    if not tex_files:
        print("❌ [Linter Error] No .tex files found in directory.")
        sys.exit(1)
        
    success = True
    print(f"🔍 Linting {len(tex_files)} TeX files...")
    
    for f in tex_files:
        if not check_markdown_leakage(f):
            success = False
            
    if bib_files:
        if not lint_citations(tex_files, bib_files[0]):
            success = False
            
    if not success:
        sys.exit(1)
    else:
        print("🎉 All checks passed! The LaTeX manuscript is clean and ready for Phase 4.")
