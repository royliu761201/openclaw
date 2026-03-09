import asyncio
import sys
import os

# Ensure src is in path
sys.path.append(os.path.join(os.getcwd(), "src"))

from skills.code_executor import CodeExecutor

async def main():
    print("=== Testing CodeExecutor (Local) ===")
    executor = CodeExecutor(timeout=3)
    
    # Test 1: Hello World
    print("\n1. Running 'Hello World'...")
    code1 = "print('Hello from Subprocess!')"
    res1 = await executor.execute_python(code1)
    print(f"Result: {res1}")
    
    # Test 2: Timeout
    print("\n2. Running Infinite Loop (should timeout)...")
    code2 = "import time; time.sleep(5); print('Should not see this')"
    res2 = await executor.execute_python(code2)
    print(f"Result: {res2}")
    
    # Test 3: Standard Error
    print("\n3. Running Syntax Error...")
    code3 = "print('Missing paren"
    res3 = await executor.execute_python(code3)
    print(f"Result: {res3}")

if __name__ == "__main__":
    asyncio.run(main())
