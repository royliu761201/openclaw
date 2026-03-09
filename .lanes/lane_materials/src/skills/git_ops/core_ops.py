import os
import subprocess
from typing import Optional, List
from git import Repo, InvalidGitRepositoryError, NoSuchPathError

"""
Atomic Core Git Operations.
Functional style, no state management.
"""

def init_repo(path: str) -> Repo:
    """Initialize or load a repo."""
    try:
        return Repo(path)
    except (InvalidGitRepositoryError, NoSuchPathError):
        print(f"[GitOps] Initializing new repo at {path}")
        os.makedirs(path, exist_ok=True)
        return Repo.init(path)

def check_git_installed() -> bool:
    try:
        subprocess.run(["git", "--version"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def ensure_gitignore(repo: Repo):
    """Ensures .gitignore and initial commit exist."""
    gitignore_path = os.path.join(repo.working_dir, ".gitignore")
    start_commit = False
    
    if not os.path.exists(gitignore_path):
        with open(gitignore_path, "w") as f:
            f.write("__pycache__/\n*.pyc\n.env\nwandb/\n")
        repo.index.add([gitignore_path])
        start_commit = True
        
    if not repo.heads:
        if not start_commit:
            # Create empty commit if no heads
            repo.index.commit("Initial commit (Empty)")
        else:
            repo.index.commit("Initial commit (.gitignore)")

def is_dirty(repo: Repo) -> bool:
    return repo.is_dirty(untracked_files=True)

def stash_changes(repo: Repo, message: str = "Auto-stash"):
    if is_dirty(repo):
        print(f"[GitOps] Stashing: {message}")
        repo.git.stash("save", message)
