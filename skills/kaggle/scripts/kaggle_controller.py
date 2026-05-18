#!/usr/bin/env python3
import os
import sys
import argparse
import subprocess
import json
from pathlib import Path

def print_err(msg):
    print(f"\\033[91m[FATAL] {msg}\\033[0m")
def print_ok(msg):
    print(f"\\033[92m[OK] {msg}\\033[0m")

def check_account_auth(account):
    """Ensure the physical kaggle.json exists for the specified account mapping."""
    # Assuming accounts are structured like ~/.config/kaggle_accounts/<account_name>
    target_dir = Path.home() / ".config" / "kaggle_accounts" / account
    if not target_dir.exists():
        target_dir = Path.home() / ".kaggle" # fallback to default if specific not available, but user needs to assure it's correct
        if account == "default":
             target_dir = Path.home() / ".kaggle"
        else:
            print_err(f"Account credentials for '{account}' not mapped in ~/.config/kaggle_accounts/{account}")
            sys.exit(1)
            
    key_file = target_dir / "kaggle.json"
    if not key_file.exists():
        print_err(f"Missing kaggle.json in {target_dir}. Cannot authorize.")
        sys.exit(1)
        
    os.environ["KAGGLE_CONFIG_DIR"] = str(target_dir)
    print_ok(f"Isolated credential context loaded for account: {account}")

def check_and_fix_metadata(kernel_path, hardware):
    """Enforce hardware metadata mapping."""
    meta_path = Path(kernel_path) / "kernel-metadata.json"
    if not meta_path.exists():
        print_err(f"Missing kernel-metadata.json in {kernel_path}.")
        sys.exit(1)

    with open(meta_path, 'r') as f:
        meta = json.load(f)

    # Validate against CAlaM/LLM blind uploads (if requesting 5CPU)
    if hardware == "5CPU":
        code_file = Path(kernel_path) / meta.get("code_file", "")
        if code_file.exists():
            content = code_file.read_text(encoding="utf-8")
            if "torch.nn" in content and "batch_size" in content:
                print(f"\\033[93m[WARNING] You requested 5CPU, but PyTorch code detected. Make sure you are not running deep learning on cheap CPU instances. This will freeze!\\033[0m")
        
        meta["accelerator"] = "None"
        print_ok("Hardware locked to 5-Core CPU (None).")
        
    elif hardware == "2P100":
        meta["accelerator"] = "GPU"
        print_ok("Hardware locked to Dual P100 (GPU).")
    else:
        print_err("Unknown hardware target. Use '5CPU' or '2P100'.")
        sys.exit(1)

    with open(meta_path, 'w') as f:
         json.dump(meta, f, indent=2)

def main():
    parser = argparse.ArgumentParser(description="Kaggle Dual-Account \u0026 Hardware Controller")
    parser.add_argument("command", choices=["push"], help="Command to execute")
    parser.add_argument("path", help="Path to the kernel directory")
    parser.add_argument("--account", required=True, help="Target Kaggle Account ID")
    parser.add_argument("--hardware", choices=["5CPU", "2P100"], required=True, help="Target Hardware Array")

    args = parser.parse_args()

    if args.command == "push":
        check_account_auth(args.account)
        check_and_fix_metadata(args.path, args.hardware)
        
        # Dispatch the push command using internal OS env
        env = os.environ.copy()
        user_bin = str(Path.home() / "Library/Python/3.9/bin")
        if user_bin not in env.get("PATH", ""):
            env["PATH"] = f"{user_bin}:{env.get('PATH', '')}"

        cmd = ["kaggle", "kernels", "push", "-p", args.path]
        print(f"\n🚀 Dispatching kernel to Kaggle Pipeline: {' '.join(cmd)}")
        try:
            subprocess.run(cmd, check=True, env=env)
            print_ok("Kernel Successfully dispatched. Monitor via kaggle kernels list.")
        except subprocess.CalledProcessError:
            print_err("Kaggle Kernel Push API failed.")
            sys.exit(1)

if __name__ == "__main__":
    main()
