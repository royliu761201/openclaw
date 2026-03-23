#!/usr/bin/env python3
import os
import sys
import socket
import argparse
import logging
import shutil
import urllib.request
import urllib.error
import time
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("OmniFetch")

def check_dns(domain):
    try:
        ip = socket.gethostbyname(domain)
        if ip == "127.0.0.1":
            logger.error(f"DNS Blackhole detected for {domain} (resolves to 127.0.0.1).")
            return False
        logger.info(f"DNS Check: {domain} -> {ip} (OK)")
        return True
    except socket.gaierror:
        logger.error(f"DNS Check Failed: {domain} is unreachable.")
        return False

def check_disk_space(target_dir, required_bytes):
    try:
        stat = shutil.disk_usage(target_dir)
        free_space = stat.free
        if free_space < required_bytes * 1.2:
            logger.error(f"Disk check failed: Need {required_bytes*1.2/1e9:.2f}GB but only {free_space/1e9:.2f}GB free.")
            return False
        logger.info(f"Disk check OK: {free_space/1e9:.2f}GB available in {target_dir}.")
        return True
    except Exception as e:
        logger.warning(f"Could not verify disk space: {e}")
        return True # Soft pass if path not totally accessible yet

def check_proxy_poison():
    # Detect if harmful dead proxies are set in the environment
    proxies = [os.environ.get('http_proxy'), os.environ.get('https_proxy')]
    for p in proxies:
        if p and "127.0.0.1" in p:
            logger.error(f"Proxy Poison detected: {p} is set in environment, which will blackhole downloads.")
            return False
    return True

def preflight(source_domain, dest_dir, required_bytes):
    logger.info("=== 🛫 Starting Omni-Fetch Pre-flight ===")
    
    if not check_proxy_poison():
        return False
        
    if not check_dns(source_domain):
        return False
        
    # Create dir if not exists to check space
    Path(dest_dir).mkdir(parents=True, exist_ok=True)
    if not check_disk_space(dest_dir, required_bytes):
        return False
        
    logger.info("=== 🛫 Pre-flight Passed. Go for Launch. ===")
    return True

def resilient_download(url, dest_path, headers=None, max_retries=10):
    """A resilient downloader implementing automatic HTTP Range resuming."""
    import requests
    headers = headers or {}
    dest_path = Path(dest_path)
    
    # Fake browser user-agent to bypass basic anti-bots (e.g. Zenodo)
    if 'User-Agent' not in headers:
        headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

    for attempt in range(max_retries):
        temp_path = Path(str(dest_path) + ".download")
        downloaded = 0
        if temp_path.exists():
            downloaded = temp_path.stat().st_size
            headers['Range'] = f'bytes={downloaded}-'
            logger.info(f"[Attempt {attempt+1}] Resuming download from {downloaded} bytes...")
            mode = 'ab'
        else:
            logger.info(f"[Attempt {attempt+1}] Starting fresh download...")
            mode = 'wb'
            
        try:
            with requests.get(url, headers=headers, stream=True, timeout=30) as r:
                # If range is rejected and it returns 200 instead of 206, we must restart
                if r.status_code == 416: # Range Not Satisfiable (likely fully downloaded)
                    logger.info("Server reported requested range not satisfiable. Assuming complete.")
                    shutil.move(temp_path, dest_path)
                    return True
                    
                if downloaded > 0 and r.status_code != 206:
                    logger.warning("Server ignored Range request. Restarting from byte 0.")
                    downloaded = 0
                    mode = 'wb'
                
                r.raise_for_status()
                total_size = int(r.headers.get('content-length', 0)) + downloaded
                
                with open(temp_path, mode) as f:
                    start_time = time.time()
                    for chunk in r.iter_content(chunk_size=8192*4):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            # Basic progress log every 2 seconds
                            if time.time() - start_time > 5.0:
                                pct = (downloaded / total_size * 100) if total_size > 0 else 0
                                logger.info(f"Progress: {downloaded/1e6:.1f} MB / {total_size/1e6:.1f} MB ({pct:.1f}%)")
                                start_time = time.time()
                
            # If download completes without exception
            shutil.move(temp_path, dest_path)
            logger.info(f"✅ Download complete: {dest_path}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Download stream broken: {e}. Retrying in 5 seconds...")
            time.sleep(5)
            
    logger.error(f"❌ Download failed after {max_retries} attempts.")
    return False

def hf_pull(repo_id, filename, dest_dir):
    """HuggingFace resilient pull utilizing hf-mirror automatically."""
    logger.info(f"Targeting HuggingFace: {repo_id}/{filename}")
    os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
    
    # Preflight Check (HuggingFace Mirror)
    if not preflight('hf-mirror.com', dest_dir, 1024*1024*10): 
        sys.exit(1)
        
    try:
        from huggingface_hub import hf_hub_download, snapshot_download
        token = os.environ.get("HF_TOKEN")
        logger.info(f"Authenticating with token: {'YES' if token else 'NO'}")
        
        for attempt in range(20):
            try:
                # [OVERRIDE]: 支持全家桶级的快照并发下载
                if filename.lower() == "all" or not filename:
                    logger.info("Initializing multi-threaded Snapshot Download for full repository...")
                    path = snapshot_download(
                        repo_id=repo_id,
                        local_dir=dest_dir,
                        repo_type="dataset" if "dataset" in dest_dir.lower() or "pdb" in dest_dir.lower() else "model",
                        token=token,
                        resume_download=True,
                        max_workers=16
                    )
                else:
                    path = hf_hub_download(
                        repo_id=repo_id,
                        filename=filename,
                        local_dir=dest_dir,
                        repo_type="dataset" if "dataset" in dest_dir.lower() else "model",
                        token=token,
                        resume_download=True
                    )
                logger.info(f"✅ HF Pull Success. Data landed safely at: {path}")
                return
            except Exception as e:
                logger.error(f"[Attempt {attempt+1}] HF Pull Interrupted or Ratelimited: {e}. Cooldown 15s...")
                time.sleep(15)
        logger.error("❌ HF Pull Failed permanently after 20 resilient retries.")
        sys.exit(1)
    except ImportError:
        logger.error("huggingface_hub package is missing. Install with: pip install huggingface_hub")
        sys.exit(1)

def raw_pull(url, dest_file):
    """Generic raw pull for Zenodo or other direct web resources."""
    domain = urllib.parse.urlparse(url).netloc
    dest_path = Path(dest_file)
    
    # Provide a rough file size estimate for pre-flight if unknown (default 50GB)
    if not preflight(domain, dest_path.parent, 50 * 1024 * 1024 * 1024):
        sys.exit(1)
        
    success = resilient_download(url, dest_path)
    if not success:
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Omni-Fetch: The ultimate resilient data retriever.")
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    # HuggingFace Subcommand
    parser_hf = subparsers.add_parser('hf', help='Pull from HuggingFace Hub')
    parser_hf.add_argument('repo', help='Repository ID (e.g. lxh5147/atm22-cache)')
    parser_hf.add_argument('filename', help='File to pull (e.g. part1)')
    parser_hf.add_argument('outdir', help='Output directory')
    parser_hf.add_argument('--token', help='HF Token (bypasses env variables)')
    
    # Raw Subcommand
    parser_raw = subparsers.add_parser('raw', help='Pull from raw URL (Zenodo/S3/Kaggle Direct)')
    parser_raw.add_argument('url', help='Direct download URL')
    parser_raw.add_argument('outfile', help='Output file path')
    
    args = parser.parse_args()
    
    if args.command == 'hf':
        if args.token:
            os.environ['HF_TOKEN'] = args.token
        hf_pull(args.repo, args.filename, args.outdir)
    elif args.command == 'raw':
        raw_pull(args.url, args.outfile)

if __name__ == "__main__":
    main()
