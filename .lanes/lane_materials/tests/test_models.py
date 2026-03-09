import asyncio
import os
import sys
# Ensure src is in path
sys.path.append(os.path.join(os.getcwd(), "src"))

from core.model_client import ModelClient

async def test_model_connectivity(client, model_id, alias):
    print(f"\n--- Testing {alias} ({model_id}) ---")
    try:
        # Use the client's internal validation logic (v2 SDK)
        response = await client.client.aio.models.generate_content(
            model=model_id,
            contents="Hello, are you online? Reply with 'Yes'."
        )
        print(f"✅ Success: {response.text.strip()}")
        return True
    except Exception as e:
        print(f"❌ Failed: {str(e)}")
        if "401" in str(e) or "Unauthenticated" in str(e):
             print("   -> Auth Error. Key might be invalid or model requires distinct OAuth.")
        return False

async def main():
    print("=== Gemini Model Connectivity Suite (V2 SDK) ===")
    
    try:
        client = ModelClient()
        print(f"Client Initialized. Key prefix: {client.api_key[:4]}...")
        
        # List available models to debug ID issues
        print("\n--- Available Models ---")
        try:
            # Pager object, iterate to get models
            async for model in await client.client.aio.models.list():
                # print(f" - {model.name} (Display: {model.display_name})")
                # Filter for gemini to reduce noise
                if "gemini" in model.name:
                     print(f" - {model.name.split('/')[-1]}")
        except Exception as e:
            print(f"Error listing models: {e}")
            
    except Exception as e:
        print(f"Critical: Client init failed - {e}")
        return

    # List of models to test (trying specific Vertex AI versions)
    models_to_test = [
        ("Gemini 1.5 Flash (Alias)", "gemini-1.5-flash"),
        ("Gemini 1.5 Flash 001", "gemini-1.5-flash-001"),
        ("Gemini 1.5 Flash 002", "gemini-1.5-flash-002"),
        ("Gemini 2.0 Flash Exp", "gemini-2.0-flash-exp"),
        ("Gemini 3 Flash Preview", "gemini-3-flash-preview"), 
        ("Gemini 2.5 Flash Lite", "gemini-2.5-flash-lite"),
    ]
    
    results = {}
    for alias, model_id in models_to_test:
        results[alias] = await test_model_connectivity(client, model_id, alias)
        
    print("\n=== Summary ===")
    for alias, success in results.items():
        print(f"{alias}: {'PASS' if success else 'FAIL'}")

if __name__ == "__main__":
    asyncio.run(main())
