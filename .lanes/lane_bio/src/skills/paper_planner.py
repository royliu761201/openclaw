
import os
import asyncio
from typing import Dict, Any, Optional
from core.model_client import ModelClient
from config import ModelTier, PAPER_WORKSPACE_DIR
from .base_skill import BaseSkill

class PaperPlanner(BaseSkill):
    """
    Skill for planning academic papers:
    1. Generates structured outlines based on venue (e.g., NeurIPS, CVPR).
    2. Supports 'Auto-Review' by an LLM Persona (Area Chair).
    3. Refines outlines based on feedback.
    """

    def __init__(self, model_client: ModelClient, output_dir: str = PAPER_WORKSPACE_DIR, config: Optional[Dict] = None):
        super().__init__(config)
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.client = model_client

    def verify(self) -> bool:
        """Checks if the planner is ready (ModelClient is connected)."""
        return self.client is not None

    async def generate_outline(self, topic: str, venue: str, context: str, output_dir: Optional[str] = None) -> str:
        """Generates a structured outline for the given topic and venue."""
        print(f"[PaperPlanner] 📝 Planning Outline for '{topic}' -> {venue}...")
        
        prompt = f"""
        Role: Senior Research Scientist targeting {venue}.
        Task: Create a detailed, Section-by-Section OUTLINE for a paper on: "{topic}".
        
        Context (May contain existing draft/LaTeX):
        {context} 
        
        **CRITICAL INSTRUCTION**:
        1. **Context Inheritance**: If an existing draft is provided in the Context, your Outline MUST **preserve** the successful parts (e.g. valid derivations, strong related work).
        2. **Iterate**: Only propose changes to sections that need improvement or are affected by the new ideas.
        3. **Expansion**: Expand weak parts. Do NOT propose a completely different structure unless necessary.
        
        Requirements:
        1. **Structure**: Follow standard {venue} structure (e.g., Abstract -> Intro -> Related -> Method -> Exp -> Conclusion).
        2. **Granularity**: For each Section, list 2-3 Subsections.
        3. **Content**: For each Subsection, provide:
           - **Key Argument**: What is the main point?
           - **Estimated Word Count**: e.g., (400 words).
           - **Key Citations**: Mention 1-2 relevant papers if known.
        4. **Format**: Markdown. Use '##' for Sections and '###' for Subsections.
        
        Output: The structured Markdown Outline ONLY.
        """
        
        outline = await self.client.chat(prompt, tier=ModelTier.STANDARD, task_type="reasoning")
        
        # Save artifact
        target_dir = output_dir if output_dir else self.output_dir
        os.makedirs(target_dir, exist_ok=True)
        filename = f"outline_{venue.lower().replace(' ', '_')}.md"
        filepath = os.path.join(target_dir, filename)
        with open(filepath, "w") as f:
            f.write(outline)
            
        print(f"[PaperPlanner] ✅ Outline saved to {filepath}")
        return outline

    async def review_outline(self, outline: str, venue: str, autonomous: bool = True) -> Dict[str, Any]:
        """
        Reviews the outline.
        If autonomous=True, simulates an 'Area Chair' review.
        """
        if not autonomous:
            # In a real app, this would pause for human input.
            # For this agent, we return a placeholder or wait signal.
            return {"status": "WAITING_FOR_HUMAN", "critique": None}

        print(f"[PaperPlanner] 🕵️ Auto-Reviewing Outline (Persona: {venue} Area Chair)...")
        
        prompt = f"""
        Role: {venue} Area Chair / Senior Reviewer.
        Task: Critique the following Paper Outline.
        
        Outline:
        {outline}
        
        Criteria:
        1. **Novelty**: Is the contribution clear?
        2. **Logic Coherence**: Does the Method follow from the Problem? Do Experiments validate the Method?
        3. **Completeness**: Are baselines missing? Is Related Work sufficient?
        4. **Feasibility**: Can this be done in 8-9 pages?
        
        Output:
        1. **Decision**: "PASS" or "REJECT".
        2. **Critique**: A bulleted list of weaknesses (if any).
        """
        
        critique = await self.client.chat(prompt, tier=ModelTier.STANDARD, task_type="reasoning")
        
        status = "PASS" if "PASS" in critique.upper() else "REJECT"
        print(f"[PaperPlanner] 🏁 Review Result: {status}")
        
        return {
            "status": status,
            "critique": critique
        }

    async def refine_outline(self, outline: str, critique: str) -> str:
        """Refines the outline based on the critique."""
        print(f"[PaperPlanner] 🔧 Refining Outline based on feedback...")
        
        prompt = f"""
        Role: Senior Research Scientist.
        Task: Improve the Paper Outline based on the Reviewer's Critique.
        
        Critique:
        {critique}
        
        Original Outline:
        {outline}
        
        Instruction: Return the IMPROVED Markdown Outline. Maintain the same format.
        """
        
        refined_outline = await self.client.chat(prompt, tier=ModelTier.STANDARD, task_type="reasoning")
        
        # Overwrite or save version
        filepath = os.path.join(self.output_dir, "outline_refined.md")
        with open(filepath, "w") as f:
            f.write(refined_outline)
            
        print(f"[PaperPlanner] ✅ Refined Outline saved to {filepath}")
        return refined_outline
