import os
from git import Repo

"""
Atomic Branch & Worktree Operations.
"""

def checkout_branch(repo: Repo, branch_name: str, base_branch: str = "main"):
    """Check out a branch, creating it if necessary from base."""
    # Ensure base exists if repo is new
    if 'main' not in repo.heads and 'master' in repo.heads:
         repo.heads.master.rename('main')
    
    if branch_name in repo.heads:
        print(f"[GitOps] Switching to existing branch: {branch_name}")
        repo.heads[branch_name].checkout()
    else:
        print(f"[GitOps] Creating new branch: {branch_name} from {base_branch}")
        if base_branch in repo.heads:
            repo.heads[base_branch].checkout()
        new_branch = repo.create_head(branch_name)
        new_branch.checkout()

def create_worktree(repo: Repo, lane_id: str, branch_name: str) -> str:
    """Setup a worktree for concurrent operations."""
    worktree_path = os.path.abspath(os.path.join(repo.working_dir, ".lanes", lane_id))
    
    if os.path.exists(worktree_path):
         print(f"[GitOps] Worktree exists at {worktree_path}")
         return worktree_path
         
    print(f"[GitOps] Creating Worktree for {lane_id} -> {branch_name}")
    
    # Ensure branch exists before worktree add
    if branch_name not in repo.heads:
        if 'main' in repo.heads:
            repo.git.branch(branch_name, "main")
        else:
            # If main doesn't exist, create orphan or from current
            repo.git.branch(branch_name)
            
    try:
        repo.git.worktree("add", "-f", worktree_path, branch_name)
    except Exception as e:
        print(f"[GitOps] Worktree add failed (pruning): {e}")
        repo.git.worktree("prune")
        repo.git.worktree("add", "-f", worktree_path, branch_name)
        
    return worktree_path
