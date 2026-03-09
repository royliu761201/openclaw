import asyncio
import os
import sys

# Ensure src is in path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from src.research_bot.core.graph_orchestrator import GraphOrchestrator
from src.research_bot.config import ModelTier

async def main():
    print("=== Starting ResearchBot Verification ===")
    
    try:
        # Initialize GraphOrchestrator (The Graph Brain)
        bot = GraphOrchestrator(root_dir=os.getcwd())
    except ValueError as e:
        print(f"Initialization Error: {e}")
        return
    
    # Run Cycle
    print("[verify] Triggering run_cycle...")
    # GraphOrchestrator.run_cycle signature: (topic, thread_id, autonomous_mode)
    await bot.run_cycle(topic="Transformer Architecture variants", thread_id="verify_run_1", autonomous_mode=True)
    
    print("\n=== Verification Complete ===")
    print("Check ./test_research_data for the git history and files.")

if __name__ == "__main__":
    asyncio.run(main())
