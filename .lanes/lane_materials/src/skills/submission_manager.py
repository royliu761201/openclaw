from typing import Dict, List, Any, Optional
import os
import shutil
from datetime import datetime
from skills.base_skill import BaseSkill
from core.model_client import ModelClient
from skills.search_client import SearchClient
from config import ModelTier

class SubmissionManager(BaseSkill):
    """
    Strategic Advisor for Paper Submission.
    - Venue Recommendation (CCF Tiers).
    - Deadline Intelligence.
    - Template Management (Centralized).
    """
    
    def __init__(self, model_client: ModelClient, search_client: SearchClient, template_root: str):
        super().__init__()
        self.client = model_client
        self.search = search_client
        self.template_root = os.path.abspath(template_root)
        self.kb_path = os.path.join(os.path.dirname(self.template_root), "knowledge_base/venues.yaml")
        self.venues_db = []
        self._load_kb()

    def verify(self) -> bool:
        return os.path.exists(self.template_root) and len(self.venues_db) > 0

    def _load_kb(self):
        import yaml
        if os.path.exists(self.kb_path):
            with open(self.kb_path, "r") as f:
                data = yaml.safe_load(f)
                self.venues_db = data.get("venues", [])
                print(f"[SubmissionManager] 📚 Loaded {len(self.venues_db)} venues from Knowledge Base.")
        else:
            print(f"[SubmissionManager] ⚠️ Venue KB not found at {self.kb_path}")

    async def suggest_venues(self, title: str, abstract: str) -> List[Dict[str, Any]]:
        """
        Suggests 3 suitable venues based on content, prioritizing KB entries.
        """
        # 1. First, ask LLM for general matching logic
        venues_str = "\n".join([f"- {v['name']} ({v['tier']}): {', '.join(v.get('preferences', []))}" for v in self.venues_db])
        
        prompt = f"""
        Role: Senior Research Strategist.
        Task: Recommend 3 target venues (Conference/Journal) for this paper.
        
        Title: {title}
        Abstract: {abstract}
        
        Available Known Venues (Prioritize these if suitable):
        {venues_str}
        
        Criteria:
        1. **Fit**: Topic alignment.
        2. **Impact**: Prioritize CCF-A / Top-Tier.
        3. **Strategy**: Default to **Conference** (NeurIPS/ICLR/CVPR) for speed and novelty. Only suggest *Journals* (Nature/TPAMI) if the work is a comprehensive system or extended benchmark.
        
        Output JSON:
        [
            {{
                "name": "NeurIPS",
                "reason": "..."
            }},
            ...
        ]
        """
        response = await self.client.chat(prompt, tier=ModelTier.STANDARD, task_type="planning")
        
        import json
        recommendations = []
        try: 
            import re
            match = re.search(r"\[.*\]", response, re.DOTALL)
            if match:
                recommendations = json.loads(match.group(0))
        except:
             print("[SubmissionManager] ⚠️ LLM Parse Error.")
             
        # 2. Enrich with KB Data
        enriched = []
        for rec in recommendations:
            kb_entry = next((v for v in self.venues_db if v['name'].lower() == rec['name'].lower()), None)
            if kb_entry:
                # Merge KB data
                rec.update(kb_entry)
            else:
                rec['tier'] = "Unknown"
            enriched.append(rec)
            
        return enriched if enriched else [{"name": "NeurIPS", "tier": "CCF-A", "type": "Conference", "reason": "Default Fallback"}]

    async def get_venue_details(self, venue_name: str) -> Dict[str, Any]:
        """
        Finds details (Deadline, Requirements, Template) from KB or Search.
        """
        # 1. Lookup KB
        kb_entry = next((v for v in self.venues_db if v['name'].lower() == venue_name.lower()), None)
        
        deadline_info = "Unknown"
        requirements = {}
        review_cycle = "Unknown"
        template_dir = None
        main_tex_source = None
        
        if kb_entry:
            print(f"[SubmissionManager] 🎯 Found {venue_name} in Knowledge Base.")
            # Resolve Deadline (Directly from 'deadline' field now)
            deadline_info = kb_entry.get("deadline", "Check Website")
            requirements = kb_entry.get("requirements", {})
            review_cycle = kb_entry.get("review_cycle", "Unknown")
            
            # Resolve Template Path (from KB relative path)
            if "template_path" in kb_entry:
                 kb_path = os.path.join(self.template_root, kb_entry["template_path"])
                 if os.path.exists(kb_path):
                     template_dir = kb_path
                     # Find main.tex
                     for f in os.listdir(kb_path):
                         if f.endswith(".tex") and ("main" in f or "example" in f):
                             main_tex_source = os.path.join(kb_path, f)
                             break
        
        # 2. Fallback: Search (if KB missing or incomplete)
        if not kb_entry or deadline_info == "Check Website":
            query = f"{venue_name} {datetime.now().year} submission deadline"
            search_results = await self.search.search_web(query)
            if search_results:
                deadline_info = search_results[0].get('snippet', deadline_info)

        # 3. Fallback: Template Heuristic (if KB path failed)
        if not template_dir:
            slug = venue_name.lower().replace(" ", "")
            candidates = [slug, slug.replace("conference", ""), slug.split(" ")[0]]
            paper_templates = os.path.join(self.template_root, "paper")
            
            for c in candidates:
                check_path = os.path.join(paper_templates, c)
                if os.path.isdir(check_path):
                    template_dir = check_path
                    for f in os.listdir(check_path):
                         if f.endswith(".tex") and ("main" in f or "example" in f or c in f):
                             main_tex_source = os.path.join(check_path, f)
                             break
                    break
                    
        if not template_dir:
            template_dir = os.path.join(self.template_root, "paper/common")
            main_tex_source = os.path.join(template_dir, "main.tex")
            
        # Prepare Base Result
        result = {
            "venue": venue_name,
            "deadline_context": deadline_info,
            "requirements": requirements,
            "review_cycle": review_cycle,
            "template_dir": template_dir, 
            "main_tex_source": main_tex_source
        }
        
        # Merge all other KB fields (tier, impact_factor, appendix, structure, etc.)
        if kb_entry:
            for k, v in kb_entry.items():
                if k not in result:
                    result[k] = v
                    
        return result

    def prepare_workspace(self, venue_details: Dict, output_dir: str) -> Dict:
        """
        Sets up the workspace WITHOUT copying the full template folder.
        """
        os.makedirs(output_dir, exist_ok=True)
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        print(f"[SubmissionManager] 🏗️ Preparing workspace for {venue_details.get('name', 'Unknown')}")
        
        # 0. Setup Paths
        common_root = os.path.join(self.template_root, "paper/common")
        sections_out = os.path.join(output_dir, "sections")
        os.makedirs(sections_out, exist_ok=True)
        os.makedirs(os.path.join(output_dir, "figs"), exist_ok=True)
        
        # 1. Map Structure to Files
        # Default mapping from KB Keys -> Common Template Files
        MAPPING = {
            "Abstract": "sections/00_abstract.tex",
            "Summary": "sections/00_abstract.tex",
            "Intro": "sections/01_introduction.tex",
            "Introduction": "sections/01_introduction.tex",
            "Related Work": "sections/02_related_work.tex",
            "Method": "sections/03_method.tex",
            "Methods": "sections/03_method.tex",
            "Materials and Methods": "sections/03_method.tex",
            "Exp": "sections/04_experiments.tex",
            "Experiments": "sections/04_experiments.tex",
            "Results": "sections/04_experiments.tex", # Result-focused
            "Discussion": "sections/05_discussion.tex",
            "Conclusion": "sections/06_conclusion.tex",
            "Impact Statement": "sections/template_impact.tex",
            "Limitations": "sections/template_limitations.tex",
            "Index Terms": "sections/00_abstract.tex", # Placeholder
            "Data Availability": "sections/05_discussion.tex", # Merge or separate? generic for now
            "Ethics Statement": "sections/template_impact.tex"
        }
        
        structure = venue_details.get("structure", [
            "Abstract", "Intro", "Related Work", "Method", "Exp", "Conclusion"
        ])
        
        inputs_list = []
        
        # 2. Dynamic Copy & Assemble
        for idx, section_key in enumerate(structure):
            # Clean key
            clean_key = section_key.split("(")[0].strip() # "Abstract (~150 words)" -> "Abstract"
            src_rel = MAPPING.get(clean_key)
            if not src_rel:
                # Fuzzy fallback or default
                 if "Intro" in clean_key: src_rel = MAPPING["Intro"]
                 elif "Method" in clean_key: src_rel = MAPPING["Method"]
                 elif "Result" in clean_key: src_rel = MAPPING["Results"]
                 elif "Diskussion" in clean_key: src_rel = MAPPING["Discussion"]
                 else: src_rel = MAPPING["Intro"] # Safety fallback? Or maybe generic?
            
            if src_rel:
                src_path = os.path.join(common_root, src_rel)
                if os.path.exists(src_path):
                    # Destination name: 00_Abstract.tex, 01_Introduction.tex
                    safe_slug = clean_key.replace(" ", "_").lower()
                    dest_filename = f"{idx:02d}_{safe_slug}.tex"
                    dest_path = os.path.join(sections_out, dest_filename)
                    shutil.copy(src_path, dest_path)
                    inputs_list.append(f"\\input{{sections/{dest_filename}}}")
                else:
                    print(f"[SubmissionManager] ⚠️ Missing source template: {src_rel}")
            else:
                 print(f"[SubmissionManager] ⚠️ Unknown section type: {clean_key}")

        # 3. Copy Refs & Generic items
        shutil.copy(os.path.join(common_root, "refs.bib"), os.path.join(output_dir, "refs.bib"))
        
        # 4. Generate Main.tex
        # If venue has a boilerplate main.tex, use it? 
        # Actually consistent Prompt engineering relies on OUR structure.
        # We will wrap the inputs in a standard shell.
        
        main_tex_content = f"""\\documentclass{{article}}
% Standard Packages
\\usepackage[utf8]{{inputenc}} 
\\usepackage[T1]{{fontenc}}
\\usepackage{{graphicx}}
\\usepackage{{amsmath}}
\\usepackage{{amssymb}}
\\usepackage{{booktabs}}
\\usepackage{{url}}
\\usepackage{{hyperref}}

% Auto-Injected Macros
\\input{{macros}}

\\title{{<<TITLE>>}}
\\author{{Anonymous Author(s)}}
\\date{{}}

\\begin{{document}}

\\maketitle

% -----------------------------------------------------------------------------
% {venue_details.get('name')} STRUCTURE
% -----------------------------------------------------------------------------
"""
        for inp in inputs_list:
            main_tex_content += f"{inp}\n"

        main_tex_content += """
% -----------------------------------------------------------------------------
% BIBLIOGRAPHY
% -----------------------------------------------------------------------------
\\bibliographystyle{plainnat}
\\bibliography{refs}

\\end{document}
"""
        
        # Write macros dummy if needed
        # (Assuming macros.tex exists in common root or is handled by template dir)
        
        with open(os.path.join(output_dir, "main.tex"), "w") as f:
            f.write(main_tex_content)
        
        with open(os.path.join(output_dir, "macros.tex"), "w") as f:
            f.write("% Macros placeholders\n")

        # 5. Create Placeholder Image for Hypothetical Drafts
        placeholder_path = os.path.join(output_dir, "figs", "placeholder.png")
        if not os.path.exists(placeholder_path):
            # Minimal 1x1 Gray PNG
            minimal_png = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
            with open(placeholder_path, "wb") as f:
                f.write(minimal_png)

        print(f"[SubmissionManager] ✅ Generated Dynamic Workspace for {venue_details.get('name')}")

        # 6. Return Env Config for TEXINPUTS
        template_dir = venue_details.get("template_dir")
        if not template_dir:
            template_dir = os.path.join(self.template_root, "paper/common")
            
        return {
            "TEXINPUTS": f".:{template_dir}//:{self.template_root}//:", 
            "template_path": template_dir
        }
