#!/usr/bin/env python3
import os
import sys
import base64
import subprocess
import argparse
import json

def get_kaggle_creds():
    # 1. Try environment variables
    user = os.getenv("KAGGLE_USERNAME")
    key = os.getenv("KAGGLE_KEY")
    if user and key:
        return user, key
    
    # 2. Try kaggle.json
    paths = ["~/.config/kaggle/kaggle.json", "~/.kaggle/kaggle.json"]
    for p in paths:
        full_p = os.path.expanduser(p)
        if os.path.exists(full_p):
            with open(full_p) as f:
                data = json.load(f)
                return data["username"], data["key"]
    
    return None, None

def main():
    parser = argparse.ArgumentParser(description="GPU-Server Safe Kaggle Downloader (DNS Bypass)")
    parser.add_argument("dataset", help="Dataset slug (e.g. owner/slug)")
    parser.add_argument("--output-dir", "-o", required=True, help="Destination directory")
    args = parser.parse_args()

    user, key = get_kaggle_creds()
    if not user or not key:
        print("Error: Kaggle credentials not found in env or kaggle.json")
        sys.exit(1)

    auth_token = base64.b64encode(f"{user}:{key}".encode()).decode()
    
    # Kaggle CDN IP fixed for 10.190.30.220 container DNS bypass
    KAGGLE_IP = "35.244.233.98"
    
    dataset_name = args.dataset.split("/")[-1]
    output_path = os.path.join(args.output_dir, f"{dataset_name}.zip")
    
    os.makedirs(args.output_dir, exist_ok=True)
    
    url = f"https://www.kaggle.com/api/v1/datasets/download/{args.dataset}"
    
    cmd = [
        "curl", "-L",
        "--resolve", f"www.kaggle.com:443:{KAGGLE_IP}",
        "-H", f"Authorization: Basic {auth_token}",
        "-C", "-",
        "-o", output_path,
        url
    ]
    
    print(f"Executing direct-IP download for: {args.dataset}")
    print(f"Target: {output_path}")
    
    try:
        subprocess.run(cmd, check=True)
        print("Download completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Download failed with exit code: {e.returncode}")
        sys.exit(1)

if __name__ == "__main__":
    main()
