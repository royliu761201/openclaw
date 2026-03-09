import os
import sys
from huggingface_hub import hf_hub_download
import time

print(f"🔍 Testing HuggingFace Connectivity from {os.uname().nodename}...")
print(f"   HF_ENDPOINT: {os.environ.get('HF_ENDPOINT', 'Not Set (Default)')}")
print(f"   HF_HOME:     {os.environ.get('HF_HOME', 'Not Set (Default)')}")

start_time = time.time()
try:
    # Try downloading a tiny file (config.json of bert-base-uncased)
    model_id = "bert-base-uncased"
    filename = "config.json"
    
    print(f"\n⏳ Attempting to download '{filename}' from '{model_id}'...")
    local_path = hf_hub_download(repo_id=model_id, filename=filename)
    
    duration = time.time() - start_time
    print(f"\n✅ Success! Downloaded in {duration:.2f}s")
    print(f"📍 Saved to: {local_path}")
    
    # Check if it really went to the right place
    if "/root/research_bot/models" in local_path:
        print("✅ Correctly saved in /root/research_bot/models")
    else:
        print(f"⚠️  Saved in unexpected location: {local_path}")
        
except Exception as e:
    print(f"\n❌ Failed: {str(e)}")
    sys.exit(1)
