import os
import asyncio
from typing import List, Optional, Dict
from .base_skill import BaseSkill
from .git_ops import core_ops, branch_ops, sync_ops

class GitExecutor(BaseSkill):
    """
    The 'Time-Space Management Engine' for the Autonomous Scientist.
    Manages:
    1. Hierarchical Branching (main -> idea/xxx -> task/xxx)
    2. Atomic Commits with Structured Messages
    3. Experiment Linking (Tags)
    
    Refactored to delegate to atomic `git_ops`.
    """

    def __init__(self, repo_path: str = ".", config: Optional[Dict] = None):
        super().__init__(config)
        self.repo_path = os.path.abspath(repo_path)
        self.repo = core_ops.init_repo(self.repo_path)

    def verify(self) -> bool:
        """Check if git is installed and repo is valid."""
        if not core_ops.check_git_installed():
            return False
            
        # Ensure hygiene
        core_ops.ensure_gitignore(self.repo)
        return True

    async def ensure_clean_state(self):
        """Stashes changes if dirty to allow switching."""
        await asyncio.to_thread(core_ops.stash_changes, self.repo)

    async def checkout_idea_branch(self, idea_id: str):
        """
        Creates (if needed) and checks out 'idea/{idea_id}'.
        """
        await self.ensure_clean_state()
        await asyncio.to_thread(
            branch_ops.checkout_branch, 
            self.repo, 
            f"idea/{idea_id}", 
            base_branch="main"
        )

    async def checkout_task_branch(self, idea_id: str, task_name: str):
        """
        Creates a temporary task branch 'task/{idea_id}/{task_name}'
        """
        await self.ensure_clean_state()
        
        def _task_checkout():
            # Ensure we are on idea branch first (logic specific to executor flow)
            idea_branch = f"idea/{idea_id}"
            if str(self.repo.active_branch) != idea_branch:
                 branch_ops.checkout_branch(self.repo, idea_branch)
            
            branch_ops.checkout_branch(self.repo, f"task/{idea_id}/{task_name}", base_branch=idea_branch)
            
        await asyncio.to_thread(_task_checkout)

    async def atom_commit(self, agent_role: str, action: str, details: str, files: List[str] = None):
        """
        Performs an atomic commit with a structured message.
        """
        return await asyncio.to_thread(
            sync_ops.atomic_commit, 
            self.repo, action, details, agent_role, files
        )

    async def tag_experiment(self, idea_id: str, run_id: str, metrics: Dict[str, float]):
        """
        Tags a successful experiment commit.
        """
        await asyncio.to_thread(
            sync_ops.create_tag, 
            self.repo, 
            f"exp_{idea_id}_{run_id}", 
            str(metrics)
        )

    async def get_history_for_reflection(self, limit: int = 20) -> str:
        """
        Returns the git log for the current branch.
        """
        return await asyncio.to_thread(
            lambda: self.repo.git.log("--pretty=format:%h - %s (%cr)", f"-n {limit}")
        )

    async def save_state_snapshot(self, state_data: Dict, idea_id: str):
        """
        Saves research_state.json and commits it.
        """
        # ... (IO Logic remains high level) ...
        # Ideally IO should be in a FileOps, but simple save is fine here for now.
        import json
        state_path = f".agent/ideas/{idea_id}/state.json"
        os.makedirs(os.path.dirname(state_path), exist_ok=True)
        with open(state_path, "w") as f:
            json.dump(state_data, f, indent=2)
        
        await self.atom_commit("SYSTEM", "SNAPSHOT", f"Update state for {idea_id}", [state_path])

    async def checkout_grant_branch(self, grant_id: str):
        """Creates (if needed) and checks out 'grant/{grant_id}'."""
        await self.ensure_clean_state()
        await asyncio.to_thread(branch_ops.checkout_branch, self.repo, f"grant/{grant_id}")

    async def merge_and_tag(self, source_branch: str, tag_name: str, message: str):
        """Merges source_branch into main and creates a tag."""
        await self.ensure_clean_state()
        
        def _merge():
            sync_ops.merge_branch(self.repo, source_branch, "main", message)
            sync_ops.create_tag(self.repo, tag_name, message)
            
        await asyncio.to_thread(_merge)

    async def setup_worktree(self, lane_id: str, branch_name: str) -> str:
        """Sets up a git worktree for a specific lane."""
        return await asyncio.to_thread(branch_ops.create_worktree, self.repo, lane_id, branch_name)

