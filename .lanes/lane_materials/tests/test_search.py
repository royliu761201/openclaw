import asyncio
import sys
import os

# Ensure src is in path
sys.path.append(os.path.join(os.getcwd(), "src"))

from skills.search_client import SearchClient

async def main():
    print("=== Testing Google Grounding SearchClient ===")
    try:
        client = SearchClient()
        
        query = "Transformer architecture attention mechanisms"
        print(f"Searching for: {query}")
        
        results = await client.search_literature_async(query, max_results=5)
        
        if not results:
            print("❌ No results found (Grounding might not have triggered or found refs).")
        else:
            print(f"✅ Found {len(results)} results:")
            for i, res in enumerate(results):
                print(f"\nResult {i+1}:")
                # print(f"  Title: {res['title']}") # Title might be None in some chunks
                print(f"  Title: {res.get('title', 'Unknown')}")
                print(f"  URL: {res['url']}")
    except Exception as e:
        print(f"Test Failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
