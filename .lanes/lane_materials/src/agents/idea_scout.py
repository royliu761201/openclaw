from typing import Dict, Any, List, Optional
from core.model_client import ModelClient
from .base_agent import BaseAgent
from config import ModelTier
from schemas.artifacts import ResearchIdea

class IdeaScout(BaseAgent):
    """
    The 'Idea Scout' Agent.
    Responsible for generating high-quality, novel research ideas using an adversarial loop.
    """

    def __init__(self, model_client: Optional[ModelClient] = None, skill_registry = None):
        super().__init__(name="IdeaScout", model_client=model_client, skill_registry=skill_registry)

    async def generate_bound_idea(self, topic: str, context: str, history_context: str) -> Dict[str, Any]:
        """
        Generates a research idea using a Red Team / Blue Team loop.
        """
        self.log(f"💡 Scouting for Nobel-worthy ideas on: {topic}")
        
        # Get Skill Context if registry provided
        skill_context = ""
        if self.skill_registry:
            skill_context = self.skill_registry.get_prompt_context()

        # 1. Initial Proposal (Innovator)
        self.log("🗣️ Innovator: Proposing initial concept...")
        proposal_prompt = f"""
        Propose a **Research Evolution** (Next Version) based on the existing work: {topic}.
        
        Context (Existing Research State):
        {context}
        
        Available Skills & Tools:
        {skill_context}

        Previous Conversation History:
        {history_context}

        **CRITICAL INSTRUCTION**: 
        If 'EXISTING RESEARCH STATE' or 'EXISTING MANUSCRIPT' is found in the Context above:
        1. **Do NOT discard** the previous core logic unless it is fundamentally flawed.
        2. **EVOLVE** the specific sections that need improvement (e.g., weak theoretical bounds, missing experiments).
        3. **Innovate** on top of the provided baseline. Your goal is the **Next Version**, not a rewrite of the current one.
        
        If no context is found, propose a novel idea from scratch.

        The Idea MUST:
        1. **Disrupt the Paradigm**: Don't just improve SOTA by 10%; propose a fundamental shift.
        2. **Be Falsifiable**: Defines clear "Mid-term Exams" that could prove it wrong.
        3. **Be Feasible**: Runnable on 1xH100/A100 within 24h.

        Format: Title, Paradigm Shift (vs Old Way), Methodology (What changes from baseline?), Expected Impact.
        """
        
        current_idea = await self.client.chat(
            message=proposal_prompt,
            tier=ModelTier.STANDARD,
            task_type="idea_generation"
        )
        
        # 2. Adversarial Loop (The "Combat")
        rounds = 2
        history = []
        structured_idea = {"title": topic, "abstract": "", "details": ""}
        
        for i in range(rounds):
            self.log(f"⚔️ Round {i+1}: Reviewer vs Innovator")
            
            # A. Reviewer Attack (Critique)
            critique_prompt = f"""
            You are Reviewer #2 (Nobel Committee Member).
            Critique this research idea based on the **Heilmeier Catechism (Elevated)**:
            
            Idea Context:
            {current_idea}
            
            Attacks required:
            1. **The Delta Check**: Is this just a 10% improvement (Reject) or a Paradigm Shift (Accept)?
            2. **The "Why"**: Does it rely on a fundamental insight or just engineering stacking?
            3. **The Impact**: If successful, will this win a Best Paper Award?
            
            Be harsh. Reject incrementalism. Demand 10x impact.
            """
            critique = await self.client.chat(critique_prompt, tier=ModelTier.CRITICAL, task_type="critique")
            history.append(f"--- Round {i+1} Critique ---\n{critique}")
            
            # B. Innovator Defense / Refinement (Structured Output)
            refine_prompt = f"""
            You are the Lead Researcher.
            Reviewer #2 just attacked your idea:
            {critique}
            
            Task:
            1. Accept valid criticisms.
            2. Refute invalid ones.
            3. REWRITE the idea to be stronger, clearer, and more rigorous.
            4. Structure your output EXACTLY as a JSON object with these keys:
            4. Structure your output EXACTLY as a JSON object matching this schema:
               {{
                   "title": "Title of the paper",
                   "scientific_problem": "The core problem being addressed (1 sentence)",
                   "key_innovations": ["Innovation 1", "Innovation 2"],
                   "methodology": "Summary of the approach",
                   "keywords": ["List", "of", "keywords"],
                   "baselines": [{"name": "Baseline1", "description": "Why relevant"}],
                   "related_work": "Contrast with SOTA",
                   "technical_indicators": [{"name": "Accuracy", "target_value": ">95%", "description": "On ImageNet"}],
                   "supporting_datasets": [{"name": "Dataset1", "url": "http..."}],
                   "broader_impact": "Societal impact",
                   "references": [{"key": "AuthorYear", "title": "Title", "year": 2024}],
                   "abstract": "The full abstract (200 words)",
                   "details": "The generic details/proposal text (Markdown)"
               }}
            
            Example Output Format:
            {{
                "title": "Deep Active Inference",
                "scientific_problem": "Agents fail to explore in sparse reward settings.",
                "key_innovations": ["Combining variational inference with deep RL.", "New free energy bound."],
                "methodology": "We introduce a derived free energy bound...",
                "keywords": ["RL", "Active Inference"],
                "baselines": [{"name": "PPO", "citation_key": "Schulman2017"}, {"name": "SAC", "description": "Off-policy baseline"}],
                "related_work": "Differs from Hafner et al by...",
                "technical_indicators": [{"name": "VFE", "target_value": "< 0.1", "description": "Variational Free Energy bound"}, {"name": "Sample Efficiency", "target_value": "> SOTA", "description": "Steps to solve"}],
                "supporting_datasets": [{"name": "Atari", "url": "https://gym.../atari"}],
                "broader_impact": "Automation safety.",
                "references": [{"key": "Hafner2020", "title": "Dream to Control", "year": 2020}],
                "abstract": "We propose...",
                "details": "## Introduction..."
            }}
            
            ENSURE THE OUTPUT IS VALID JSON. Do not include markdown formatting like ```json.
            """
            # Use JSON mode if possible, or strong prompting
            current_idea_raw = await self.client.chat(
                refine_prompt, 
                tier=ModelTier.STANDARD, 
                task_type="brainstorming"
            )
            
            # Attempt to parse JSON using Schema
            try:
                # Strip potential markdown constraints
                clean_json = current_idea_raw.replace("```json", "").replace("```", "").strip()
                
                # Schema Validation
                validated_idea = ResearchIdea.model_validate_json(clean_json)
                structured_idea = validated_idea.model_dump() # Convert back to dict for generic handling if needed, or keep as object
                
                # If we want to persist efficiently
                # validated_idea.save(f"idea_{i}.json") 

                current_idea = structured_idea.get("details", str(structured_idea))
                
            except Exception as e:
                self.log(f"⚠️ LLM Schema Validation failed: {e}. Falling back to raw text.")
                current_idea = current_idea_raw
                structured_idea = {"title": "Parse Error", "abstract": "", "details": current_idea_raw}

            
        self.log("🏆 Idea Finalized after Combat.")
        # Return structured Dict
        return {"idea": structured_idea, "review_history": "\n".join(history)}
