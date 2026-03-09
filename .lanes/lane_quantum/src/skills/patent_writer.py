
import os
import asyncio
import re
import shutil
from typing import Dict, List, Union
from .academic_writer import AcademicWriter
from config import ModelTier

class PatentWriter(AcademicWriter):
    """
    Specialized Writer for Chinese Patent Disclosures.
    Inherits robustness and core skills from AcademicWriter.
    """
    
    def __init__(self, model_client, git_manager, root_dir=None):
        super().__init__(model_client, git_manager, output_base="patent_output")
        self.root_dir = root_dir or os.getcwd()
        self.PATENT_STYLE = """
        **Language & Style Rules (CRITICAL)**:
        1. **Tone**: Formal, Objective, Legal-Technical (法律技术文书).
        2. **Forbidden Words**: "Best", "Perfect", "First ever", "Leading", "Ideally".
        3. **Required Terms**:
           - Use "The present invention" (本发明) instead of "We" or "Our method".
           - Use "Embodiment" (实施例) instead of "Example".
           - Use "Said/The" (所述) when referencing previously introduced elements.
        4. **Definitiveness**: Avoid "About", "Maybe", "Possibly". Use definite ranges or specific values.
        5. **NO MARKDOWN**: Do NOT use `**bold**`, `## Headers`, or `*bullets*`. Use LaTeX commands only (`\\section`, `\\item`).
        6. **Punctuation**: Use Chinese punctuation (。，、) strictly. Do NOT use English quotes (`""`).
        """
        
    async def draft_disclosure(self, topic: str, context: str, input_mode: str = "IDEA") -> str:
        safe_topic = re.sub(r'[^a-zA-Z0-9]', '_', topic)[:50]
        project_dir = os.path.join(self.output_base, safe_topic)
        sections_dir = os.path.join(project_dir, "sections")
        os.makedirs(sections_dir, exist_ok=True)
        
    async def draft_disclosure(self, topic: str, context: str, input_mode: str = "IDEA") -> str:
        safe_topic = re.sub(r'[^a-zA-Z0-9]', '_', topic)[:50]
        project_dir = os.path.join(self.output_base, safe_topic)
        sections_dir = os.path.join(project_dir, "sections")
        os.makedirs(sections_dir, exist_ok=True)
        
        # 1. Load Patent Standards (Centralized KB)
        standards_path = os.path.join(self.root_dir, "research_vault/knowledge_base/standards/patent_standards.md")
        if os.path.exists(standards_path):
            with open(standards_path, "r") as f:
                patent_standards = f.read()
            print(f"[PatentWriter] 🧠 Loaded Standards from {standards_path}")
        else:
            patent_standards = "Focus on Problem-Solution-Effect."
        
        # Inject Standards into Style
        self.PATENT_STYLE += f"\n\n*** OFFICIAL WRITING STANDARDS ***\n{patent_standards}"
        
        print(f"[PatentWriter] 📜 Drafting Disclosure: {topic} (Mode: {input_mode})")
        
        # 1. Parallel Generation
        tasks = [
            self._write_section("Background", topic, context, "Describe Prior Art & Technical Problem.", input_mode),
            self._write_section("Technical Solution", topic, context, "Describe the Core technical means.", input_mode),
            self._write_section("Beneficial Effects", topic, context, "List technical advantages.", input_mode),
            self._write_section("Embodiments", topic, context, "Describe at least 2 distinct implementation scenarios.", input_mode),
            self._write_section("Claims", topic, context, "Draft 1 independent claim and 5-9 dependent claims.", input_mode)
        ]
        
        # 1b. Figures & Application
        fig_tasks = [
            self._generate_system_figure(topic, context, project_dir),
            self._generate_application_scenario(topic, context, project_dir, mode="Patent (Embodiment)"),
            self._generate_demo_code(topic, context, project_dir)
        ]
        
        print("[PatentWriter] 🚀 Launching Agents...")
        text_results = await asyncio.gather(*tasks)
        bg, sol, eff, emb, claims = text_results
        
        await asyncio.gather(*fig_tasks)
        
        # 2. Adversarial Review (Examiner Persona)
        print("[PatentWriter] 🕵️‍♂️ Starting Adversarial Review Loop...")
        refine_tasks = [
            self._adversarial_review("Technical Solution", sol, "Clarity, Completeness, No Marketing Language.", "Patent Examiner", "Patent Attorney"),
            self._adversarial_review("Embodiments", emb, "Enablement (Could a phD reproduce it?).", "Patent Examiner", "Patent Attorney"),
            self._adversarial_review("Claims", claims, "Legal Validity, Antecodent Basis.", "Patent Examiner", "Patent Attorney")
        ]
        
        refined_sol, refined_emb, refined_claims = await asyncio.gather(*refine_tasks)
        
        # 3. Write Files
        with open(os.path.join(sections_dir, "01_background.tex"), "w") as f: f.write(self._clean_latex(bg))
        with open(os.path.join(sections_dir, "02_solution.tex"), "w") as f: f.write(self._clean_latex(refined_sol))
        with open(os.path.join(sections_dir, "03_effects.tex"), "w") as f: f.write(self._clean_latex(eff))
        with open(os.path.join(sections_dir, "04_embodiments.tex"), "w") as f: f.write(self._clean_latex(refined_emb))
        with open(os.path.join(sections_dir, "05_claims.tex"), "w") as f: f.write(self._clean_latex(refined_claims))
        with open(os.path.join(sections_dir, "09_practical_application.tex"), "w") as f: f.write(self._clean_latex("See Embodiments Section for Integration.")) # Patents handle this in embodiments usually
        
        self._write_main_tex(project_dir, topic)
        await self._compile_pdf(project_dir, "main.tex")
        
        return await self._zip_package(project_dir, safe_topic)

    async def _write_section(self, section: str, topic: str, context: Union[str, List[any]], instruction: str, input_mode: str = "IDEA") -> str:
        
        role_desc = "Patent Attorney (CNIPA)."
        task_desc = f"Draft Patent Section '{section}'."
        
        if input_mode == "PAPER":
            instruction_prefix = f"""
            TRANSFORMATION MODE:
            You are provided with a SCIENTIFIC PAPER (LaTeX/Text).
            Your task is to REWRITE and TRANSFORM this content into a Patent Disclosure.
            
            Mapping Rules:
            - Paper 'Method' -> Patent 'Technical Solution' (Steps).
            - Paper 'Experiments' -> Patent 'Embodiments' (Proof of efficacy).
            - Paper 'Baselines' -> Patent 'Background/Prior Art'.
            
            Key Objective for {section}:
            Extract relevant details from the paper context and strictly format as {section}.
            """
        else:
            instruction_prefix = "CREATIVE MODE: Draft from the core idea."

        prompt_instruction = f"""
        Role: {role_desc}
        Task: {task_desc}
        Topic: {topic}
        Mode: {input_mode}
        
        {instruction_prefix}
        
        Specific Instruction: {instruction}
        Style Rules: {self.PATENT_STYLE}
        Format: LaTeX.
        """
        prompt = self._construct_prompt(prompt_instruction, context)
        return await self._safe_chat(prompt, tier=ModelTier.CRITICAL, task_type="paper_drafting")

    async def _generate_system_figure(self, topic: str, context: str, output_dir: str):
        prompt = f"""
        Role: Viz Expert.
        Task: Matplotlib code for System Architecture.
        Topic: {topic}
        Restrictions: Save to 'schematic.png'. Use patches.
        """
        await self._execute_figure_code(prompt, output_dir, "schematic.png")

    def _write_main_tex(self, project_dir: str, topic: str):
         content = f"""
\\documentclass{{article}}
\\usepackage{{ctex}}
\\usepackage{{graphicx}}
\\usepackage{{geometry}}
\\geometry{{a4paper}}

\\title{{{topic} - Patent Disclosure}}
\\author{{AI4S ResearchBot}}
\\date{{\\today}}

\\begin{{document}}
\\maketitle

\\section{{Background & Technical Problem}}
\\input{{sections/01_background}}

\\section{{Technical Solution}}
\\begin{{figure}}[h]
    \\centering
    \\includegraphics[width=0.9\\textwidth]{{schematic.png}}
    \\caption{{System Schematic}}
\\end{{figure}}
\\input{{sections/02_solution}}

\\section{{Beneficial Effects}}
\\input{{sections/03_effects}}

\\section{{Embodiments}}
\\input{{sections/04_embodiments}}

\\section{{Practical Application Scenario}}
\\input{{sections/09_practical_application}}

\\section{{Claims}}
\\input{{sections/05_claims}}

\\end{{document}}
"""
         with open(os.path.join(project_dir, "main.tex"), "w") as f:
            f.write(content)
