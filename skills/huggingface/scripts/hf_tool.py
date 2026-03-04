import argparse
from huggingface_hub import snapshot_download, hf_hub_download
import os

def download_model(repo_id):
    print(f"Downloading model: {repo_id}...")
    try:
        path = snapshot_download(repo_id=repo_id)
        print(f"Successfully downloaded to: {path}")
    except Exception as e:
        print(f"Error downloading model: {e}")

def download_dataset(repo_id, filename=None, repo_type="dataset"):
    print(f"Downloading dataset: {repo_id}...")
    try:
        if filename:
             path = hf_hub_download(repo_id=repo_id, filename=filename, repo_type=repo_type)
             print(f"Successfully downloaded file to: {path}")
        else:
             path = snapshot_download(repo_id=repo_id, repo_type=repo_type)
             print(f"Successfully downloaded snapshot to: {path}")
    except Exception as e:
        print(f"Error downloading dataset: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Model
    model_parser = subparsers.add_parser("model")
    model_parser.add_argument("id", help="Model ID (e.g. 'bert-base-uncased')")
    
    # Dataset
    data_parser = subparsers.add_parser("dataset")
    data_parser.add_argument("id", help="Dataset ID (e.g. 'glue')")
    data_parser.add_argument("--file", help="Specific file to download")
    
    args = parser.parse_args()
    
    if args.command == "model":
        download_model(args.id)
    elif args.command == "dataset":
        download_dataset(args.id, args.file)
