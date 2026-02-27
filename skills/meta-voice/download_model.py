from huggingface_hub import snapshot_download
import sys
import os
import time

# Unset proxies within the python process
for key in ['http_proxy', 'https_proxy', 'all_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY']:
    if key in os.environ:
        del os.environ[key]

model_id = 'facebook/seamless-m4t-v2-large'
endpoint = 'https://hf-mirror.com'

print(f"Aggressive Download: {model_id} from {endpoint}...")

max_attempts = 10
for attempt in range(max_attempts):
    print(f"Attempt {attempt + 1}/{max_attempts}...")
    try:
        # snapshot_download is resume-aware by default
        snapshot_download(
            model_id, 
            endpoint=endpoint,
            max_workers=4,
            tqdm_class=None # Disable tqdm to avoid log bloating
        )
        print("✅ Download successful.")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Attempt {attempt + 1} failed: {e}")
        if attempt < max_attempts - 1:
            print("Waiting 10 seconds before retry...")
            time.sleep(10)
        else:
            print("💥 All attempts failed.")
            sys.exit(1)
