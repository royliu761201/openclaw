import asyncio
import os
import sys

# Ensure src is in path
sys.path.append(os.getcwd())

from src.research_bot.core.model_client import ModelClient
from src.research_bot.agents.idea_scout import IdeaScout
from src.research_bot.schemas.idea import ResearchIdea

async def run_test():
    print("🧪 Starting Verification: IdeaScout Enrichment")
    
    # 1. Initialize
    try:
        client = ModelClient()
        scout = IdeaScout(model_client=client)
        print("   ✅ IdeaScout Initialized")
    except Exception as e:
        print(f"   ❌ Init Failed: {e}")
        return

    # 2. Setup Mock State
    scout.idea_state = {
        "topic": "Test Topic",
        "current_idea_raw": "A new method for AI.",
        "last_critique": "The idea is too vague. It lacks a specific problem definition and baselines.",
        "review_history": [],
        "context": "Testing environment."
    }
    
    # 3. Trigger Refine Draft (which uses the new Schema)
    print("   🏃 Running refine_draft with Structured Output...")
    await scout.refine_draft(None)
    
    # 4. Assess Result
    structured = scout.idea_state.get("structured_idea")
    
    if not structured:
        print("   ❌ Failed: No structured idea found.")
        return
        
    print(f"   📂 Result Keys: {list(structured.keys())}")
    
    required_keys = [
        "scientific_problem", 
        "key_innovation", 
        "baselines", 
        "supporting_datasets", 
        "broader_impact"
    ]
    
    missing = [k for k in required_keys if k not in structured]
    
    if not missing:
        print("   ✅ All required fields present!")
        print(f"   - Problem: {structured.get('scientific_problem')}")
        print(f"   - Innovation: {structured.get('key_innovation')}")
        print(f"   - Baselines: {structured.get('baselines')}")
    else:
        print(f"   ❌ Missing keys: {missing}")

if __name__ == "__main__":
    asyncio.run(run_test())
