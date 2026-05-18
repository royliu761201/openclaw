#!/usr/bin/env python3
import os
import sys
import os
import sys
import subprocess

def download_file(url, target_path, target_dir, filename):
    print(f"⏳ Downloading from {url} via aria2c (16-threads)...")
    try:
        # Use aria2c for multi-threaded high-speed fetching (Standardized OpenClaw protocol)
        cmd = [
            "aria2c", 
            "-x", "16", 
            "-s", "16", 
            "--dir", target_dir,
            "--out", filename,
            url
        ]
        subprocess.run(cmd, check=True)
        print(f"✅ Successfully downloaded to {target_path}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to download {url} via aria2c. Please ensure aria2c is installed: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("❌ Error: 'aria2c' command not found. Please install it (e.g., brew install aria2c).")
        sys.exit(1)

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    models_dir = os.path.join(base_dir, "models")
    os.makedirs(models_dir, exist_ok=True)
    
    # Using ghproxy.net as it is the only stable resolving proxy on Node 01
    proxy_prefix = "https://ghproxy.net/"
    
    files_to_download = {
        "kokoro-v1.0.onnx": f"{proxy_prefix}https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx",
        "voices-v1.0.bin": f"{proxy_prefix}https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"
    }

    print(f"🎯 [Node 01 Fetcher] Setting up Local TTS Sandbox at {models_dir}")
    print(f"📥 Target: GitHub Releases via Proxy (Zero-Footprint V1.0)")
    
    for filename, url in files_to_download.items():
        target_path = os.path.join(models_dir, filename)
        if not os.path.exists(target_path) or os.path.exists(target_path + ".aria2"):
            # If it's partial (.aria2 exists) or missing, run aria2c to fetch/resume
            download_file(url, target_path, models_dir, filename)
        else:
            print(f"✅ {filename} already exists, skipping.")

    print("\n🎉 [Zero-Bloat Fetch Complete] Models securely isolated in local sandbox.")

if __name__ == "__main__":
    main()
