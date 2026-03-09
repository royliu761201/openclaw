from typing import List, Dict, Any, Optional
import os
import re
from .base_skill import BaseSkill
from .bibtex_ops import entry_ops, fix_ops

class BibTexManager(BaseSkill):
    """
    Manages bibliography generation, merging, and linting.
    Consolidated Skill using atomic `bibtex_ops`.
    """
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)

    def verify(self) -> bool:
        return True
        
    def generate_bibtex(self, search_results: List[Dict]) -> str:
        """
        Converts search results [{'title':..., 'url':...}] to BibTeX entries.
        """
        # This logic is specific to "generating new entries from scratch", 
        # distinct from parsing existing files.
        bib_entries = []
        for i, res in enumerate(search_results):
            title = res.get('title', 'Unknown')
            # Use entry_ops for key generation? Or custom?
            # Let's use simple logic here as it's ad-hoc generation
            key_base = entry_ops.normalize_key_title(title)[:15]
            key = f"ref{i}_{key_base}"
            
            raw_url = res.get('url', '')
            # Simple heuristic
            if "arxiv.org" in raw_url: pass 
            
            entry = f"""@misc{{{key},
  title = {{{title}}},
  howpublished = {{\\url{{{raw_url}}}}},
  note = {{Accessed: 2026}}
}}"""
            bib_entries.append(entry)
            
        return "\n\n".join(bib_entries)

    def merge_and_save(self, new_search_results: List[Dict], output_dir: str):
        """
        Smart Merge: Reads existing refs.bib, dedupes, and appends new entries.
        Uses `entry_ops` for robust parsing/checking.
        """
        path = os.path.join(output_dir, "refs.bib")
        
        # 1. Read Existing
        existing_entries = entry_ops.parse_bibtex_file(path)
        existing_keys = {entry_ops.normalize_key_title(e.get('title', '')) for e in existing_entries if e.get('title')}
        
        # 2. Process New
        new_text_entries = []
        added_count = 0
        
        for res in new_search_results:
            title = res.get('title', 'Unknown')
            if not title: continue
            
            # Secondary Safety Filter
            if "amazonaws.com" in title.lower() or "grounding-api-redirect" in res.get('url', '').lower():
                continue
                
            norm_title = entry_ops.normalize_key_title(title)
            
            if norm_title in existing_keys:
                continue # Skip Duplicate
                
            # Create Entry (Text format for appending)
            key = f"ref_new_{norm_title[:15]}"
            raw_url = res.get('url', '')
            
            entry_str = f"""@misc{{{key},
  title = {{{title}}},
  howpublished = {{\\url{{{raw_url}}}}},
  note = {{Accessed: 2026}}
}}"""
            new_text_entries.append(entry_str)
            existing_keys.add(norm_title)
            added_count += 1
            
        # 3. Append
        if new_text_entries:
            mode = "a" if os.path.exists(path) else "w"
            with open(path, mode, encoding="utf-8") as f:
                if mode == "a": f.write("\n")
                f.write("\n% --- Auto-Merged New References ---\n")
                f.write("\n\n".join(new_text_entries))
            print(f"[BibTexManager] 🔗 Merged {added_count} new entries into refs.bib")
        else:
            print("[BibTexManager] No new unique references to add.")

    async def lint_and_format(self, bib_path: str) -> Dict[str, int]:
        """
        Lints and Cleanups the BibTeX file.
        Replaces the old `BibTexLinter`.
        """
        if not os.path.exists(bib_path):
             return {"status": "file_not_found"}
             
        # 1. Parse
        entries = entry_ops.parse_bibtex_file(bib_path)
        original_count = len(entries)
        
        # 2. Dedup
        cleaned_entries, dup_removed = fix_ops.deduplicate_entries(entries)
        
        # 3. Apply Fixes
        fix_count = 0
        for entry in cleaned_entries:
            fix_count += fix_ops.apply_standard_fixes(entry)
            
        # 4. Write Back
        entry_ops.write_bibtex_file(cleaned_entries, bib_path)
        
        print(f"[BibTexManager] Lint Complete: {dup_removed} dups removed, {fix_count} format fixes.")
        
        return {
            "original": original_count,
            "final": len(cleaned_entries),
            "duplicates_removed": dup_removed,
            "fixes": fix_count
        }

    def validate_policy(self, bib_path: str, min_count: int = 35, recency_ratio: float = 0.5, recent_year: int = 2023) -> Dict[str, Any]:
        """
        Enforces Scientific Taste Policy.
        """
        # Parse using Ops
        entries = entry_ops.parse_bibtex_file(bib_path)
        total_count = len(entries)
        
        recent_count = 0
        for e in entries:
            y_str = e.get('year', '0')
            # Extract number
            match = re.search(r'\d{4}', y_str)
            if match:
                y = int(match.group(0))
                if y >= recent_year: recent_count += 1
                
        actual_ratio = recent_count / total_count if total_count > 0 else 0
        valid = (total_count >= min_count) and (actual_ratio >= recency_ratio)
        
        report = {
            "valid": valid,
            "total_count": total_count,
            "min_count": min_count,
            "recent_count": recent_count,
            "actual_ratio": round(actual_ratio, 2),
            "required_ratio": recency_ratio
        }
        
        if not valid:
             print(f"[BibTexManager] ❌ Policy Violation: {total_count} refs ({recent_count} recent).")
        else:
             print(f"[BibTexManager] ✅ Policy Passed.")
             
        return report

