#!/usr/bin/env python3
import argparse
import sys
import os
import subprocess
import logging
import urllib.request
import time

logging.basicConfig(level=logging.INFO, format="%(message)s", filename="fetch_worker.log")

def run_cmd(cmd):
    try:
        logging.info(f"Running: {cmd}")
        subprocess.run(cmd, shell=True, check=True, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        logging.error(f"Command failed: {e}")
        sys.exit(1)

def get_vault_dir(category):
    mapping = {
        "model": "models",
        "dataset": "datasets",
        "software": "binaries"
    }
    return f"~/data_vault/{mapping.get(category, 'models')}"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--filename", required=True)
    parser.add_argument("--category", required=True)
    parser.add_argument("--is-local", action="store_true")
    parser.add_argument("--remote-id", help="e.g. 05")
    parser.add_argument("--target-host")
    
    args = parser.parse_args()
    
    # OS Detection
    is_windows = os.name == 'nt'
    
    # 1. Download phase
    logging.info(f"Downloading {args.url} to {args.filename}")
    
    # Use curl with -C - (resume) as the universal cross-platform downloader (Windows 10+ includes curl.exe)
    if args.is_local:
        # On Node 03, prefer aria2c if available for multi-connection speed, fallback to curl
        # Check for aria2c availability
        use_aria2c = False
        try:
            subprocess.run(["aria2c", "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            use_aria2c = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            logging.info("aria2c not found or failed, falling back to curl.")

        try:
            # Pass DEVNULL to prevent the subprocess from crashing when it attempts to draw a progress bar in a fully detached background worker (no CONOUT$ handle available)
            if use_aria2c:
                cmd = ["aria2c", "-x", "16", "-s", "16", "-c", "-o", args.filename, "-d", ".", args.url]
                logging.info(f"Running aria2c: {' '.join(cmd)}")
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                cmd = ["curl" + (".exe" if is_windows else ""), "-L", "-C", "-", "-o", args.filename, args.url]
                logging.info(f"Running curl: {' '.join(cmd)}")
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            logging.info(f"✅ Success: {args.filename}")
        except subprocess.CalledProcessError as e:
            logging.error(f"Download failed: {e}")
            sys.exit(1)
    else:
        # Original logic for remote nodes (not Node 03)
        # ADD -s -S to completely silence the curl progress bar, preventing fatal IO crashes when running in a 100% detached WScript.Shell context with no console allocation.
        if is_windows:
            download_cmd = f"curl.exe -s -S -L -C - -o \"{args.filename}\" \"{args.url}\""
        else:
            download_cmd = f"curl -s -S -L -C - -o '{args.filename}' '{args.url}'"
        
        # Execute Download
        run_cmd(download_cmd)
    
    vault_base = get_vault_dir(args.category)
    
    # 2. Vault phase
    if args.is_local:
        # Already on Node 03, just move it to vault
        run_cmd(f"mkdir -p {vault_base}")
        run_cmd(f"mv '{args.filename}' {vault_base}/")
        logging.info("Moved to local vault.")
    else:
        # We are on a remote node (Windows, Mac, or Linux)
        # We need to SCP back to Node 03 using ssh_tool
        brain_host = "100.108.106.119" # Node 03
        brain_user = "roy-003"
        
        # C-Check: Verify download succeeded before pushing
        if not os.path.exists(args.filename):
            logging.error("❌ C-Check Failed: Download did not produce the local file. Aborting.")
            sys.exit(1)
        
        logging.info("Ensuring Vault Directory exists on Node 03...")
        # Use native ssh instead of ssh_tool for absolute dependency decoupling
        mkdir_cmd = f"ssh -o StrictHostKeyChecking=no {brain_user}@{brain_host} 'mkdir -p {vault_base}'"
        if is_windows:
            mkdir_cmd = f"ssh -o StrictHostKeyChecking=no {brain_user}@{brain_host} \"mkdir -p {vault_base}\""
        run_cmd(mkdir_cmd)
        
        logging.info("Pushing to Vault (Node 03) via native scp...")
        push_cmd = f"scp -o StrictHostKeyChecking=no \"{args.filename}\" {brain_user}@{brain_host}:\"{vault_base}/\""
        if not is_windows:
             push_cmd = f"scp -o StrictHostKeyChecking=no '{args.filename}' {brain_user}@{brain_host}:'{vault_base}/'"
        run_cmd(push_cmd)
        
        # 3. Cleanup phase
        logging.info("Cleaning up local edge cache...")
        if is_windows:
            run_cmd(f"del \"{args.filename}\"")
        else:
            run_cmd(f"rm -f '{args.filename}'")

    # 4. Target Delivery (if requested)
    if args.target_host and args.is_local:
        # Node 03 pushing to the final target
        logging.info(f"Delivering from Vault to Target: {args.target_host}")
        pass # To be implemented via ssh_tool trigger in the future

    logging.info("✅ Worker Job Completed Successfully.")
    
if __name__ == "__main__":
    main()
