
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional
import random

@dataclass
class OrganizationConfig:
    name: str = "University_A"
    depth: int = 5
    width_per_node: int = 3
    
@dataclass
class CognitiveProfile:
    risk_aversion: float = 0.5
    compliance_bias: float = 0.5
    metric_focus: float = 0.5

@dataclass
class Action:
    name: str
    params: Dict[str, str] = field(default_factory=dict)
    
    def __str__(self):
        return f"{self.name}({self.params})"

class Constitution:
    """
    Symbolic layer determining legal actions.
    """
    def __init__(self, role: str):
        self.role = role
        
    def get_legal_actions(self, state: Dict) -> List[str]:
        # Minimal constraints logic
        actions = ["Escalate", "Defer"]
        if "budget" in state and state["budget"] > 0:
            actions.append("ApproveBudget")
        
        if self.role == "Dean":
            actions.append("IssuePolicy")
        elif self.role == "Frontline":
            actions.append("Implement")
            
        return actions

class Agent:
    """
    Constitutional LLM Agent.
    """
    def __init__(self, agent_id: str, role: str, profile: CognitiveProfile):
        self.id = agent_id
        self.role = role
        self.profile = profile
        self.constitution = Constitution(role)
        self.history = []
        
    def decide(self, context: Dict) -> Action:
        # 1. Constitutional Check
        legal_moves = self.constitution.get_legal_actions(context)
        
        # 2. Cognitive Kernel (Mocked for now)
        # In real Org-GPT, this calls an LLM api
        chosen_move = random.choice(legal_moves)
        
        return Action(name=chosen_move)
