import asyncio
import sys
import os

# Add src to path
sys.path.append(os.path.abspath("src"))

from agents.idea_scout import IdeaScout
from config import ModelTier

async def test_idea_scout():
    print("🧪 Testing IdeaScout Agent...")
    
    # Initialize
    scout = IdeaScout()
    
    # Mock parameters
    topic = "Simple Test Topic"
    context = "Existing research context..."
    history = "User: Let's research something simple."
    
    # We want to verify it CALLS the model and returns a structure.
    # To avoid spending money/time on a full loop, we can just run it
    # OR we can trust the previous step if we just want to verify import/class structure.
    # Let's run it but interrupt or keep it short if possible.
    # Actually, the IdeaScout hardcodes 'rounds=2'. 
    # For a quick verification, we assume the code works if it runs without import errors
    # and starts the chat.
    
    # Let's just verify instantiation and method signature for now to be fast,
    # or run a full pass if the user wants "Extraction" verified.
    # Given the user says "Refine Idea Scout", they likely want to see it work.
    
    result = await scout.generate_bound_idea(topic, context, history)
    
    print("✅ IdeaScout finished.")
    print(f"Idea Keys: {result.keys()}")
    print(f"Review History Length: {len(result['review_history'])}")

if __name__ == "__main__":
    try:
        asyncio.run(test_idea_scout())
    except Exception as e:
        print(f"❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()
