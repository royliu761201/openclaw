import asyncio
import os
import sys

# Ensure src is in path
sys.path.append(os.getcwd())

from src.research_bot.core.model_client import ModelClient
from src.research_bot.skills.search_client import SearchClient 
from src.research_bot.agents.paper_producer import PaperProducer

async def run_test():
    print("🧪 Starting Verification: Auto-Venue Selection")
    
    # 1. Initialize
    try:
        client = ModelClient()
        producer = PaperProducer(root_dir=os.getcwd(), model_client=client, git_manager=None)
        print("   ✅ PaperProducer Initialized")
    except Exception as e:
        print(f"   ❌ Init Failed: {e}")
        return

    # 2. Mock suggest_venues (Simulate intelligent decision)
    # We override the real method to avoid API costs and deterministically test logic
    async def mock_suggest_venues(title, abstract):
        return [{"name": "Nature", "tier": "SCI-Q1", "reason": "High impact topic"}]
    
    producer.sub_manager.suggest_venues = mock_suggest_venues
    
    # 3. Call produce_theory_draft with venue="Auto"
    # We also mock 'think' and 'act' to stop execution early
    async def mock_act(*args, **kwargs):
        return {"status": "success"}
    producer.act = mock_act
    
    async def mock_think(*args, **kwargs):
        return '{"strategy":"noop", "steps": []}'
    producer.think = mock_think

    print("   🏃 Running produce_theory_draft(venue='Auto')...")
    # Using a dummy dict for idea_data
    mock_idea = {"title": "A Generic Science Paper", "abstract": "We solved science."}
    
    await producer.produce_theory_draft(mock_idea, venue="Auto")
    
    # 4. Verify State
    selected_venue = producer.theory_state.get('venue')
    print(f"   🔍 Selected Venue: {selected_venue}")
    
    if selected_venue == "Nature":
        print("   ✅ Auto-Selection Success: Correctly picked Nature")
    else:
        print(f"   ❌ Auto-Selection Failed: Got {selected_venue}")

if __name__ == "__main__":
    asyncio.run(run_test())
