import os
import re
import sys
from pathlib import Path

def lint_citations(paper_dir):
    paper_path = Path(paper_dir)
    bib_file = paper_path / "refs.bib"
    
    if not bib_file.exists():
        print(f"Error: {bib_file} not found.")
        sys.exit(1)
        
    with open(bib_file, 'r', encoding='utf-8') as f:
        bib_content = f.read()
        
    # Extract citation keys from .bib file
    bib_keys = set(re.findall(r'@\w+\{([^,]+),', bib_content))
    print(f"[{len(bib_keys)}] References loaded from refs.bib")
    
    # Extract all \cite{...} from .tex files
    tex_files = list(paper_path.glob('**/*.tex'))
    cited_keys = set()
    
    for tex_file in tex_files:
        with open(tex_file, 'r', encoding='utf-8') as f:
            content = f.read()
            # Match \cite{key1, key2}
            cites = re.findall(r'\\cite\{([^}]+)\}', content)
            for cite in cites:
                # Split by comma and strip whitespace
                keys = [k.strip() for k in cite.split(',')]
                cited_keys.update(keys)
                
    print(f"[{len(cited_keys)}] Unique references cited in text")
    
    # Orphans (in bib but not cited)
    orphans = bib_keys - cited_keys
    # Ghosts (cited but not in bib)
    ghosts = cited_keys - bib_keys
    
    if orphans:
        print(f"\n[ORPHANS FOUND] {len(orphans)} references in bib but never cited in text:")
        for orphan in sorted(list(orphans)):
            print(f" - {orphan}")
            
    if ghosts:
        print(f"\n[GHOSTS FOUND] {len(ghosts)} references cited in text but missing from bib:")
        for ghost in sorted(list(ghosts)):
            print(f" - {ghost}")
            
    if not orphans and not ghosts:
        print("\n✅ Verification SUCCESS. 0 Orphans. 0 Ghosts.")
        return 0
    else:
        print("\n❌ Verification FAILED. Fix orphans and ghosts.")
        return 1

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python lint_manuscript.py <paper_dir>")
        sys.exit(1)
        
    sys.exit(lint_citations(sys.argv[1]))
