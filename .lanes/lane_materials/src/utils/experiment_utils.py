import os
import signal
import sys
import torch
import glob
from typing import Optional, Callable, Dict, Any

class GracefulKiller:
    """
    Captures SIGINT/SIGTERM to allow generic graceful exit logic.
    """
    kill_now = False
    
    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        self.kill_now = True
        print(f"[GracefulKiller] Received signal {signum}. Setting kill_now=True.")

def find_latest_checkpoint(ckpt_dir: str) -> Optional[str]:
    """
    Finds the latest checkpoint in a directory.
    Prioritizes 'last.pth', then 'latest.pth', then sorts by modification time.
    """
    if not os.path.exists(ckpt_dir):
        return None
        
    # Standard names
    for name in ["last.pth", "latest.pth", "last.ckpt"]:
        path = os.path.join(ckpt_dir, name)
        if os.path.exists(path):
            return path
            
    # Sort by time
    ckpts = glob.glob(os.path.join(ckpt_dir, "*.pth")) + glob.glob(os.path.join(ckpt_dir, "*.ckpt"))
    if not ckpts:
        return None
        
    return max(ckpts, key=os.path.getmtime)

def auto_resume(ckpt_dir: str):
    """
    Decorator for the main training loop or setup function.
    Automatically looks for a checkpoint and injects it into the function args
    if the function accepts a 'resume_from' argument.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Check if we should resume
            latest = find_latest_checkpoint(ckpt_dir)
            if latest:
                print(f"[AutoResume] Found checkpoint: {latest}")
                # Inject into kwargs if supported
                if 'resume_from' in func.__code__.co_varnames: # Simple check
                     kwargs['resume_from'] = latest
                # Or if it expects an args object with resume_from attribute
                elif len(args) > 0 and hasattr(args[0], 'resume_from'):
                     # This is a bit risky to modify args[0] in place, but common for argparse
                     print(f"[AutoResume] Setting args.resume_from = {latest}")
                     setattr(args[0], 'resume_from', latest)
            else:
                print("[AutoResume] No checkpoint found. Starting fresh.")
                
            return func(*args, **kwargs)
        return wrapper
    return decorator

def save_checkpoint(state: Dict[str, Any], output_dir: str, is_best: bool = False):
    """
    Saves checkpoint with atomic 'last.pth' overwrite and optional 'best.pth'.
    """
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, "checkpoint_temp.pth")
    torch.save(state, filename)
    
    # Atomic rename to last.pth
    last_path = os.path.join(output_dir, "last.pth")
    os.replace(filename, last_path)
    
    if is_best:
        import shutil
        best_path = os.path.join(output_dir, "best.pth")
        shutil.copyfile(last_path, best_path)
