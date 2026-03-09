import re
import os
from typing import List, Dict, Any

"""
Atomic BibTex Entry Operations.
Pure functions for parsing, writing, and key normalization.
"""

def parse_bibtex_file(path: str) -> List[Dict[str, str]]:
    """
    Simple Regex Parser to avoid complex dependencies.
    Returns list of dicts with 'entry_type' and 'citation_key'.
    """
    if not os.path.exists(path):
        return []
        
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    entries = []
    # robust split by @ at start of line
    # but many files are one-line. Simple split by @ is heuristic.
    raw_chunks = content.split("@")
    
    for chunk in raw_chunks:
        chunk = chunk.strip()
        if not chunk or chunk.startswith("%"): continue
        
        # Extract Type and Body
        if "{" not in chunk: continue
        try:
            entry_type, rest = chunk.split("{", 1)
            entry_type = entry_type.strip().lower()
            
            # Key is usually before the first comma
            if "," not in rest: continue
            
            citation_key, fields_block = rest.split(",", 1)
            citation_key = citation_key.strip()
            
            fields = {'entry_type': entry_type, 'citation_key': citation_key}
            
            # Parse lines for key=value
            lines = fields_block.split("\n")
            for line in lines:
                line = line.strip()
                if "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip().lower()
                    v = v.strip()
                    # Clean value (imperfect regex replacement)
                    v = v.rstrip(",").strip('}').strip('"').strip("{")
                    if k and v:
                        fields[k] = v
            
            entries.append(fields)
        except Exception:
            continue
            
    return entries

def write_bibtex_file(entries: List[Dict[str, str]], path: str):
    """Writes list of entries to .bib file."""
    with open(path, 'w', encoding='utf-8') as f:
        for e in entries:
            etype = e.get('entry_type', 'misc')
            key = e.get('citation_key', 'unknown')
            f.write(f"@{etype}{{{key},\n")
            for k, v in e.items():
                if k in ['entry_type', 'citation_key']: continue
                f.write(f"  {k} = {{{v}}},\n")
            f.write("}\n\n")

def normalize_key_title(title: str) -> str:
    """Normalized title for deduplication (lowercase, alphanumeric only)."""
    return re.sub(r'[^a-z0-9]', '', title.lower())

def create_citation_key(title: str, year: str = "", author: str = "") -> str:
    """Generates a standard citation key."""
    # Pattern: AuthorYearWord or WordYear
    title_slug = re.sub(r'[^a-zA-Z0-9]', '', title)[:10]
    return f"{title_slug}{year}"
