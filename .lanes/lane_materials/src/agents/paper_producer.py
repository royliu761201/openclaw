import asyncio
import os
import sys
import yaml
import importlib.util
import re
import hashlib
from utils.string_utils import slugify
from config import PAPER_WORKSPACE_DIR
from typing import Dict, Any, Optional, List

from skills.paper_planner import PaperPlanner
from skills.academic_writer import AcademicWriter
from skills.latex_architect import LatexArchitect
from skills.visual_reviewer import VisualInspector
from config import ModelTier
from core.model_client import ModelClient
from .base_agent import BaseAgent

class PaperProducer(BaseAgent):
    """
    The 'Principal Investigator' Agent.
    Orchestrates the entire lifecycle of a paper from Idea to PDF.
    """

    def __init__(self, root_dir: str, model_client: ModelClient, git_manager: Any, code_generator: Any = None):
        super().__init__(name="PaperProducer", root_dir=root_dir)
        self.root_dir = root_dir # Store root_dir explicitly
        # Initialize Skills
        self.code_generator = code_generator
        self.planner = PaperPlanner(model_client=model_client)
        self.writer = AcademicWriter(model_client=model_client, git_manager=git_manager)
        self.architect = LatexArchitect()
        self.inspector = VisualInspector(model_client=model_client)

    async def plan_paper(self, topic: str, venue: str, context_str: str, autonomous_review: bool = True, output_dir: Optional[str] = None) -> str:
        """
        Phase 1: Generates and optionally reviews the paper outline.
        """
        print(f"\n--- [PaperProducer] Phase 1: Planning ({topic}) ---")
        
        # Check cache
        outline_filename = f"outline_{venue.lower().replace(' ', '_')}.md"
        target_dir = output_dir if output_dir else self.planner.output_dir
        outline_path = os.path.join(target_dir, outline_filename)
        
        if os.path.exists(outline_path):
            print("⏩ Outline exists. Loading from cache.")
            with open(outline_path, "r") as f: return f.read()
            
        outline = await self.planner.generate_outline(topic, venue, context_str, output_dir=output_dir)
            
        # Auto-Review Loop
        if autonomous_review:
            review = await self.planner.review_outline(outline, venue)
            if review['status'] == "REJECT":
                print("⚠️ Outline Rejected. Refining...")
                outline = await self.planner.refine_outline(outline, review['critique'])
            else:
                print("✅ Outline Approved.")
                
        return outline

    async def write_draft(self, config: Dict, outline: str, output_dir: str, target_sections: Optional[List[str]] = None):
        """
        Phase 3: Writes sections based on the outline.
        Args:
            target_sections: Optional list of section names (e.g. ["Introduction"]) to write. If None, writes all.
        """
        print(f"\n--- [PaperProducer] Phase 3: Drafting (Writing) [Targets: {target_sections if target_sections else 'ALL'}] ---")
        
        all_sections = [
            ("Introduction", "01_introduction.tex"),
            ("Related Work", "02_related_work.tex"),
            ("Method", "03_method.tex"),
            ("Experiments", "04_experiments.tex"),
            ("Discussion", "05_discussion.tex")
        ]
        
        # Filter sections
        sections_to_process = []
        if target_sections:
            for name, file in all_sections:
                if name in target_sections:
                    sections_to_process.append((name, file))
        else:
            sections_to_process = all_sections
        
        for sec_name, filename in sections_to_process:
            path = os.path.join(output_dir, "sections", filename)
            if os.path.exists(path):
                print(f"⚠️ {sec_name} exists. Overwriting (Aggressive Iteration Mode)...")
                # continue -> Removed to enable Overwrite
                
            print(f"✍️ Writing {sec_name}...")
            
            # Load Bibliography Context if available
            bib_path = os.path.join(output_dir, "refs.bib")
            bib_context = ""
            if os.path.exists(bib_path):
                with open(bib_path, "r") as f:
                    bib_content = f.read()
                    # Truncate if too long (heuristic 10k chars) to save tokens, or trust context window
                    bib_context = f"\n\nAvailable Bibliography (BibTeX):\n{bib_content}"

            prompt = f"""
            Write the **{sec_name}** section for a {config['venue']} paper.
            Title: {config['title']}
            
            Outline Context:
            {outline}
            
            {bib_context}
            
            Data Context (Paper Macros):
            (See macros.tex in context)
            
            Requirements:
            1. High academic density.
            2. STRICT LaTeX format (no preamble).
            3. Use \\cite{{key}} for citations. ONLY use keys found in the "Available Bibliography".
            """
            content = await self.writer._safe_chat(prompt, tier=ModelTier.CRITICAL, task_type="writing")
            
            # Clean markdown fences
            lines = content.split("\n")
            cleaned = [l for l in lines if not l.strip().startswith("```")]
            
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                f.write("\n".join(cleaned))

    async def compile_and_inspect(self, output_dir: str) -> Dict[str, Any]:
        """
        Phase 4: Compiles PDF and performs Visual Inspection.
        """
        print("\n--- [PaperProducer] Phase 4: Production (Compilation & QA) ---")
        
        # 4.1 Compile (Auto-Fix enabled by default in Architect)
        result = self.architect.compile_pdf(output_dir)
        
        if result["success"]:
            print(f"✅ PDF Generated: {result['pdf_path']}")
            
            # 4.2 Visual Inspection
            report = self.inspector.inspect_artifact(
                pdf_path=result['pdf_path'],
                log_path=result['pdf_path'].replace(".pdf", ".log"),
                output_dir=output_dir
            )
            
            # 4.3 Quality Gate
            if report['defects_count'] > 0:
                print(f"⚠️ Visual Defects Found: {report['defects_count']}")
                print("🔄 [PaperProducer] Architect likely attempted fixes. Check visual_report.md.")
            else:
                print("🌟 QA PASSED: No visual defects.")
            
            return {"success": True, "pdf_path": result['pdf_path'], "report": report}
                
        else:
            print("❌ Compilation Failed.")
            return {"success": False, "error": result.get('log', '')}

    async def produce_paper(self, config_path: str):
        """
        Executes the autonomous pipeline based on the provided config file.
        Uses the granular methods: plan, draft, compile.
        """
        # 0. Load Config
        if not os.path.exists(config_path):
            print(f"❌ Config file not found: {config_path}")
            return

        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
            
        print(f"🚀 [PaperProducer] Starting Pipeline for: {config['title']}")
        print(f"📍 Project ID: {config['project_id']}")
        
        # --- Phase 1: Planning ---
        context_str = ""
        proposal_path = config['context']['proposal'] if os.path.isabs(config['context']['proposal']) else os.path.join(self.root_dir, config['context']['proposal'])
        code_path = config['context']['code'] if os.path.isabs(config['context']['code']) else os.path.join(self.root_dir, config['context']['code'])
        
        if os.path.exists(proposal_path):
            with open(proposal_path, 'r') as f: context_str += f.read()
            
        if os.path.exists(code_path):
            with open(code_path, 'r') as f: context_str += f"\n\nCODE:\n{f.read()}"

        outline = await self.plan_paper(config['title'], config['venue'], context_str, config.get('autonomous_review', True), output_dir=config['output_dir'])

        # --- Phase 2: Experimentation ---
        print("\n--- Phase 2: Experimentation (Science/Data Bridge) ---")
        self._run_experiment(config) # Extracted helper

        # Inject Data (Data Bridge)
        output_dir = config['output_dir']
        if not os.path.isabs(output_dir):
            output_dir = os.path.join(self.root_dir, output_dir)
            
        self.writer.inject_results(output_dir)
        
        # Inject Bibliography (Context Inheritance)
        await self._inherit_bibliography(config)

        # --- Phase 3: Drafting ---
        await self.write_draft(config, outline, output_dir)

    async def _inherit_bibliography(self, config: Dict):
        """
        Copies existing .bib files (ref.bib or refs.bib) from the source project
        to the build directory to ensure 'Context Inheritance'.
        """
        output_dir = config['output_dir']
        if not os.path.isabs(output_dir):
            output_dir = os.path.join(self.root_dir, output_dir)
            
        # Determine Source Dir (Heuristic: Parent of proposal, or from 'code' context)
        # We try to find where the user likely keeps 'refs.bib'
        search_dirs = []
        
        # 1. From Proposal Path
        if 'proposal' in config['context']:
             prop_path = config['context']['proposal'] 
             if not os.path.isabs(prop_path): prop_path = os.path.join(self.root_dir, prop_path)
             search_dirs.append(os.path.dirname(prop_path))
             # Also check 'paper' subdir relative to proposal
             search_dirs.append(os.path.join(os.path.dirname(prop_path), "paper"))

        # 2. From Root
        search_dirs.append(self.root_dir)

        target_bib = os.path.join(output_dir, "refs.bib")
        
        found = False
        for src_dir in search_dirs:
            if not os.path.exists(src_dir): continue
            
            for candidate in ["refs.bib", "bibliography.bib", "ref.bib"]:
                src_bib = os.path.join(src_dir, candidate)
                if os.path.exists(src_bib):
                    print(f"📚 [Context] Inheriting bibliography from: {src_bib}")
                    with open(src_bib, "r") as f: legacy_content = f.read()
                    
                    # Append or Create
                    mode = "a" if os.path.exists(target_bib) else "w"
                    with open(target_bib, mode) as f:
                        f.write(f"\n\n% --- Inherited from {candidate} ---\n")
                        f.write(legacy_content)
                    found = True
                    break # Stop after finding one major bib file
            if found: break
            
        if not found:
            print("⚠️ No existing bibliography found to inherit.")

        # --- Phase 4: Production ---
        await self.compile_and_inspect(output_dir)

    def _run_experiment(self, config: Dict):
        """Executes the experiment script provided in config."""
        exp_script = config['experiment_script']
        if not os.path.isabs(exp_script):
            exp_script = os.path.join(self.root_dir, exp_script)
            
        if os.path.exists(exp_script):
            # Dynamically import experiment script
            spec = importlib.util.spec_from_file_location("exp_module", exp_script)
            exp_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(exp_module)
            
            project_dir = os.path.dirname(config['output_dir']) # Parent of 'paper'
            if not os.path.isabs(project_dir):
                project_dir = os.path.join(self.root_dir, project_dir)
                
            print(f"🧪 Executing experiment script: {exp_script}")
            if hasattr(exp_module, 'run_experiment'):
                exp_success = exp_module.run_experiment(project_dir)
                if not exp_success:
                    print("❌ Experiment Failed. Aborting.")
            else:
                print(f"⚠️ Script {exp_script} has no 'run_experiment' function. Skipping execution.")
        else:
            print(f"⚠️ Experiment script not found: {exp_script}")


    async def produce_theory_draft(self, idea_data: Any, venue: str = "NeurIPS 2024", template: str = "neurips_2024.tex", source_path: str = None, references: List[Any] = None) -> Dict[str, Any]:
        """
        High-Level Phase A: From Idea to Theory Draft (Intro, Related Work, Method).
        Handles title cleaning, ID generation, scaffolding, and bib inheritance.
        """
        print(f"\n--- [PaperProducer] 🏗️ Producing Theory Draft ---")
        
        # 1. Parse & Clean Logic
        if isinstance(idea_data, dict):
            final_title = idea_data.get("title", "Untitled Research")
            final_abstract = idea_data.get("abstract", "No abstract provided.")
            idea_details = idea_data.get("details", str(idea_data))
            
            if final_title == "Parse Error" or len(final_title) < 5:
                 title_match = re.search(r"Title:\s*(.+)", idea_details, re.IGNORECASE)
                 if title_match: final_title = title_match.group(1).strip().strip('"').strip("'")
        else:
            # Legacy String Path
            idea_details = idea_data
            title_match = re.search(r"Title:\s*(.+)", idea_data, re.IGNORECASE)
            if title_match:
                final_title = title_match.group(1).strip().strip('"').strip("'")
            else:
                lines = idea_data.strip().split('\n')
                candidate = "Untitled Research"
                for line in lines:
                    clean = line.strip().replace("#", "").strip()
                    if not clean: continue
                    if clean.lower().startswith(("okay", "sure", "here is", "certainly")): continue
                    candidate = clean
                    break
                final_title = candidate
            final_abstract = idea_details

        # Clean Prefixes
        clean_title = final_title
        prefixes = ["re:", "fw:", "response to:", "revised proposal:", "proposal:", "subject:"]
        changed = True
        while changed:
            changed = False
            for p in prefixes:
                if clean_title.lower().startswith(p):
                    clean_title = clean_title[len(p):].strip()
                    changed = True
        final_title = clean_title.strip().strip('"').strip("'")
        
        # Clean Abstract
        clean_abstract = final_abstract
        for p in ["abstract:", "summary:", "here is the abstract:", "proposed abstract:"]:
            if clean_abstract.lower().startswith(p): clean_abstract = clean_abstract[len(p):].strip()
        final_abstract = clean_abstract.strip()

        # 2. ID Generation
        idea_slug = slugify(final_title)
        if len(idea_slug) > 50: idea_slug = idea_slug[:50].rstrip("_")
        if len(idea_slug) < 5: idea_slug = f"{idea_slug}_{hashlib.md5(final_title.encode()).hexdigest()[:4]}"
        
        output_dir = os.path.join(self.root_dir, f"{PAPER_WORKSPACE_DIR}/{idea_slug}")
        print(f"📍 Target Workspace: {output_dir}")
        
        # 3. Plan
        context_str = f"Title: {final_title}\nAbstract: {final_abstract}\n\nIdea Details:\n{idea_details}"
        outline = await self.plan_paper(final_title, venue, context_str, autonomous_review=False, output_dir=output_dir)
        
        # 4. Scaffold
        self.architect.scaffold_paper(idea_slug, final_title, output_dir, template_name=template)
        os.makedirs(os.path.join(output_dir, "sections"), exist_ok=True)
        with open(os.path.join(output_dir, "sections/00_abstract.tex"), "w") as f:
             f.write(final_abstract)

        # 5. Write Theory
        config = {"title": final_title, "venue": venue}
        targets = ["Introduction", "Related Work", "Method"]
        await self.write_draft(config, outline, output_dir, target_sections=targets)
        
        # 6. Bibliography Management
        from skills.bibtex_manager import BibTexManager
        bib_manager = BibTexManager()
        
        # Inherit
        if source_path:
            self._smart_inherit_bib(source_path, output_dir)
            
        # Merge New
        if references:
            bib_manager.merge_and_save(references, output_dir)
        else:
             if not os.path.exists(os.path.join(output_dir, "refs.bib")):
                 open(os.path.join(output_dir, "refs.bib"), 'a').close()
                 
        # 7. Schema Enforcement (State Return)
        from schemas.paper import ScientificPaper, PaperSection
        from schemas.common import Citation
        
        # Reconstruct sections from file system for schema validity
        sections = []
        for sec_name, filename in [("Introduction", "01_introduction.tex"), ("Related Work", "02_related_work.tex"), ("Method", "03_method.tex"), ("Abstract", "00_abstract.tex")]:
             path = os.path.join(output_dir, "sections", filename)
             if os.path.exists(path):
                 with open(path, "r") as f: content = f.read()
                 sections.append(PaperSection(title=sec_name, content_tex=content))
        
        # Parse Citations (Naive)
        citations = []
        if references:
            # If passed raw objects, convert to Citation schema if needed? 
            # Assuming references is list of strings or dicts, we simplify for now.
            pass

        return ScientificPaper(
            title=final_title,
            abstract=final_abstract,
            sections=sections,
            citations=citations, # Populated if we parsed bib
            target_venue=venue
        )

    async def produce_final_manuscript(self, idea_data: Any, venue: str, result_dir: str = None) -> Dict[str, Any]:
        """
        Phase 2 Writing: Experiments, Discussion, and Compilation.
        """
        print("\n--- [PaperProducer] 🏁 Producing Final Manuscript ---")
        
        # Re-derive ID
        idea_title = idea_data.get("title", "Untitled") if isinstance(idea_data, dict) else "Untitled"
        idea_slug = slugify(idea_title)
        if len(idea_slug) > 50: idea_slug = idea_slug[:50].rstrip("_")
        if len(idea_slug) < 5: idea_slug = f"{idea_slug}_{hashlib.md5(idea_title.encode()).hexdigest()[:4]}"
        
        output_dir = os.path.join(self.root_dir, f"{PAPER_WORKSPACE_DIR}/{idea_slug}")
        
        # Verify Context
        if not os.path.exists(os.path.join(output_dir, "sections/01_introduction.tex")):
             print("⚠️ Warning: Theory draft missing. This assumes standard flow.")
             
        # Inject Results
        self.writer.inject_results(output_dir) # Uses macros.tex
        
        # Load Result Text
        result_context_str = ""
        if result_dir:
            case_path = os.path.join(result_dir, "case_study.txt")
            if os.path.exists(case_path): 
                with open(case_path, "r") as f: result_context_str += f"\n[Case Study Data]:\n{f.read()}\n"
            lim_path = os.path.join(result_dir, "limitations_and_future_work.txt")
            if os.path.exists(lim_path):
                with open(lim_path, "r") as f: result_context_str += f"\n[Limitations Data]:\n{f.read()}\n"
        
        # Re-Plan (Augmented)
        config = {"title": idea_title, "venue": venue}
        # Ideally we load cached outline
        outline = await self.plan_paper(idea_title, venue, "", autonomous_review=False, output_dir=output_dir)
        augmented_outline = f"{outline}\n\n=== NEW EXPERIMENTAL RESULTS ===\n{result_context_str}"
        
        # Write
        await self.write_draft(config, augmented_outline, output_dir, target_sections=["Experiments", "Discussion"])
        
        # Compile
        result = await self.compile_and_inspect(output_dir)
        result["result_context_str"] = result_context_str # Pass back for Patent
        return result

    def _smart_inherit_bib(self, source_path: str, output_dir: str):
        search_dirs = [source_path, os.path.join(source_path, "paper")]
        target_bib = os.path.join(output_dir, "refs.bib")
        
        for src_dir in search_dirs:
            legacy_bib = os.path.join(src_dir, "refs.bib")
            if os.path.exists(legacy_bib):
                print(f"📚 [Context] Inheriting bibliography from: {legacy_bib}")
                with open(legacy_bib, "r") as f: legacy_content = f.read()
                
                mode = "a" if os.path.exists(target_bib) else "w"
                with open(target_bib, mode) as f:
                    if mode == "a": f.write("\n")
                    f.write(f"% --- Inherited from {legacy_bib} ---\n")
                    f.write(legacy_content)
                return

