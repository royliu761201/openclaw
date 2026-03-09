from typing import Dict, List, Optional, Any, Union
from .academic_writer import AcademicWriter
from config import ModelTier
from core.model_client import ModelClient

class PaperWriter(AcademicWriter):
    """
    Specialized Writer for Academic Papers (IMRAD Structure).
    Inherits robustness and figure generation from AcademicWriter.
    """
    
    def __init__(self, model_client: ModelClient, git_manager: Any = None, code_generator: Any = None):
        super().__init__(model_client=model_client, git_manager=git_manager, output_base="paper_output")
        self.code_generator = code_generator
        
    async def draft_paper(self, topic: str, context: str) -> str:
        safe_topic = topic.replace(" ", "_")[:50]
        project_dir = os.path.join(self.output_base, f"{safe_topic}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        sections_dir = os.path.join(project_dir, "sections")
        os.makedirs(sections_dir, exist_ok=True)
        
        print(f"[PaperWriter] 📄 Drafting Paper: {topic}")
        
        # 1. Parallel Generation
        tasks = [
            self._write_section("Introduction", topic, context, "Focus on Research Gap & Contributions. Language: English Only."),
            self._write_section("Related Work", topic, context, "Compare with SOTA. Language: English Only."),
            self._write_section("Methodology", topic, context, "Mathematical Formulation. Language: English Only."),
            self._write_section("Experiments", topic, context, "Datasets, Metrics, Baselines. Language: English Only."),
            self._write_section("Conclusion", topic, context, "Summary & Future Work. Language: English Only.")
        ]
        
        # 1b. Figures & Application (Delegated to CodeGenerator if available)
        if self.code_generator:
            print("[PaperWriter] 🎨 Generating Figures & Code via CodeGenerator...")
            
            # Generate Scripts
            arch_code = await self.code_generator.generate_visualization_script(topic, f"{context}\nType: System Architecture Diagram", "architecture.png")
            plot_code = await self.code_generator.generate_visualization_script(topic, f"{context}\nType: Experiment Results (Bar Plot)", "results.png")
            exp_code = await self.code_generator.generate_experiment_script(topic, context)
            demo_code = await self.code_generator.generate_demo_app(topic, context)
            
            # Write & Execute
            self._write_code_file(project_dir, "gen_arch.py", arch_code)
            self._write_code_file(project_dir, "gen_plot.py", plot_code)
            self._write_code_file(project_dir, "experiment.py", exp_code)
            self._write_code_file(project_dir, "app.py", demo_code)
            
            await self._execute_python(project_dir, "gen_arch.py")
            await self._execute_python(project_dir, "gen_plot.py")
        else:
            print("[PaperWriter] ⚠️ CodeGenerator not active. Skipping figures.")

        # Application Content (Case Study)
        app_content = await self._generate_application_scenario(topic, context, project_dir, mode="Paper (Case Study)")

        print("[PaperWriter] 🚀 Launching Text Agents...")
        text_results = await asyncio.gather(*tasks)
        intro, related, method, exp, conc = text_results
        
        # Figures & Application (Batched)
        # Note: fig_tasks now has 5 items. The last one is exp_code, second to last is demo, third to last is app_content.
        # Wait, let's just await them and pick by index if needed, or structured return
        # Since _generate_* methods (except app_scenario) return None (void), we rely on file side-effects.
        # _generate_application_scenario returns content string.
        
        
        
        
        # 2. Adversarial Review (Methodology is critical)
        refined_method = await self._adversarial_review(
            "Methodology", method, 
            criteria="1. Mathematical Rigor. 2. Clarity of Algorithm. 3. Language MUST be English.", 
            reviewer_persona="Senior NeurIPS Reviewer", 
            drafter_persona="Academic Researcher"
        )
        
        # 3. Write
        with open(os.path.join(sections_dir, "01_intro.tex"), "w") as f: f.write(self._clean_latex(intro))
        with open(os.path.join(sections_dir, "02_related.tex"), "w") as f: f.write(self._clean_latex(related))
        with open(os.path.join(sections_dir, "03_method.tex"), "w") as f: f.write(self._clean_latex(refined_method))
        with open(os.path.join(sections_dir, "04_exp.tex"), "w") as f: f.write(self._clean_latex(exp))
        with open(os.path.join(sections_dir, "05_conc.tex"), "w") as f: f.write(self._clean_latex(conc))
        with open(os.path.join(sections_dir, "09_practical_application.tex"), "w") as f: f.write(self._clean_latex(app_content))
        
        self._write_main_tex(project_dir, topic)
        await self._compile_pdf(project_dir, "main.tex")
        
        return await self._zip_package(project_dir, safe_topic)

    async def _write_section(self, section: str, topic: str, context: Union[str, List[any]], instruction: str) -> str:
        prompt_instruction = f"""
        Role: Academic Researcher.
        Task: Write '{section}' section for a paper on '{topic}'.
        Instruction: {instruction}
        Language: STRICTLY ENGLISH. No Chinese characters.
        Format: LaTeX.
        """
        prompt = self._construct_prompt(prompt_instruction, context)
        return await self._safe_chat(prompt, tier=ModelTier.CRITICAL, task_type="paper_drafting")

    async def _generate_architecture_diagram(self, topic: str, context: str, output_dir: str):
        prompt = f"""
        Role: Viz Expert.
        Task: Matplotlib code for System Architecture of {topic}.
        Context: {context}
        Restrictions: Use patches/lines. Save to 'architecture.png'.
        """
        await self._execute_figure_code(prompt, output_dir, "architecture.png")

    async def _generate_experiment_plot(self, topic: str, context: str, output_dir: str):
        prompt = f"""
        Role: Viz Expert.
        Task: Matplotlib code for Experiment Results (Bar/Line).
        Context: {context}
        Restrictions: Save to 'results.png'. Compare 'Ours' vs 'SOTA'.
        """
        await self._execute_figure_code(prompt, output_dir, "results.png")
        
    async def _generate_experiment_code(self, topic: str, context: str, output_dir: str):
        """Generates backend experiment code and instructions."""
        print(f"[PaperWriter] 🧪 Generates Backend Experiment Code...")
        exp_dir = os.path.join(output_dir, "predictions")
        os.makedirs(exp_dir, exist_ok=True)
        
        prompt = f"""
        Role: ML Engineer.
        Task: Write a prediction/experiment script ('experiment.py') for: {topic}.
        Context: {context}
        
        Requirements:
        1. Use PyTorch or TensorFlow (Mock data is fine).
        2. Implement a 'train()' and 'evaluate()' function.
        3. Save dummy metrics to 'results.json'.
        4. Print progress logs.
        
        Output: Python Code ONLY.
        """
        code = await self._safe_chat(prompt, tier=ModelTier.STANDARD, task_type="coding")
        code = code.replace("```python", "").replace("```", "").strip()
        
        with open(os.path.join(exp_dir, "experiment.py"), "w") as f: f.write(code)
        
        # Generate README
        readme = f"""
        # Experiment Code for {topic}
        
        ## Usage
        ```bash
        python3 experiment.py
        ```
        
        ## Outputs
        - results.json: Metrics
        """
        with open(os.path.join(exp_dir, "README.md"), "w") as f: f.write(readme)

    def _write_main_tex(self, project_dir: str, topic: str):
        content = f"""
\\documentclass{{article}}
\\usepackage{{graphicx}}
\\usepackage{{geometry}}
\\usepackage{{booktabs}}
\\geometry{{a4paper}}

\\title{{{topic}}}
\\author{{AI4S ResearchBot}}
\\date{{\\today}}

\\begin{{document}}
\\maketitle
\\begin{{abstract}}
Automatic draft generated by AI4S ResearchBot.
\\end{{abstract}}

\\section{{Introduction}}
\\input{{sections/01_intro}}

\\section{{Related Work}}
\\input{{sections/02_related}}

\\section{{Methodology}}
\\begin{{figure}}[h]
    \\centering
    \\includegraphics[width=0.9\\textwidth]{{architecture.png}}
    \\caption{{System Architecture}}
\\end{{figure}}
\\input{{sections/03_method}}

\\section{{Experiments}}
\\begin{{figure}}[h]
    \\centering
    \\includegraphics[width=0.8\\textwidth]{{results.png}}
    \\caption{{Experimental Results}}
\\end{{figure}}
\\input{{sections/04_exp}}

\\section{{Case Study: Practical Application}}
\\input{{sections/09_practical_application}}

\\section{{Conclusion}}
\\input{{sections/05_conc}}

\\end{{document}}
"""
        with open(os.path.join(project_dir, "main.tex"), "w") as f:
            f.write(content)
