import asyncio
import os
import sys

# Ensure src is in path
sys.path.append(os.getcwd())

from src.research_bot.core.model_client import ModelClient
from src.research_bot.agents.paper_producer import PaperProducer

async def run_test():
    print("🧪 Starting Verification: Idea Integration")
    
    # 1. Initialize
    try:
        # Mock dependencies
        client = ModelClient()
        producer = PaperProducer(root_dir=os.getcwd(), model_client=client, git_manager=None)
        print("   ✅ PaperProducer Initialized")
    except Exception as e:
        print(f"   ❌ Init Failed: {e}")
        return

    # 2. Create Mock Structured Idea
    mock_idea = {
        "title": "Test Title",
        "abstract": "Test Abstract",
        "scientific_problem": "Problem X",
        "key_innovation": "Innovation Y",
        "methodology": "Method Z",
        "baselines": ["Baseline-A-2025", "Baseline-B"],
        "supporting_datasets": ["Dataset-1"],
        "broader_impact": "Huge Impact",
        "related_work": "Related Work Summary",
        "details": "Original messy details..."
    }
    
    # 3. Call produce_theory_draft (Mocking act to avoid real LLM calls if possible, 
    # but produce_theory_draft calls act. We can inspect the state before act() finishes or mocks act.)
    # Actually produce_theory_draft awaits act(). We can just run it and let it fail on 'think' or just check the state initialization logic.
    # To test nicely, we can subclass or just run up to the point of state creation.
    # Since we can't easily break the async function, let's rely on the formatted string presence in the log or check attributes if exposed.
    # The attributes are in `producer.theory_state`.
    
    # We will wrap it in a try/except because 'think' might fail without real API or mocking.
    # But we want to check `theory_state` which is set BEFORE `think`.
    
    # Trick: We can override `think` to return a dummy plan.
    async def mock_think(*args, **kwargs):
        return '{"strategy": "noop", "steps": []}'
    producer.think = mock_think
    
    async def mock_act(*args, **kwargs):
        return {"status": "success"}
    producer.act = mock_act
    
    print("   🏃 Running produce_theory_draft...")
    await producer.produce_theory_draft(mock_idea, venue="Test Venue")
    
    # 4. Verify State
    details = producer.theory_state.get('idea_details', '')
    print(f"   🔍 Inspecting Context...")
    
    if "Scientific Problem: Problem X" in details:
        print("   ✅ Scientific Problem found")
    else:
        print("   ❌ Scientific Problem MISSING")
        
    if "Baselines to Beat: ['Baseline-A-2025', 'Baseline-B']" in details:
         print("   ✅ Baselines found")
    else:
         print(f"   ❌ Baselines MISSING: {details[:200]}...")

if __name__ == "__main__":
    asyncio.run(run_test())
