import re
from typing import List, Dict, Any, Tuple
from .entry_ops import normalize_key_title

"""
Atomic BibTex Fixing Operations.
Pure functions for linting, cleaning, and formatting.
"""

def deduplicate_entries(entries: List[Dict[str, str]]) -> Tuple[List[Dict[str, str]], int]:
    """
    Removes duplicates based on normalized title.
    Keeps the entry with more fields.
    Returns (cleaned_list, count_removed).
    """
    unique_map = {}
    original_count = len(entries)
    
    for entry in entries:
        title = entry.get('title', '')
        # Fallback to citation key if title missing
        key = normalize_key_title(title) if title else entry.get('citation_key')
        
        if not key: continue
        
        if key in unique_map:
            # Conflict: Keep the one with more fields
            existing = unique_map[key]
            if len(entry) > len(existing):
                unique_map[key] = entry
        else:
            unique_map[key] = entry
            
    cleaned = list(unique_map.values())
    return cleaned, original_count - len(cleaned)

def standardize_venue(venue: str) -> str:
    """Standardizes common venue names."""
    v = venue.lower()
    if "cvpr" in v: return "Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)"
    if "iccv" in v: return "Proceedings of the IEEE/CVF International Conference on Computer Vision (ICCV)"
    if "eccv" in v: return "Proceedings of the European Conference on Computer Vision (ECCV)"
    if "neurips" in v or "nips" in v: return "Advances in Neural Information Processing Systems (NeurIPS)"
    if "iclr" in v: return "International Conference on Learning Representations (ICLR)"
    if "icml" in v: return "International Conference on Machine Learning (ICML)"
    return venue

def escape_latex(text: str) -> str:
    """Escapes common LaTeX special characters."""
    # Simple heuristic to avoid double escaping
    # Only escape & and % and _ if not preceded by \
    text = re.sub(r'(?<!\\)&', r'\\&', text)
    text = re.sub(r'(?<!\\)%', r'\%', text)
    text = re.sub(r'(?<!\\)_', r'\_', text)
    return text

def protect_title_case(title: str) -> str:
    """Wraps acronyms in braces."""
    words = title.split()
    new_words = []
    for w in words:
        clean_w = w.strip("{},.:;")
        if clean_w.isupper() and len(clean_w) > 1 and "{" not in w:
             replaced = w.replace(clean_w, f"{{{clean_w}}}")
             new_words.append(replaced)
        else:
             new_words.append(w)
    return " ".join(new_words)

def apply_standard_fixes(entry: Dict[str, str]) -> int:
    """
    Applies in-place fixes to a single entry.
    Returns number of modifications.
    """
    fixes = 0
    
    # 1. Venue
    if 'booktitle' in entry:
        old = entry['booktitle']
        entry['booktitle'] = standardize_venue(old)
        if entry['booktitle'] != old: fixes += 1
    if 'journal' in entry:
        old = entry['journal']
        entry['journal'] = standardize_venue(old)
        if entry['journal'] != old: fixes += 1
        
    # 2. Latex Escaping
    for k, v in entry.items():
        if k not in ['citation_key', 'entry_type']:
            new_v = escape_latex(v)
            if new_v != v:
                entry[k] = new_v
                fixes += 1
                
    # 3. Title Case
    if 'title' in entry:
        old = entry['title']
        entry['title'] = protect_title_case(old)
        if entry['title'] != old: fixes += 1
        
    # 4. Et al. fix
    if 'author' in entry:
        if " et al." in entry['author'] or " et al" in entry['author']:
            entry['author'] = entry['author'].replace(" et al.", " and others").replace(" et al", " and others")
            fixes += 1
            
    # 5. ArXiv Phantom Fields cleanup
    if 'journal' in entry and 'arxiv' in entry['journal'].lower():
        for phantom in ['pages', 'number', 'volume', 'address', 'publisher']:
            if phantom in entry: 
                del entry[phantom]
                # Not counting as fix, just cleanup
                
    return fixes
