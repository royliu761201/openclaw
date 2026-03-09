from typing import Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class AnalysisResult:
    status: str  # "SUPPORTED", "CONTRADICTED", "INCONCLUSIVE"
    reasoning: str
    next_action: str # "WRITE", "REFINE", "ABORT"
    suggested_task: Optional[str] = None

class AnalysisEngine:
    """
    Implements the "Scientific Falsification" logic.
    Compares Experimental Results against Theoretical Hypotheses.
    """
    def __init__(self, model_client):
        self.client = model_client

    async def analyze_results(self, hypothesis: str, metrics: Dict[str, float], visual_path: Optional[str] = None) -> AnalysisResult:
        """
        Critiques the results. if visual_path is provided, uses Vision model.
        """
        prompt = f"""
        You are the Chief Reviewer. Analyze these results against the hypothesis.
        
        Hypothesis: {hypothesis}
        Actual Metrics: {metrics}
        
        Determine:
        1. Consistency: Do the metrics support the hypothesis?
        2. Robustness: Is this likely noise or a real signal?
        3. Root Cause: If contradictory, why? (Distribution shift? Bad checks?)
        
        Return JSON:
        {{
            "status": "SUPPORTED" | "CONTRADICTED" | "INCONCLUSIVE",
            "reasoning": "...",
            "next_action": "WRITE" | "REFINE" | "ABORT",
            "suggested_task": "Description of next experiment if REFINE"
        }}
        """
        
        # If visual path exists, we would use a multimodal call here
        # For now, we simulate the text-only path
        
        response_text = await self.client.chat("tier_1", prompt, structured=True)
        
        # Mock parsing logic since we don't have the real JSON parser hooked up in this snippet
        # In production, use the Pydantic parser from Phase 4
        import json
        try:
            data = json.loads(response_text)
            return AnalysisResult(**data)
        except:
            # Fallback for non-JSON response
            return AnalysisResult(
                status="INCONCLUSIVE", 
                reasoning=f"Failed to parse LLM response: {response_text[:100]}", 
                next_action="REFINE"
            )

    async def result_critique_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Reflects on the latest experiment results.
        """
        result = state.get("latest_metrics", {})
        hypothesis = state.get("proposal", {}).get("hypothesis", "No hypothesis found")
        
        analysis = await self.analyze_results(hypothesis, result)
        
        state["analysis_log"] = state.get("analysis_log", []) + [analysis]
        
        if analysis.status == "CONTRADICTED":
            print(f"[Analysis] Hypothesis contradicted: {analysis.reasoning}")
            # Generate Refinement Task
            if analysis.suggested_task:
                 state["task_queue"].append({"type": "refinement", "desc": analysis.suggested_task})
            state["phase"] = "refining"
        else:
            print(f"[Analysis] Hypothesis supported/inconclusive. Proceeding to write.")
            state["phase"] = "writing"
            
        return state
