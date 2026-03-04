#!/usr/bin/env python3
import argparse
import os
from dotenv import load_dotenv

# Load env vars BEFORE importing kaggle
load_dotenv()

import json
import shutil
import time
from kaggle.api.kaggle_api_extended import KaggleApi

def get_api():
    api = KaggleApi()
    api.authenticate()
    return api

def create_dataset(args):
    api = get_api()
    path = args.path
    is_zip = args.zip
    msg = args.message
    
    if is_zip and not path.endswith('.zip'):
        # If path is a folder and zip is requested, make archive
        print(f"Zipping {path}...")
        # shutil.make_archive base_name is without extension
        # If path is 'foo/bar', make_archive('foo/bar', 'zip', 'foo/bar') -> 'foo/bar.zip'
        # But we want to control where it goes? 
        # For simplicity, let's assume path provided IS the folder to upload.
        # Kaggle API handles zipping if dir_mode='zip'.
        pass

    print(f"Creating/Updating dataset from {path}...")
    try:
        # Check if exists (by metadata.json in folder)
        meta_path = os.path.join(path, "dataset-metadata.json")
        if not os.path.exists(meta_path):
            print(f"Error: {meta_path} not found. Please create metadata first.")
            return

        with open(meta_path, 'r') as f:
            meta = json.load(f)
            ref = meta.get('id')
            
        # Try update first (most common)
        try:
            api.dataset_create_version(path, msg, dir_mode='zip' if is_zip else 'skip', quiet=False)
            print("Dataset version created.")
        except Exception:
            # Fallback to create
            print("Update failed, trying create_new...")
            api.dataset_create_new(path, dir_mode='zip' if is_zip else 'skip', quiet=False)
            print("Dataset created.")
            
    except Exception as e:
        print(f"Error: {e}")

def push_kernel(args):
    api = get_api()
    path = args.path
    
    print(f"Pushing kernel from {path}...")
    try:
        # Check metadata
        meta_path = os.path.join(path, "kernel-metadata.json")
        if not os.path.exists(meta_path):
             print(f"Error: {meta_path} not found.")
             return
             
        api.kernels_push(path)
        print(f"Kernel pushed successfully.")
        
    except Exception as e:
        print(f"Error: {e}")

def list_kernels(args):
    api = get_api()
    search = args.search
    user = args.user
    
    if user:
        print(f"Listing kernels for user {user} search '{search}'...")
        kernels = api.kernels_list(user=user, search=search, sort_by='dateRun')
    else:
        print(f"Listing MY kernels search '{search}'...")
        kernels = api.kernels_list(mine=True, search=search, sort_by='dateRun')
        
    for k in kernels:
        print(f"Ref: {k.ref}, LastRun: {getattr(k, 'lastRunTime', 'N/A')}")

def get_kernel_output(args):
    api = get_api()
    slug = args.slug
    path = args.path
    
    print(f"Downloading output for {slug} to {path}...")
    try:
        # 1. Check status for failure message
        print(f"Checking status for {slug}...")
        statuses = api.kernels_status(slug) 
        # API returns object or dict? kernels_status usually returns KernelStatus object
        # It might be 'status' and 'failureMessage'
        if hasattr(statuses, 'status'):
            print(f"Status: {statuses.status}")
        if hasattr(statuses, 'failureMessage') and statuses.failureMessage:
            print(f"FAILURE MESSAGE: {statuses.failureMessage}")

        # 2. Download logs
        api.kernels_output(slug, path)
        print("Output downloaded.")
        
        # 3. Stream logs to console
        print("--- LOG CONTENTS ---")
        for root, dirs, files in os.walk(path):
            for f in files:
                if f.endswith(".log") or f.endswith(".txt") or f == "main.py.log":
                    full = os.path.join(root, f)
                    print(f"\n[Reading {f}]")
                    try:
                        with open(full, 'r', encoding='utf-8', errors='replace') as lf:
                            content = lf.read()
                            if len(content) > 10000:
                                print(content[-10000:]) # Tail last 10k chars
                                print(f"<... truncated start of {len(content)} bytes ...>")
                            else:
                                print(content)
                    except Exception as e:
                        print(f"Could not read {f}: {e}")
        print("--------------------")

    except Exception as e:
        print(f"Error: {e}")

def main():
    parser = argparse.ArgumentParser(description="OpenClaw Kaggle Tool")
    subparsers = parser.add_subparsers(dest="command")
    
    # Dataset
    d_parser = subparsers.add_parser("dataset_push")
    d_parser.add_argument("path", help="Folder containing dataset and metadata")
    d_parser.add_argument("-m", "--message", default="Updated via OpenClaw", help="Commit message")
    d_parser.add_argument("-z", "--zip", action="store_true", help="Upload as zip")
    
    # Kernel
    k_parser = subparsers.add_parser("kernel_push")
    k_parser.add_argument("path", help="Folder containing kernel and metadata")
    
    # List
    l_parser = subparsers.add_parser("kernels_list")
    l_parser.add_argument("--user", help="Kaggle username")
    l_parser.add_argument("--search", default="", help="Search term")
    
    # Output
    o_parser = subparsers.add_parser("kernels_output")
    o_parser.add_argument("slug", help="Kernel slug (e.g. user/my-kernel)")
    o_parser.add_argument("path", help="Download path")

    args = parser.parse_args()
    
    if args.command == "dataset_push":
        create_dataset(args)
    elif args.command == "kernel_push":
        push_kernel(args)
    elif args.command == "kernels_list":
        list_kernels(args)
    elif args.command == "kernels_output":
        get_kernel_output(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
