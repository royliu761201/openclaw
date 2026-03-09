from typing import Optional
from core.model_client import ModelClient

class BaseAgent:
    """
    Base class for all ResearchBot Agents.
    Provides standard initialization for ModelClient, SkillRegistry, and Logging.
    """
    
    def __init__(self, name: str, root_dir: str = ".", model_client: Optional[ModelClient] = None, skill_registry = None):
        self.name = name
        self.root_dir = root_dir
        self.client = model_client or ModelClient()
        self.skill_registry = skill_registry
        self.print_logo()

    def log(self, message: str):
        """Standardized logging with Agent Prefix."""
        print(f"[{self.name}] {message}")
        
    def print_logo(self):
        """Optional hook for startup banner."""
        pass

    async def think(self, goal: str, context: str = "") -> str:
        """
        Phase 1: PLANNING
        Generates a step-by-step plan to achieve the goal.
        """
        self.log(f"🧠 Thinking about: {goal}...")
        prompt = f"""
        GOAL: {goal}
        CONTEXT: {context}
        
        TASK:
        Create a structured, step-by-step Execution Plan.
        The plan should be broken down into atomic actions that an autonomous agent can perform.
        
        OUTPUT FORMAT (JSON):
        {{
            "strategy": "High-level approach...",
            "steps": [
                {{"id": 1, "action": "search_web", "params": "query string"}},
                {{"id": 2, "action": "write_file", "params": "filename..."}}
            ]
        }}
        """
        plan = await self.client.chat(prompt, tier="planning", task_type="planning")
        return plan

    async def act(self, plan: str):
        """
        Phase 2: EXECUTION
        (To be overridden by subclasses or implemented with a generic executor)
        For now, we just log the plan.
        """
        self.log(f"⚙️ Executing Plan: {plan[:100]}...")
        # In a real system, this would parse the JSON and call matching tools.
        return {"status": "success", "output": "Plan Executed (Mock)"}

    async def reflect(self, result: dict, original_goal: str) -> dict:
        """
        Phase 3: REFLECTION
        Reviews the outcome against the goal.
        """
        self.log("🪞 Reflecting on outcome...")
        prompt = f"""
        ORIGINAL GOAL: {original_goal}
        EXECUTION RESULT: {result}
        
        TASK:
        Did we succeed? If not, what should be changed?
        
        OUTPUT FORMAT (JSON):
        {{
            "success": true/false,
            "critique": "Analysis of what happened...",
            "next_step": "terminate" or "retry_with_new_plan"
        }}
        """
        reflection = await self.client.chat(prompt, tier="critical", task_type="reflection")
        return reflection

    async def run_task_loop(self, goal: str):
        """
        The Universal Cognitive Loop.
        """
        plan = await self.think(goal)
        result = await self.act(plan)
        review = await self.reflect(result, goal)
        
        self.log(f"🏁 Task Completion Review: {review}")
        return review
