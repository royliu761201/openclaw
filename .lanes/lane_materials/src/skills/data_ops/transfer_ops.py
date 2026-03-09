import os
import urllib.request
import zipfile
import tarfile
import shutil
import tempfile
from typing import Optional

"""
Atomic Data Transfer Operations.
Pure functions for downloading and extracting data.
"""

def download_file(url: str, output_path: str) -> bool:
    """Standard file download."""
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        urllib.request.urlretrieve(url, output_path)
        return True
    except Exception as e:
        print(f"[transfer_ops] Download failed: {e}")
        return False

def download_and_extract(url: str, target_dir: str) -> bool:
    """Downloads archive and extracts to target_dir."""
    try:
        with tempfile.TemporaryDirectory() as temp:
            filename = "download.tmp"
            dl_path = os.path.join(temp, filename)
            
            print(f"[transfer_ops] Downloading from {url}...")
            urllib.request.urlretrieve(url, dl_path)
            
            os.makedirs(target_dir, exist_ok=True)
            
            if url.endswith(".zip"):
                with zipfile.ZipFile(dl_path, 'r') as zip_ref:
                    zip_ref.extractall(target_dir)
            elif url.endswith(".tar.gz") or url.endswith(".tgz"):
                with tarfile.open(dl_path, "r:gz") as tar:
                    tar.extractall(target_dir)
            else:
                # Fallback: Move single file
                fname = url.split("/")[-1] or "data.bin"
                shutil.move(dl_path, os.path.join(target_dir, fname))
                
            return True
    except Exception as e:
        print(f"[transfer_ops] Extract failed: {e}")
        return False

def create_dummy_dataset(target_dir: str, filename: str = "dummy.csv", content: str = "id,value\n0,0.0"):
    """Creates a dummy dataset for testing."""
    os.makedirs(target_dir, exist_ok=True)
    with open(os.path.join(target_dir, filename), "w") as f:
        f.write(content)
