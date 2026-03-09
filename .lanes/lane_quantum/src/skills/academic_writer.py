
import asyncio
import os
import shutil
from typing import Dict, List, Optional, Tuple, Union
from core.model_client import ModelClient
from config import ModelTier
from .git_executor import GitExecutor
from .writer_ops import latex_ops, prompt_ops
from .base_skill import BaseSkill

class AcademicWriter(BaseSkill):
    """
    Abstract Base Class for Academic Output Generation (Papers, Patents, Grants).
    Refactored to delegate atomic operations to `writer_ops`.
    Inherits from BaseSkill for standard config/validation.
    """

    def __init__(self, model_client: ModelClient, git_manager: GitExecutor, output_base: str = "academic_output", config: Optional[Dict] = None):
        super().__init__(config)
        self.output_base = os.path.join(os.getcwd(), output_base)
        os.makedirs(self.output_base, exist_ok=True)
        self.client = model_client
        # Rate Limiting: Max 3 concurrent LLM calls
        self.semaphore = asyncio.Semaphore(3)
        
        # Git Persistence (Background Management)
        # Git Persistence (Background Management)
        self.git_manager = git_manager

    def verify(self) -> bool:
        """
        Verifies that the writer is ready to run.
        Checks for:
        1. Output directory write access.
        2. LaTeX compiler availability (xelatex).
        """
        # 1. Check Output Dir
        if not os.access(self.output_base, os.W_OK):
            print(f"[{self.name}] ❌ Output directory not writable: {self.output_base}")
            return False

        # 2. Check LaTeX
        import shutil
        if not shutil.which("xelatex"):
             print(f"[{self.name}] ⚠️ xelatex not found. PDF compilation will fail.")
             # We might still return True if we allow text-only generation, but let's be strict for now or Warn.
             # Given the core value is PDF, let's warn but return True (soft fail) or False (hard fail)?
             # The error "Can't instantiate abstract class" means we MUST implement it.
             pass
        
        return True

    async def _safe_chat(self, prompt: Union[str, List[any]], tier: ModelTier, task_type: str = "general") -> str:
        """Rate-limited wrapper for LLM calls."""
        async with self.semaphore:
            try:
                return await self.client.chat(prompt, tier=tier, task_type=task_type)
            except Exception as e:
                print(f"[AcademicWriter] LLM Error: {e}")
                return "GENERATION_FAILED"

    def inject_results(self, project_dir: str):
        """Delegates to latex_ops."""
        print(f"[AcademicWriter] 🌉 Injecting experimental results...")
        latex_ops.inject_results_macros(project_dir)

    def _construct_prompt(self, instruction: str, context: Union[str, List[any]]) -> Union[str, List[any]]:
        """Delegates to prompt_ops."""
        return prompt_ops.construct_multimodal_prompt(instruction, context)

    async def _adversarial_review(self, section: str, content: str, criteria: str, 
                                  reviewer_persona: str, drafter_persona: str) -> str:
        """
        Generic Adversarial Loop: Drafter -> Reviewer -> Drafter.
        Uses prompt_ops for construction.
        """
        print(f"[AcademicWriter] 🏛️ {reviewer_persona} reviewing {section}...")
        
        critique_prompt = prompt_ops.build_critique_prompt(reviewer_persona, section, criteria, content)
        critique = await self._safe_chat(critique_prompt, tier=ModelTier.STANDARD, task_type="reasoning")
        
        if "PASS" in critique or len(critique) < 20:
            print(f"[AcademicWriter] ✅ {section} Passed Review.")
            return content
        
        print(f"[AcademicWriter] ⚠️ {section} Rejected. Refining...")
        refine_prompt = prompt_ops.build_refine_prompt(drafter_persona, critique, content)
        return await self._safe_chat(refine_prompt, tier=ModelTier.STANDARD, task_type="paper_drafting")

    async def _execute_python(self, directory: str, filename: str):
        """Simple execution wrapper."""
        cmd = f"cd {directory} && python3 {filename}"
        script_path = os.path.join(directory, filename)
        if not os.path.exists(script_path): return
        
        print(f"[AcademicWriter] 🏃 Running {filename}...")
        proc = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            print(f"[AcademicWriter] ❌ Error running {filename}: {stderr.decode()}")
        else:
            print(f"[AcademicWriter] ✅ {filename} executed successfully.")

    async def _execute_figure_code(self, prompt: str, output_dir: str, filename: str):
        """Generates and executes code for figures."""
        # 1. Generate Code
        code = await self._safe_chat(prompt, tier=ModelTier.STANDARD, task_type="coding")
        clean_code = code.replace("```python", "").replace("```", "").strip()
        
        # 2. Write File
        script_name = filename.replace(".png", ".py").replace(".pdf", ".py")
        script_path = os.path.join(output_dir, script_name)
        
        # Ensure dir exists
        os.makedirs(output_dir, exist_ok=True)
        
        with open(script_path, "w") as f:
            f.write(clean_code)
            
        # 3. Execute
        await self._execute_python(output_dir, script_name)


    def _clean_latex(self, text: str) -> str:
        return latex_ops.clean_latex(text)

    async def _generate_application_scenario(self, topic: str, context: str, output_base: str, mode: str) -> str:
        """Generates a 'Practical Application' section."""
        print(f"[AcademicWriter] 🏭 Engineering Practical Application Scenario ({mode})...")
        
        prompt = prompt_ops.build_application_prompt(mode, topic, context)
        content = await self._safe_chat(prompt, tier=ModelTier.STANDARD, task_type="paper_drafting")
        
        filename = "09_practical_application.tex"
        # Ensure 'sections' exists
        sections_dir = os.path.join(output_base, "sections")
        os.makedirs(sections_dir, exist_ok=True)
        
        with open(os.path.join(sections_dir, filename), "w") as f:
            f.write(self._clean_latex(content))
            
        return content

    async def _generate_demo_code(self, topic: str, context: str, output_dir: str):
        """Generates a runnable Streamlit Demo."""
        print(f"[AcademicWriter] 🖥️ Building Runnable Demo for: {topic}...")
        
        prompt = prompt_ops.build_demo_code_prompt(topic, context)
        code = await self._safe_chat(prompt, tier=ModelTier.STANDARD, task_type="coding")
        code = code.replace("```python", "").replace("```", "").strip()
        
        with open(os.path.join(output_dir, "demo_app.py"), "w") as f:
            f.write(code)
            
        print(f"[AcademicWriter] ✅ Generated demo_app.py")

    async def _compile_pdf(self, work_dir: str, tex_file: str):
        """Compiles LaTeX using latex_ops."""
        print(f"[AcademicWriter] ⚙️ Compiling {tex_file}...")
        
        # Heuristic for template root (same as before)
        repo_root = os.getcwd()
        template_root = os.path.join(repo_root, "research_vault", "templates")
        
        success = await latex_ops.compile_pdf_xetex(work_dir, tex_file, template_root)
        if success:
             print(f"[AcademicWriter] ✅ PDF Compiled Successfully.")
        else:
             print(f"[AcademicWriter] ⚠️ Compilation Failed.")

    def inject_figures(self, content_path: str, figures_dir: str):
        """Delegates to latex_ops."""
        print(f"[AcademicWriter] 🎨 Injecting figures...")
        latex_ops.inject_figures(content_path, figures_dir)

    async def _zip_package(self, project_dir: str, safe_topic: str) -> str:
        """Zips the project directory and commits changes to Git."""
        zip_path = os.path.join(self.output_base, f"{safe_topic}_Package.zip")
        shutil.make_archive(zip_path.replace(".zip", ""), 'zip', project_dir)
        
        # Git Commit (Auto-Save)
        try:
            # We assume git_manager has atomic commit logic exposed
            # Note: We are not changing git_executor interface here
            await self.git_manager.atom_commit("WRITER", "AUTO-SAVE", f"feat: Auto-generated research artifact for '{safe_topic}'")
            print(f"[AcademicWriter] 💾 Committed changes for {safe_topic}")
        except Exception as e:
            print(f"[AcademicWriter] ⚠️ Git Auto-Commit Failed: {e}")
            
        return zip_path


