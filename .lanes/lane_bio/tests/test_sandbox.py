import sys
import os
import shutil
import asyncio
from unittest.mock import MagicMock

sys.path.append(os.path.join(os.getcwd(), "src"))
from skills.code_executor import CodeExecutor

TEST_DIR = os.path.abspath("./test_sandbox_env")

def setup_mock_venv():
    """Creates a mock .venv structure."""
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)
    os.makedirs(TEST_DIR)
    
    venv_bin = os.path.join(TEST_DIR, ".venv", "bin")
    os.makedirs(venv_bin)
    
    # Create a mock python executable (shell script)
    mock_python = os.path.join(venv_bin, "python")
    with open(mock_python, "w") as f:
        f.write("#!/bin/sh\n")
        f.write('echo "SANDBOXED_EXEC"\n')
    
    # Make executable
    os.chmod(mock_python, 0o755)
    return mock_python

async def test_sandbox_detection():
    print("Testing Sandbox Detection...")
    mock_python_path = setup_mock_venv()
    print(f"Created Mock Python at: {mock_python_path}")
    
    executor = CodeExecutor(work_dir=TEST_DIR)
    
    # We expect the stdout to contain "SANDBOXED_EXEC" because our mock python prints it
    # regardless of input code (since it's a dummy shell script ignoring args)
    result = await executor.execute_python("print('hello')")
    
    print(f"Result: {result}")
    
    if "SANDBOXED_EXEC" in result['stdout']:
        print("✅ Success: CodeExecutor used the Sandbox Python.")
    else:
        print(f"❌ Failure: CodeExecutor used System Python (Stdout: {result['stdout']})")
        exit(1)

    # Cleanup
    shutil.rmtree(TEST_DIR)

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(test_sandbox_detection())
