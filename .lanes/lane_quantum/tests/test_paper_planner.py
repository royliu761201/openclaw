
import asyncio
import sys
import os

# Ensure import path
sys.path.append(os.path.abspath("src"))

from skills.paper_planner import PaperPlanner

async def test_planner():
    planner = PaperPlanner()
    
    topic = "LLMs for Climate Change Mitigation"
    venue = "NeurIPS 2026"
    context = "We propose a new framework 'Climate-GPT' using RAG to query IPCC reports and optimize energy grid policies."
    
    # 1. Generate
    print("--- 1. Generating Outline ---")
    outline = await planner.generate_outline(topic, venue, context)
    print(f"Outline length: {len(outline)} chars")
    
    # 2. Review (Auto)
    print("\n--- 2. Auto-Review ---")
    review_result = await planner.review_outline(outline, venue, autonomous=True)
    print(f"Status: {review_result['status']}")
    print(f"Critique snippet: {review_result['critique'][:200]}...")
    
    # 3. Refine (if REJECT)
    # We force refinement just to test the method
    print("\n--- 3. Refining ---")
    new_outline = await planner.refine_outline(outline, review_result['critique'])
    print(f"Refined Outline length: {len(new_outline)} chars")
    
    if len(new_outline) > 0:
        print("\n✅ Test Passed!")

if __name__ == "__main__":
    asyncio.run(test_planner())
