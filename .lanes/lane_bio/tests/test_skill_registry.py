import sys
import os
sys.path.append(os.path.join(os.getcwd(), "src"))

from core.skill_registry import SkillRegistry
from skills.search_client import SearchClient

class MockModelClient:
    def __init__(self): pass

def test_registry_basic():
    print("Testing Registry Basic Functionality...")
    registry = SkillRegistry()
    
    # Mock Skill
    class TestSkill:
        """A sample test skill."""
        def test_method(self, arg1: str) -> int:
            """Does something useful."""
            return 1
            
    registry.register(TestSkill())
    
    context = registry.get_prompt_context()
    print("Context Output:\n", context)
    
    assert "TestSkill" in context
    assert "Does something useful" in context
    assert "test_method" in context
    print("✅ Basic Test Passed")

def test_orchestrator_integration():
    print("\nTesting Orchestrator Integration...")
    # Import here to avoid circular dependencies in global scope during partial runs
    from core.graph_orchestrator import GraphOrchestrator
    
    # Instantiate (Mocking complex deps with None as they are optional/mocked in init)
    # GraphOrchestrator handles None args gracefully
    graph = GraphOrchestrator(root_dir=".")
    
    context = graph.skill_registry.get_prompt_context()
    
    # Check for expected skills
    required_skills = ["SearchClient", "SSHExecutor", "KaggleExecutor", "EnvironmentManager"]
    
    missing = []
    for s in required_skills:
        if s not in context:
            missing.append(s)
            
    if missing:
        print(f"❌ Missing Skills in Registry: {missing}")
        exit(1)
    else:
        print(f"✅ All Core Skills Registered: {required_skills}")
        print("Sample Context snippet:\n", context[:500])

if __name__ == "__main__":
    test_registry_basic()
    test_orchestrator_integration()
