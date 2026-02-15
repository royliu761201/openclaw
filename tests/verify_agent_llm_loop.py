
import requests
import json
import time

API_URL = "http://localhost:18789/v1/chat/completions"

def test_agent_loop():
    print("🧠 Starting Agent LLM Loop Verification...")
    
    # Complex prompt requiring multiple tools
    prompt = (
        "Please perform the following integration test:\n"
        "1. List my Kaggle kernels (user: xiaohualiu).\n"
        "2. Count how many kernels are found.\n"
        "3. Log that count to WandB project 'verification-test' with metric name 'agent_kernel_count'.\n"
        "4. Reply with the final count."
    )
    
    payload = {
        "model": "openclaw",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "stream": False
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer local-dev-token"
    }
    
    try:
        print(f"📡 Sending request to {API_URL}...")
        start_time = time.time()
        response = requests.post(API_URL, json=payload, headers=headers, timeout=120)
        duration = time.time() - start_time
        
        if response.status_code != 200:
            print(f"❌ Error: API returned {response.status_code}")
            print(response.text)
            return
            
        data = response.json()
        content = data['choices'][0]['message']['content']
        
        print("\n✅ Agent Response Received:")
        print("-" * 40)
        print(content)
        print("-" * 40)
        print(f"⏱️ Duration: {duration:.2f}s")
        
        # Simple heuristic verification
        if "Kaggle" in content or "kernels" in content:
            print("✅ Response mentions Kaggle context.")
        else:
            print("⚠️ Response might be missing Kaggle context.")
            
        if "WandB" in content or "logged" in content:
            print("✅ Response confirms WandB logging.")
        else:
            print("⚠️ Response might be missing WandB context.")

    except Exception as e:
        print(f"❌ Connection Failed: {e}")
        print("Is the Gateway running on port 18789?")

if __name__ == "__main__":
    # Wait a moment for Gateway to be fully ready if just started
    time.sleep(2)
    test_agent_loop()
