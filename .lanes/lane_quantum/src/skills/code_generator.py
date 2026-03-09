import os
from typing import Dict, Optional, Union, List
from .base_skill import BaseSkill
from core.model_client import ModelClient
from config import ModelTier
from .code_ops import gen_ops

class CodeGenerator(BaseSkill):
    """
    Specialized Skill for Generating Research Code (ML Experiment & Visualization).
    Centralizes the 'ML Engineer' and 'Viz Expert' personas.
    Refactored to delegate prompt engineering to `code_ops.gen_ops`.
    """
    
    def __init__(self, model_client: ModelClient, config: Optional[Dict] = None):
        super().__init__(config)
        self.client = model_client

    async def verify(self) -> bool:
        """
        Verifies the skill is operational.
        """
        return self.client is not None

    async def generate_experiment_script(self, topic: str, context: str, framework: str = "pytorch") -> str:
        """Generates a standalone Python training/eval script."""
        prompt = gen_ops.build_experiment_prompt(topic, context, framework)
        code = await self.client.chat(prompt, tier=ModelTier.STANDARD, task_type="coding")
        return self._clean_code(code)

    async def generate_visualization_script(self, topic: str, context: str, output_filename: str = "plot.png", images: Optional[List[str]] = None) -> str:
        """
        Generates a Matplotlib/Seaborn script for figures.
        """
        text_prompt = gen_ops.build_viz_prompt(topic, context, output_filename)
        
        # Multimodal Construction
        prompt_content = [text_prompt]
        if images:
            prompt_content.extend(images)
        else:
            prompt_content = text_prompt 

        code = await self.client.chat(prompt_content, tier=ModelTier.STANDARD, task_type="coding")
        return self._clean_code(code)

    async def generate_demo_app(self, topic: str, context: str, images: Optional[List[str]] = None) -> str:
        """
        Generates a simple Streamlit/Gradio demo app.
        """
        text_prompt = gen_ops.build_demo_prompt(topic, context)
        
        prompt_content = [text_prompt]
        if images:
            prompt_content.extend(images)
        else:
            prompt_content = text_prompt

        code = await self.client.chat(prompt_content, tier=ModelTier.STANDARD, task_type="coding")
        return self._clean_code(code)

    async def optimize_code(self, code: str, objective: str = "efficiency") -> str:
        """
        Refactors code for Speed, Readability, or Memory usage.
        """
        prompt = gen_ops.build_optimize_prompt(code, objective)
        refined_code = await self.client.chat(prompt, tier=ModelTier.STANDARD, task_type="coding")
        return self._clean_code(refined_code)

    def _clean_code(self, raw_text: str) -> str:
        """Strips markdown formatting."""
        code = raw_text.replace("```python", "").replace("```", "").strip()
        return code
