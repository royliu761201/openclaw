import asyncio
import os
import shutil
import json
from skills.data_manager import DataManager
from skills.kaggle_executor import KaggleExecutor

async def test_data_manager_local():
    print("=== Testing DataManager (Local) ===")
    dm = DataManager(base_path=".")
    
    # Test 1: Ensure Dataset (Local Dummy)
    # We use a fake name "test_dataset_local"
    # We expect it to create a dummy if no URL
    path = await dm.ensure_dataset("test_dataset_local")
    print(f"Path returned: {path}")
    
    path = os.path.abspath(path)
    expected_path = os.path.join(os.getcwd(), "research_vault/library/datasets/test_dataset_local")
    if path == expected_path and os.path.exists(path):
        print("✅ Local Ensure Success")
    else:
        print(f"❌ Local Ensure Failed: {path}")

async def test_kaggle_executor():
    print("\n=== Testing KaggleExecutor (Metadata) ===")
    ke = KaggleExecutor()
    
    # Test 1: Push Notebook with Datasets
    # We will mock the subprocess call to avoid actual push, 
    # but we want to check the generated checking metadata file.
    # Actually, push_notebook generates files before pushing.
    # We can inspect the file.
    
    # But push_notebook cleans up? No it leaves .kaggle_builds
    try:
        # We start the coroutine but fail at subprocess (since no kaggle auth in test env maybe?)
        # Or we just catch the exception
        pass 
    except:
        pass

    # Let's manually invoke the logic part or just run it and catch error
    try:
        await ke.push_notebook(
            code="print('hello')",
            title="test_kernel_data",
            dataset_slugs=["user/data-slug", "user/other-slug"],
            verify_only=True
        )
    except Exception as e:
        print(f"Unexpected error: {e}")

    # Inspect the generated metadata
    # KaggleExecutor seems to strip underscores or use checking on title? 
    # The log said: Build created at .kaggle_builds/testkerneldata
    slug_dir = "testkerneldata" 
    meta_path = f".kaggle_builds/{slug_dir}/kernel-metadata.json"
    
    if os.path.exists(meta_path):
        with open(meta_path, 'r') as f:
            data = json.load(f)
            sources = data.get("dataset_sources")
            print(f"Generated Sources: {sources}")
            
            if "user/data-slug" in str(sources):
                 print("✅ Kaggle Metadata Injection Success")
            else:
                 print("❌ Kaggle Metadata Injection Failed: Sources mismatch")
    else:
        print(f"❌ Metadata file not found at {meta_path}")

    # Test Download (Mocked)
    print("\n=== Testing KaggleExecutor (Download Results) ===")
    try:
        # We assume verify_only doesn't apply to download (it runs CLI)
        # We can't really run it without a real kernel.
        # But we can check if the method exists.
        if hasattr(ke, "download_results"):
             print("✅ download_results method exists.")
    except Exception as e:
        print(f"❌ download_results check failed: {e}")

async def main():
    await test_data_manager_local()
    await test_kaggle_executor()

if __name__ == "__main__":
    asyncio.run(main())
