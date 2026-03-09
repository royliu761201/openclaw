import asyncio
import sys
import os

# Ensure src is in path
sys.path.append(os.path.abspath("src"))

from agents.base_agent import BaseAgent
from core.model_client import ModelClient

class MockModelClient:
    async def chat(self, message, tier=None, task_type=None):
        print(f"  [MockClient] Intercepted request: {task_type}")
        if task_type == "planning":
            return '{"strategy": "Mock Strategy", "steps": [{"id": 1, "action": "mock_act", "params": "none"}]}'
        elif task_type == "reflection":
            return '{"success": true, "critique": "Mock Success", "next_step": "terminate"}'
        return "{}"

async def test_cognitive_loop():
    print("🧪 Testing Universal Cognitive Architecture (Zero-Cost Mode)...")
    
    # Use Mock Client to save tokens
    agent = BaseAgent(name="TestRationalAgent", model_client=MockModelClient())
    
    print("\n[Step 1] Assigning Complex Goal...")
    goal = "Research and summarize the latest advancements in 'Liquid Neural Networks' from 2024."
    
    print("\n[Step 2] Running Cognitive Loop (Think -> Act -> Reflect)...")
    try:
        review = await agent.run_task_loop(goal)
        print("\n✅ Loop Completed Successfully!")
        print(f"Final Outcome: {review}")
        
        # Simple Assertion
        assert review.get("success") is True
        
    except Exception as e:
        print(f"\n❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_cognitive_loop())
