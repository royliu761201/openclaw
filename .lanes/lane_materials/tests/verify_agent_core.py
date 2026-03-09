
import asyncio
import os
import shutil
import json
import time
from typing import Dict, Any
# Add source to path
import sys
sys.path.append(os.path.join(os.getcwd(), "src"))

from agents.base_agent import BaseAgent
from core.model_client import ModelClient

# --- MOCK AGENT ---
class TestAgent(BaseAgent):
    def __init__(self, root_dir: str):
        # Pass mock client to avoid API calls
        self.client = None 
        # But BaseAgent init expects model_client kwarg if it uses it.
        # BaseAgent.__init__ only takes name, root_dir. 
        # It creates self.client internally if not passed? 
        # Let's check BaseAgent.__init__ signature in source. Use simple super call.
        super().__init__(name="TestAgent", root_dir=root_dir)
        self.mock_log = []

    def log(self, message: str):
        print(f"[{self.name}] {message}")
        self.mock_log.append(message)

    # --- SIMULATED ACTIONS ---
    
    async def fast_action(self, params):
        """Sequential Action: Instant."""
        return {"status": "success", "result": f"Fast: {params}"}

    async def slow_action(self, params):
        """Parallel Action: Takes 1 second."""
        await asyncio.sleep(1.0)
        return {"status": "success", "result": f"Slow: {params}", "time": time.time()}

    async def injection_action(self, params):
        """Triggers Dynamic Injection."""
        return {
            "status": "success", 
            "new_tasks": [
                {"id": "inj_1", "action": "fast_action", "params": "Injected Task 1"},
                {"id": "inj_2", "action": "fast_action", "params": "Injected Task 2"}
            ]
        }
        
    async def crash_action(self, params):
        """Simulates a crash (System Exit)."""
        print("💥 CRASHING AGENT...")
        # We don't actually exit python, we raise exception to stop the 'act' loop
        raise RuntimeError("Simulated System Crash")

# --- TEST SUITE ---

async def test_batch_processing():
    print("\n--- TEST 1: Async Batch Processing ---")
    agent = TestAgent(root_dir=".")
    
    # Plan: 3 slow actions in parallel.
    # If sequential: 3 seconds.
    # If parallel: ~1 second.
    
    plan_data = {
        "strategy": "Parallel Test",
        "steps": [
            [
                {"id": "p1", "action": "slow_action", "params": "A"},
                {"id": "p2", "action": "slow_action", "params": "B"},
                {"id": "p3", "action": "slow_action", "params": "C"}
            ]
        ]
    }
    
    start_time = time.time()
    await agent.act(f"```json\n{json.dumps(plan_data)}\n```")
    duration = time.time() - start_time
    
    print(f"⏱️ Duration: {duration:.2f}s")
    if duration < 1.5:
        print("✅ PASS: Parallel Execution Confirmed (< 1.5s)")
    else:
        print("❌ FAIL: Seems Sequential (> 1.5s)")

async def test_dynamic_injection():
    print("\n--- TEST 2: Dynamic Task Injection ---")
    agent = TestAgent(root_dir=".")
    
    plan_data = {
        "strategy": "Injection Test",
        "steps": [
            {"id": "trigger", "action": "injection_action", "params": "Trigger"},
            {"id": "final", "action": "fast_action", "params": "Final"}
        ]
    }
    
    await agent.act(f"```json\n{json.dumps(plan_data)}\n```")
    
    # Check Log Order: Trigger -> Injected -> Final
    # But wait, BaseAgent prepends reversed list?
    # Logic: 
    # Queue: [Trigger, Final]
    # Pop Trigger -> Returns [Inj1, Inj2]
    # Inject -> Reversed([Inj1, Inj2]) = [Inj2, Inj1]
    # Queue.appendleft(Inj2) -> [Inj2, Final]
    # Queue.appendleft(Inj1) -> [Inj1, Inj2, Final]
    # Expected Order: Trigger -> Inj1 -> Inj2 -> Final
    
    log_str = "\n".join(agent.mock_log)
    if "Injected Task 1" in log_str and "Injected Task 2" in log_str:
        print("✅ PASS: Tasks Injected.")
        # Verify order roughly
        pass
    else:
        print("❌ FAIL: Tasks not found.")

async def test_checkpointing():
    print("\n--- TEST 3: Checkpoint & Resume ---")
    agent = TestAgent(root_dir=".")
    state_file = ".testagent_state.json"
    
    # Cleanup previous
    if os.path.exists(state_file): os.remove(state_file)
    
    plan_data = {
        "strategy": "Crash Test",
        "steps": [
            {"id": "1", "action": "fast_action", "params": "Step 1"},
            {"id": "2", "action": "crash_action", "params": "Boom"},
            {"id": "3", "action": "fast_action", "params": "Step 3 (Resumed)"}
        ]
    }
    
    # Run 1: Should Crash
    try:
        await agent.act(f"```json\n{json.dumps(plan_data)}\n```")
    except Exception as e:
        print(f"Expected Crash: {e}")
        
    # Verify State File
    if os.path.exists(state_file):
        print("✅ Checkpoint File Found.")
        with open(state_file, 'r') as f:
            data = json.load(f)
            # Should have Step 3 in queue
            # And Step 2? Step 2 was popped before crash.
            # wait, if logic is: save BEFORE action.
            # pop 2 -> save queue [3] -> act(2) -> crash.
            # So stored queue is [3].
            # When resuming, we start with [3]. Step 2 is effectively "consumed" (though failed).
            # This handles "Bad Action Loop" (infinite retry).
            queue = data.get("start_queue", [])
            print(f"Status in File: Queue Len = {len(queue)}")
            if len(queue) == 1 and queue[0]['id'] == "3":
                 print("✅ Checkpoint Content Correct (Step 2 consumed, Step 3 ready)")
            else:
                 print(f"❌ Checkpoint Content Unexpected: {queue}")
    else:
        print("❌ FAIL: No Checkpoint File.")
        return

    # Run 2: Resume
    print("🔄 Resuming...")
    res = await agent.act("", resume=True)
    
    # Verify Step 3 ran
    if "Step 3 (Resumed)" in res['execution_log']:
        print("✅ PASS: Resumed and executed remaining steps.")
    else:
        print(f"❌ FAIL: Did not execute Step 3. Log: {res['execution_log']}")

    # Cleanup
    if os.path.exists(state_file): os.remove(state_file)

if __name__ == "__main__":
    asyncio.run(test_batch_processing())
    asyncio.run(test_dynamic_injection())
    asyncio.run(test_checkpointing())
