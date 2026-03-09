
import asyncio
import os
import shutil
import json
from unittest.mock import MagicMock, AsyncMock
from core.graph_orchestrator import GraphOrchestrator, AgentState
from agents.paper_producer import PaperProducer
from agents.experiment_scientist import ExperimentScientist
from core.model_client import ModelClient

async def run_verification():
    print("🚀 Starting Integration Verification...")
    
    # 1. Setup Mock Environment
    test_dir = "./test_workspace"
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    os.makedirs(test_dir)
    
    # Mock Model Client (Crucial to avoid API calls)
    mock_client = MagicMock(spec=ModelClient)
    # Fix: SearchClient accesses .client, so we must mock it
    mock_client.client = MagicMock() 
    # Mock responses for different tasks
    # Mock responses list
    responses = [
        # --- PaperProducer ---
        # 1. Plan (Think)
        json.dumps({
            "strategy": "Dynamic Theory Draft",
            "steps": [
                {"id": "1", "action": "theory_plan_outline", "params": {}},
                {"id": "2", "action": "theory_scaffold", "params": {}},
                {"id": "3", "action": "theory_write_abstract", "params": {}},
                {"id": "4", "action": "theory_write_sections", "params": {}}
             ]
        }),
        # 2. Plan Outline (Chat)
        """
        # Outline for NeurIPS
        ## Introduction
        - Argument: Introduce the problem.
        ## Related Work
        - Argument: Discuss previous work.
        ## Method
        - Argument: Proposed solution.
        """,
        
        # 3. Write Abstract (Chat - Standard)
        json.dumps({"title": "Refined Test Paper", "abstract": "This is a refined abstract."}),
        
        # 4. Refine Title (Chat - Fast)
        "Refined Test Paper: A Study",

        # 5. Write Section: Introduction
        "## Introduction\nContent...",
        # 6. Write Section: Related Work
        "## Related Work\nContent...",
        # 7. Write Section: Method
        "## Method\nContent...",

        # --- ExperimentScientist ---
        # 8. Exp Plan (Think)
        json.dumps({
            "strategy": "Dynamic Experiment Plan",
            "steps": [
                {"id": "1", "action": "setup_environment_context", "params": {}},
                {"id": "2", "action": "generate_experiment_code", "params": {}}
            ]
        }),
        # 9. Exp Code (Chat)
        "```python\nprint('Hello World')\n```"
    ]
    
    # Add padding to avoid StopIteration
    responses.extend(["Generic Fallback Response"] * 10)

    mock_client.chat = AsyncMock(side_effect=responses)
    
    # Init Orchestrator
    orchestrator = GraphOrchestrator(root_dir=test_dir, model_client=mock_client)
    
    # --- TEST 1: PaperProducer Integration ---
    print("\n[Test 1] Verifying PaperProducer (Theory Draft)...")
    state_theory = {
        "idea": {
            "title": "Test Paper",
            "abstract": "This is a test.",
            "details": "Details here."
        },
        "venue": "TestVenue",
        "template": "neurips_2024.tex",
        "references": []
    }
    
    try:
        # Manually invoke the node logic (unit test style)
        result1 = await orchestrator.node_write_theory(state_theory)
        
        # Verify Output
        expected_dir = os.path.join(test_dir, "research_vault/papers/test_paper")
        if "output_dir" in result1 and result1["output_dir"] == expected_dir:
            print(f"✅ PaperProducer returned correct output dir: {expected_dir}")
        else:
            print(f"❌ PaperProducer Output Mismatch: {result1}")
            
        # Verify File Creation (The 'theory_write_abstract' step should have run)
        abstract_path = os.path.join(expected_dir, "sections/00_abstract.tex")
        if os.path.exists(abstract_path):
             print(f"✅ Abstract file created at: {abstract_path}")
        else:
             print(f"❌ Abstract file missing! (Did act() execute?)")

    except Exception as e:
        print(f"❌ Test 1 Failed: {e}")
        import traceback
        traceback.print_exc()

    # --- TEST 2: ExperimentScientist Integration ---
    print("\n[Test 2] Verifying ExperimentScientist...")
    state_exp = {
        "topic": "TestTopic",
        "idea": "TestIdea",
        "autonomous_mode": True
    }
    
    try:
        # Mocking the act method internals effectively is hard without running it.
        # But we mocked the PLAN above. 
        # The 'setup_environment_context' action needs to run.
        
        # We need to mock wandb inside ExperimentScientist or it will fail/try to connect
        orchestrator.experiment_scientist.wandb = MagicMock()
        orchestrator.experiment_scientist.wandb.init_run = MagicMock()
        
        result2 = await orchestrator.node_experimentation(state_exp)
        
        print(f"✅ Experiment Result Keys: {result2.keys()}")
        
        # Validate Side Effects (State)
        if hasattr(orchestrator.experiment_scientist, "exp_state"):
             print(f"✅ Experiment State Initialized: {orchestrator.experiment_scientist.exp_state['topic']}")
        else:
             print("❌ Experiment State Missing.")

    except Exception as e:
        print(f"❌ Test 2 Failed: {e}")
        import traceback
        traceback.print_exc()

    # Cleanup
    # shutil.rmtree(test_dir)
    print("\n🏁 Verification Complete.")

if __name__ == "__main__":
    asyncio.run(run_verification())
