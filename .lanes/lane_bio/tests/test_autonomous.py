import asyncio
import unittest
from unittest.mock import MagicMock, AsyncMock
from core.graph_orchestrator import GraphOrchestrator
from config import ModelTier

class TestAutonomousAgent(unittest.TestCase):
    def setUp(self):
        # 1. Mock Dependencies
        self.mock_llm = MagicMock()
        self.mock_llm.chat = AsyncMock(return_value="```python\nprint('Test')\n```")
        
        self.mock_ssh = MagicMock()
        self.mock_ssh.config = {"host": "test_host"} # Simulate Remote Configured
        self.mock_ssh.execute_command = AsyncMock(return_value={"exit_code": 0, "stdout": "Accuracy: 0.99", "stderr": ""})
        self.mock_ssh.execute = self.mock_ssh.execute_command # Alias for Provider Interface
        self.mock_ssh.pull_directory = AsyncMock()
        
        self.mock_search = MagicMock()
        self.mock_search.search_literature_async = AsyncMock(return_value=[{"title": "Test Paper", "url": "http://test"}])

        self.mock_env = MagicMock()
        self.mock_env.wrap_command = MagicMock(return_value="python3 -c 'print(1)'")

        self.mock_wandb = MagicMock()
        self.mock_data = MagicMock()
        self.mock_data.get_data_path.return_value = "/tmp/test_data"
        
        # 2. Instantiate Orchestrator with Mocks
        self.orchestrator = GraphOrchestrator(
            model_client=self.mock_llm,
            search_client=self.mock_search,
            ssh_executor=self.mock_ssh,
            env_manager=self.mock_env,
            wandb_observer=self.mock_wandb,
            data_manager=self.mock_data
        )

    def test_full_cycle(self):
        """
        Runs one full cycle of the graph (Grounding -> ... -> Paper)
        verifying that Mocks are called correctly.
        """
        async def run_test():
            # Run cycle (Phase 1: Until Human Review Interrupt)
            inputs = {"topic": "Test Topic"}
            config = {"configurable": {"thread_id": "test_1"}}
            
            print("[Test] Starting Phase 1...")
            async for output in self.orchestrator.app.astream(inputs, config=config):
                pass
            
            # Resume (Phase 2: Post-Review)
            print("[Test] Resuming Phase 2 (Human Feedback)...")
            self.orchestrator.app.update_state(config, {"human_feedback": "Proceed"})
            async for output in self.orchestrator.app.astream(None, config=config):
                pass
                
            # Assertions
            # 1. Verify Idea Generation called LLM
            self.mock_llm.chat.assert_called()
            
            # 2. Verify Experimentation called SSH
            self.mock_ssh.execute_command.assert_called()
            
            # 3. Verify Result Pull
            self.mock_ssh.download_results.assert_called()

        loop = asyncio.new_event_loop()
        loop.run_until_complete(run_test())
        loop.close()
        print("✅ Graph Cycle Test Passed")

if __name__ == "__main__":
    unittest.main()
