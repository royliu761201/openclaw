#!/usr/bin/env python3
"""
chunked_sync.py: The MTU-Bypass File Synchronizer for Node 02

This script transmits local files to Node 02 while actively bypassing Tailscale MTU blackhole restrictions (where large TCP packets are dropped silently). 
It works by compressing the payload, converting it to base64, and chunking it into smaller strings (e.g., 500 bytes) sent individually over a standard SSH text pipe, followed by destination reconstruction.

Usage:
  python3 scripts/chunked_sync.py <local_path> <remote_path> [--reload]
"""

import sys
import subprocess
import base64
import os
import argparse

def main():
    parser = argparse.ArgumentParser(description="Tailscale MTU-Bypass SSH Uploader")
    parser.add_argument("local_path", help="Absolute path to the local file to send")
    parser.add_argument("remote_path", help="Absolute path on Node 02 to write the file")
    parser.add_argument("--reload", action="store_true", help="Trigger a pm2 reload on dandan-mac02 after successful upload")
    
    args = parser.parse_args()

    # 1. Verification
    if not os.path.exists(args.local_path):
        print(f"❌ Error: Local file not found: {args.local_path}")
        sys.exit(1)
        
    print(f"📡 [MTU-Bypass] Initializing chunked transfer to Node 02...")
    print(f"📦 Source: {args.local_path}")
    print(f"🎯 Target: {args.remote_path}")

    with open(args.local_path, 'rb') as f:
        file_bytes = f.read()

    # Base64 encode the binary data to make it printable text
    b64_content = base64.b64encode(file_bytes).decode('utf-8')
    total_len = len(b64_content)
    chunk_size = 500
    
    # Calculate remote directory and ensure it exists, resolve ~ remotely
    remote_dir_cmd = f"dirname '{args.remote_path}'"
    
    # Pre-flight: create dir and scorch the remote b64 temp file
    temp_remote = f"{args.remote_path}.b64"
    init_cmd = f"mkdir -p $({remote_dir_cmd}) && rm -f {temp_remote} {args.remote_path} && touch {temp_remote}"
    subprocess.run(["ssh", "02", f"/bin/bash -c \"{init_cmd}\""], check=True)

    # Transmission loop
    print(f"🚀 Transmitting {total_len} bytes in {total_len // chunk_size + 1} chunks...")
    for i in range(0, total_len, chunk_size):
        chunk = b64_content[i:i+chunk_size]
        result = subprocess.run(["ssh", "-o", "ConnectTimeout=5", "02", f"echo -n '{chunk}' >> {temp_remote}"])
        if result.returncode != 0:
             print(f"❌ Error: Failed to transmit chunk at offset {i}. The SSH tunnel may be completely dead.")
             sys.exit(1)
             
    # Reconstruction
    print(f"🛠️ Reconstructing {args.remote_path} on Node 02...")
    decode_cmd = f"base64 -D < {temp_remote} > {args.remote_path} && chmod 644 {args.remote_path} && rm -f {temp_remote}"
    result = subprocess.run(["ssh", "02", decode_cmd])
    
    if result.returncode != 0:
         print("❌ Error: Remote Base64 reconstruction failed.")
         sys.exit(1)
         
    print(f"✅ Success! File synchronized to {args.remote_path}")

    # Reload
    if args.reload:
         print("⚙️ Executing hot-reload on Node 02 PM2 Gateway...")
         reload_cmd = "source ~/.openclaw_env && source ~/.zshrc && pm2 reload dandan-mac02 --update-env"
         subprocess.run(["ssh", "02", reload_cmd])
         print("✅ Gateway reloaded.")

if __name__ == "__main__":
    main()
