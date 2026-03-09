import asyncio
import os
import sys
from google import genai
from google.genai import types

sys.path.append(os.path.join(os.getcwd(), "src"))
from core.model_client import ModelClient

async def test_grounding():
    print("=== Testing Google Search Grounding ===")
    try:
        # Re-use logic from ModelClient to load key
        client_wrapper = ModelClient()
        client = client_wrapper.client
        
        model_id = "gemini-3-flash-preview"
        print(f"Model: {model_id}")
        
        # Enable Google Search Tool
        google_search_tool = types.Tool(
            google_search=types.GoogleSearch()
        )
        
        response = await client.aio.models.generate_content(
            model=model_id,
            contents="What is the latest version of the Gemini model as of late 2024?",
            config=types.GenerateContentConfig(
                tools=[google_search_tool],
                response_modalities=["TEXT"]
            )
        )
        
        print("\nResponse:")
        print(response.text)
        
        if response.candidates[0].grounding_metadata:
             print("\n✅ Grounding Metadata found (Search worked!)")
             print(response.candidates[0].grounding_metadata)
        else:
             print("\n❌ No grounding metadata.")
             
    except Exception as e:
        print(f"\n❌ Grounding Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_grounding())
