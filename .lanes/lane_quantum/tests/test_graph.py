import asyncio
import sys
import os

# Ensure src is in path
sys.path.append(os.path.join(os.getcwd(), "src"))

from core.graph_orchestrator import GraphOrchestrator

async def main():
    print("=== Testing GraphOrchestrator (LangGraph) ===")
    try:
        orchestrator = GraphOrchestrator()
        
        print("\nStarting Cycle for topic: 'Autonomous Science Agents'")
        await orchestrator.run_cycle("Autonomous Science Agents")
        
        print("\n✅ Cycle Complete.")
    except Exception as e:
        print(f"\n❌ Graph Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
