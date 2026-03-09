from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import json
import os

@dataclass
class TraceLink:
    """
    Represents a link in the Idea-Experiment-Paper Triangle.
    """
    source_type: str # "Idea", "Experiment", "PaperSection"
    source_id: str
    target_type: str
    target_id: str
    relation: str # "validates", "implements", "supports", "refutes"
    metadata: Dict[str, Any] = field(default_factory=dict)

class DoubleHelix:
    """
    The Nexus-AI4S 'Double Helix' Engine.
    Manages the interplay between Theory (Idea/Paper) and Data (Experiment).
    Enforces Traceability and Logical Consistency.
    """
    def __init__(self, base_path=".agent/helix"):
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)
        self.links: List[TraceLink] = []
        self.load_links()

    def load_links(self):
        link_path = os.path.join(self.base_path, "traceability_map.json")
        if os.path.exists(link_path):
            with open(link_path) as f:
                data = json.load(f)
                self.links = [TraceLink(**d) for d in data]

    def save_links(self):
        link_path = os.path.join(self.base_path, "traceability_map.json")
        with open(link_path, "w") as f:
            json.dump([l.__dict__ for l in self.links], f, indent=2)

    def add_link(self, source_type, source_id, target_type, target_id, relation, metadata=None):
        link = TraceLink(source_type, source_id, target_type, target_id, relation, metadata or {})
        self.links.append(link)
        self.save_links()
        print(f"[DoubleHelix] Linked {source_type}:{source_id} --{relation}--> {target_type}:{target_id}")

    def verify_consistency(self, paper_claim_id: str) -> Dict[str, Any]:
        """
        Checks if a Paper Claim is supported by Experiments.
        """
        # Find experiments linked to this claim (or the idea that generated the claim)
        # This is a simplified traversal
        experiments = [l for l in self.links if l.target_id == paper_claim_id and l.relation == "supports"]
        
        if not experiments:
            return {"status": "UNSUPPORTED", "reason": "No supporting experiments found."}
        
        # Check correctness of experiments (mock logic)
        return {"status": "SUPPORTED", "evidence": [e.source_id for e in experiments]}

    def generate_feedback_loop(self, experiment_result: Dict) -> str:
        """
        Experiment -> Idea Feedback.
        If result contradicts idea, generate refinement directive.
        """
        if experiment_result.get("status") == "failed":
            return "REFINE_IDEA: Experiment failed to validate hypothesis. Check assumptions."
        return "PROCEED_PAPER: Hypothesis validated."

    def scan_paper_placeholders(self, latex_content: str) -> List[Dict[str, str]]:
        """
        Scans LaTeX content for defining experimental placeholders.
        Pattern: \\newcommand{\\ResultMetricA}{PENDING}
        """
        import re
        placeholders = []
        # Regex to find commands defined as 'PENDING' or similar markers
        # Captures command name (e.g. ResultMetricA)
        pattern = r"\\newcommand\{\\([a-zA-Z0-9_]+)\}\{(PENDING|TBD|TODO)\}"
        
        matches = re.finditer(pattern, latex_content)
        for m in matches:
            placeholders.append({
                "command": m.group(1),
                "status": m.group(2),
                "type": "metric_placeholder"
            })
        
        print(f"[DoubleHelix] Found {len(placeholders)} placeholders in paper.")
        return placeholders

    def derive_experiments(self, placeholders: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Logic to convert placeholders into Experiment Tasks.
        e.g. ResultAccuracy -> Task: 'Run evaluation to get accuracy'
        """
        tasks = []
        for p in placeholders:
            # Simple heuristic mapping for now. In real system, LLM does this via prompt.
            if "Accuracy" in p['command']:
                tasks.append({"type": "experiment", "metric": "accuracy", "goal": "Fill " + p['command']})
            elif "Speed" in p['command']:
                tasks.append({"type": "experiment", "metric": "latency", "goal": "Fill " + p['command']})
        return tasks
