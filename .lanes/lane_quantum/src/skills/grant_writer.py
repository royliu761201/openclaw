
import os
import asyncio
import re
import shutil
from typing import Dict, List, Union
from .academic_writer import AcademicWriter
from config import ModelTier

class GuidelineIngester:
    @staticmethod
    def parse(text: str) -> Dict[str, str]:
        constraints = {"budget_limit": "Unknown", "time_limit": "Unknown"}
        budget_match = re.search(r"(\d+)\s*[万k]元?", text)
        if budget_match: constraints["budget_limit"] = f"{budget_match.group(1)}0000" if "万" in text else budget_match.group(1)
        time_match = re.search(r"(\d+)\s*(年|个月|months|years)", text)
        if time_match: constraints["time_limit"] = f"{time_match.group(1)} {time_match.group(2)}"
        return constraints

class GrantWriter(AcademicWriter):
    def __init__(self, model_client, git_manager, root_dir=None):
        super().__init__(model_client, git_manager, output_base="grant_output")
        self.root_dir = root_dir or os.getcwd()
        
    async def draft_proposal(self, topic: str, context: str, guideline_text: str, team_info: str = "Standard AI Team") -> str:
        constraints = GuidelineIngester.parse(guideline_text)
        safe_topic = re.sub(r'[^a-zA-Z0-9]', '_', topic)[:50]
        project_dir = os.path.join(self.output_base, safe_topic)
        sections_dir = os.path.join(project_dir, "sections")
        os.makedirs(sections_dir, exist_ok=True)
        
        # 1. Load Grant Standards (The "Brain")
        standards_path = os.path.join(self.root_dir, "research_vault/knowledge_base/standards/grant_standards.md")
        if os.path.exists(standards_path):
            with open(standards_path, "r") as f:
                grant_standards = f.read()
            print(f"[GrantWriter] 🧠 Loaded Standards from {standards_path}")
        else:
            grant_standards = "Focus on Originality and Feasibility."
            print(f"[GrantWriter] ⚠️ Standards file not found at {standards_path}")
            
        print(f"[GrantWriter] 💰 Drafting Grant: {topic}")
        print(f"[GrantWriter] 📜 Guideline Focus: {guideline_text[:100]}...")
        
        full_context = f"Idea Context: {context}\n\nFull Guidelines: {guideline_text}\n\nTeam Info: {team_info}\n\nGRANT STANDARDS (CRITICAL):\n{grant_standards}"
        
        # 0. GIT ISOLATION: Switch to Grant Branch
        self.git_manager.checkout_grant_branch(safe_topic)
        
        # 1. Parallel Tasks
        tasks = [
            self._write_section("Background", topic, full_context, constraints, "Strategic Necessity (800w) & Scientific Gap (800w)"),
            self._write_section("Content", topic, full_context, constraints, "Research Targets (Scientific Language, 400w) & Key Question"),
            self._write_section("Indicators", topic, full_context, constraints, "Key Technical Indicators (KPIs). Specific, Measurable, Time-bound. (e.g. Accuracy > 95%, Latency < 10ms)."),
            self._write_section("Innovation", topic, full_context, constraints, "Key Innovations (3 points). Contrast with SOTA. (400w)"),
            self._write_section("Methodology", topic, full_context, constraints, "Feasibility (Risk Mitigation, 800w) & Timeline"),
            self._write_section("Foundation", topic, full_context, constraints, "Team Capability & Preliminary Results"),
            self._generate_budget(constraints)
        ]
        
        # 1b. Figures & Application
        fig_tasks = [
            self._generate_flowchart(topic, context, project_dir),
            self._generate_prelim_plot(topic, context, project_dir),
            self._generate_application_scenario(topic, context, project_dir, mode="Grant (Social/Economic Impact)"),
            self._generate_demo_code(topic, context, project_dir)
        ]

        print("[GrantWriter] 🚀 Launching Agents...")
        text_results = await asyncio.gather(*tasks)
        bg, content, indicators, innovation, method, found, budget = text_results
        
        # Application content is the second to last result (Demo is last)
        app_content = (await asyncio.gather(*fig_tasks))[-2]
        
        # 2. Adversarial Review (Refined)
        print("[GrantWriter] 🏛️ Convening Grant Review Panel...")
        refine_tasks = [
            self._adversarial_review("Research Content", content, f"Constraints: {constraints}. Innovation & Scientific Value.", "Senior Grant Reviewer", "Grant Writer"),
            self._adversarial_review("Methodology", method, f"Constraints: {constraints}. Feasibility & Risk.", "Senior Grant Reviewer", "Grant Writer")
        ]
        refined_content, refined_method = await asyncio.gather(*refine_tasks)
        
        # 3. Write
        with open(os.path.join(sections_dir, "01_background.tex"), "w") as f: f.write(self._clean_latex(bg))
        with open(os.path.join(sections_dir, "02_content.tex"), "w") as f: f.write(self._clean_latex(refined_content))
        with open(os.path.join(sections_dir, "02_indicators.tex"), "w") as f: f.write(self._clean_latex(indicators))
        with open(os.path.join(sections_dir, "02_innovation.tex"), "w") as f: f.write(self._clean_latex(innovation))
        with open(os.path.join(sections_dir, "03_methodology.tex"), "w") as f: f.write(self._clean_latex(refined_method))
        # Note: Foundation might effectively duplicate application, but they are distinct in NSFC
        with open(os.path.join(sections_dir, "04_foundation.tex"), "w") as f: f.write(self._clean_latex(found))
        with open(os.path.join(sections_dir, "budget.tex"), "w") as f: f.write(self._clean_latex(budget))
        with open(os.path.join(sections_dir, "09_practical_application.tex"), "w") as f: f.write(self._clean_latex(app_content))
        
        self._write_main_tex(project_dir, topic)
        await self._compile_pdf(project_dir, "main.tex")
        
        # 4. Auto-Commit Draft
        self.git_manager.atom_commit("GRANT_WRITER", "DRAFT", f"Drafted grant for {topic}")
        
        return await self._zip_package(project_dir, safe_topic)

    def finalize_grant(self, topic: str):
        """
        Interactive Method: Call this when Grant is ready to submit.
        Merges grant branch to main and tags it.
        """
        safe_topic = re.sub(r'[^a-zA-Z0-9]', '_', topic)[:50]
        branch = f"grant/{safe_topic}"
        tag = f"v1.0-grant-{safe_topic}"
        
        print(f"[GrantWriter] 🏁 Finalizing Grant: {topic}")
        self.git_manager.merge_and_tag(branch, tag, f"Finalized Grant Proposal: {topic}")

    async def _write_section(self, section: str, topic: str, context: Union[str, List[any]], constraints: Dict, instruction: str) -> str:
        prompt_instruction = f"""
        Role: Academic Grant Writer (NSFC Expert).
        Task: Write Part '{section}' of a grant proposal.
        Topic: {topic}
        Guideline: {constraints}
        Instruction: {instruction}
        Format: LaTeX.
        """
        prompt = self._construct_prompt(prompt_instruction, context)
        return await self._safe_chat(prompt, tier=ModelTier.CRITICAL, task_type="paper_drafting")

    async def _generate_budget(self, constraints: Dict) -> str:
        prompt = f"""
        Role: Project Manager.
        Task: Create a LaTeX Budget Table. Limit: {constraints.get('budget_limit')}.
        Items: Equipment, Material, Travel, Labor, Other.
        Output: ONLY LaTeX tabular code.
        """
        return await self._safe_chat(prompt, tier=ModelTier.ECONOMY, task_type="formatting")

    async def _generate_flowchart(self, topic: str, context: str, output_dir: str):
        prompt = f"""
        Role: Viz Expert.
        Task: Matplotlib code for 'Technical Roadmap' Flowchart (DAG).
        Topic: {topic}
        Context: {context}
        Restrictions: Draw patches. Save to 'technical_roadmap.png'.
        """
        await self._execute_figure_code(prompt, output_dir, "technical_roadmap.png")

    async def _generate_prelim_plot(self, topic: str, context: str, output_dir: str):
        prompt = f"""
        Role: Viz Expert.
        Task: Matplotlib code for 'Preliminary Results' (Bar/Line).
        Topic: {topic}
        Restrictions: Show 'Ours' > 'Baseline'. Save to 'prelim_results.png'.
        """
        await self._execute_figure_code(prompt, output_dir, "prelim_results.png")

    def _write_main_tex(self, project_dir: str, topic: str):
         content = f"""
\\documentclass{{article}}
\\usepackage{{ctex}}
\\usepackage{{graphicx}}
\\usepackage{{geometry}}
\\usepackage{{booktabs}}
\\geometry{{a4paper, scale=0.8}}

\\title{{{topic} - Grant Proposal}}
\\author{{AI4S ResearchBot}}
\\date{{\\today}}

\\begin{{document}}
\\maketitle
\\tableofcontents
\\newpage

\\section{{Part 1: Research Background & Significance}}
\\input{{sections/01_background}}

\\section{{Part 2: Research Content & Targets}}
\\input{{sections/02_content}}

\\subsection{{Technical Indicators}}
\\input{{sections/02_indicators}}

\\section{{Key Innovations}}
\\input{{sections/02_innovation}}

\\section{{Part 3: Methodology & Roadmap}}
\\begin{{figure}}[h]
    \\centering
    \\includegraphics[width=0.9\\textwidth]{{technical_roadmap.png}}
    \\caption{{Technical Roadmap}}
\\end{{figure}}
\\input{{sections/03_methodology}}

\\section{{Part 4: Research Foundation}}
\\begin{{figure}}[h]
    \\centering
    \\includegraphics[width=0.8\\textwidth]{{prelim_results.png}}
    \\caption{{Preliminary Verification Results}}
\\end{{figure}}
\\input{{sections/04_foundation}}

\\section{{Application & Social Impact}}
\\input{{sections/09_practical_application}}

\\section{{Part 5: Budget Plan}}
\\input{{sections/budget}}

\\end{{document}}
"""
         with open(os.path.join(project_dir, "main.tex"), "w") as f:
            f.write(content)
