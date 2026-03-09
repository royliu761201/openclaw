
import networkx as nx
from typing import Dict, List
from .agent import Agent, CognitiveProfile, Action

class Organization:
    """
    Hierarchical Graph Environment.
    """
    def __init__(self, config):
        self.config = config
        self.graph = nx.DiGraph()
        self.agents: Dict[str, Agent] = {}
        self._build_hierarchy()
        
    def _build_hierarchy(self):
        # Root
        root_id = "Exec_0"
        self._add_agent(root_id, "Executive")
        
        current_level = [root_id]
        
        for level in range(1, self.config.depth):
            next_level = []
            role = self._get_role_name(level)
            for parent_id in current_level:
                for child_idx in range(self.config.width_per_node):
                    child_id = f"{role}_{level}_{len(self.agents)}"
                    self._add_agent(child_id, role)
                    self.graph.add_edge(parent_id, child_id)
                    next_level.append(child_id)
            current_level = next_level
            
    def _get_role_name(self, level):
        if level == 1: return "Dean"
        if level == 2: return "Chair"
        return "Frontline"
        
    def _add_agent(self, agent_id, role):
        # Random profile for now
        profile = CognitiveProfile()
        self.agents[agent_id] = Agent(agent_id, role, profile)
        self.graph.add_node(agent_id)
        
    def propagate_policy(self, policy_text: str):
        """
        Simulate top-down propagation.
        """
        print(f"📢 Executive Issue: {policy_text}")
        # Top-down traversal
        visited = set()
        queue = ["Exec_0"]
        
        while queue:
            current_id = queue.pop(0)
            agent = self.agents[current_id]
            
            # Agent decides based on policy
            action = agent.decide({"policy": policy_text})
            print(f"  ➡️ {agent.role} ({agent.id}) chose: {action}")
            
            # Pass to children
            children = list(self.graph.successors(current_id))
            queue.extend(children)
