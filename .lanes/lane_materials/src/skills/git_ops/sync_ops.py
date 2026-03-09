from typing import List, Dict
import json
from git import Repo

"""
Atomic Sync Operations (Commit, Tag, Merge).
"""

def atomic_commit(repo: Repo, action: str, details: str, role: str = "SYSTEM", files: List[str] = None) -> str:
    """Commits changes atomically."""
    if files:
        repo.index.add(files)
    else:
        repo.git.add(A=True)
        
    message = f"[{role.upper()}] {action}: {details}"
    # Check if anything to commit
    if not repo.index.diff("HEAD"):
        print("[GitOps] Nothing to commit.")
        return repo.head.commit.hexsha
        
    commit = repo.index.commit(message)
    print(f"[GitOps] Committed: {message} ({commit.hexsha[:7]})")
    return commit.hexsha

def create_tag(repo: Repo, tag_name: str, message: str):
    """Creates a lightweight tag."""
    print(f"[GitOps] Tagging {tag_name}")
    repo.create_tag(tag_name, message=message)

def merge_branch(repo: Repo, source_branch: str, target_branch: str = "main", message: str = ""):
    """Merges source into target."""
    if target_branch not in repo.heads:
        print(f"[GitOps] Error: Target '{target_branch}' not found.")
        return

    repo.heads[target_branch].checkout()
    
    try:
        msg = f"Merge {source_branch}: {message}"
        repo.git.merge(source_branch, "--no-ff", "-m", msg)
        print(f"[GitOps] Merged {source_branch} into {target_branch}")
    except Exception as e:
        print(f"[GitOps] Merge Conflict/Error: {e}. Aborting.")
        repo.git.merge("--abort")
