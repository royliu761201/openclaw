import asyncio
import os
import sys

# Add src to path
sys.path.append(os.path.abspath("src"))

from core.lab_manager import EnvManager, EnvironmentSpec
from core.experiment import ResilientRunner, ExperimentConfig, validationLevel

async def test_mock_lab():
    print("=== Testing Lab Manager (Mock Mode) ===")
    
    # 1. Init Manager
    lab = EnvManager(base_path="tests/envs")
    print(f"Binary detected: {lab.binary}")
    assert lab.binary == "mock"

    # 2. Create Spec
    spec = EnvironmentSpec(name="test_env_01", dependencies=["torch", "numpy"])
    await lab.create_env(spec)
    
    # Verify YAML created
    yaml_path = "tests/envs/test_env_01.yml"
    assert os.path.exists(yaml_path)
    print(f"YAML Spec created at {yaml_path}")
    
    # 3. Test Runner
    runner = ResilientRunner(lab)
    config = ExperimentConfig(
        idea_id="idea_test",
        task_id="task_001",
        cmd="python train.py",
        env_name="test_env_01",
        output_dir="tests/outputs/task_001",
        validation_level=validationLevel.T1_SMOKE
    )
    
    # Run T1 Smoke (Mock)
    success = await runner.run_experiment(config)
    assert success
    print("Experiment Run Successful (Mock)")

if __name__ == "__main__":
    asyncio.run(test_mock_lab())
