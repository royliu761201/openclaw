import os
import re
from typing import Optional, Dict, Any
from .base_skill import BaseSkill

class ProjectManager(BaseSkill):
    """
    Skill for autonomous project lifecycle management.
    Capabilities:
    1. Create Project Structure (Vault Compliance).
    2. Register Project in Knowledge Map (Cortex Awareness).
    """
    def __init__(self, vault_root: str = "research_vault", config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.vault_root = os.path.abspath(vault_root)
        self.map_path = os.path.join(self.vault_root, ".agent_rules", "project_map.md")

    def verify(self) -> bool:
        """Checks if the vault root exists."""
        return os.path.isdir(self.config.get("vault_root", self.vault_root))

    def create_project(self, name: str, category: str = "Uncategorized", description: str = "") -> str:
        """
        Creates a new research project.
        
        Args:
            name (str): Project codename (e.g. "Active-Bidder").
            category (str): Category (e.g. "AI Safety", "Life Science").
            description (str): Short summary.
            
        Returns:
            str: Path to the new project.
        """
        # 1. Sanitize Name
        safe_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', name).lower()
        
        # 2. Create Directory Structure
        project_path = os.path.join(self.vault_root, "library", "papers", safe_name)
        
        folders = [
            "code",
            "code/src",
            "paper",
            "results",
            "data"  # For datasets & model checkpoints
        ]
        
        print(f"[ProjectManager] 🏗️ Scaffolding project: {name} at {project_path}")
        for f in folders:
            os.makedirs(os.path.join(project_path, f), exist_ok=True)
            
        # 3. Register in Map
        self._register_in_map(name, safe_name, category, description)
        
        # 4. Auto-Scaffold Paper (Using LatexArchitect)
        # Ensure imports here to avoid heavy deps on init
        try:
            from skills.latex_architect import LatexArchitect
            architect = LatexArchitect()
            paper_dir = os.path.join(project_path, "paper")
            architect.scaffold_paper(
                idea_id=safe_name,
                title=f"Research on {name}",
                output_dir=paper_dir, # Correct Subdir
                template_name="neurips_2024.tex"
            )
            print(f"[ProjectManager] 📄 Initialized Paper Draft in {paper_dir}")
        except Exception as e:
            print(f"[ProjectManager] ⚠️ Paper scaffold failed: {e}")

        return project_path

    def _register_in_map(self, name: str, safe_name: str, category: str, description: str):
        """Append to project_map.md"""
        if not os.path.exists(self.map_path):
            print(f"[ProjectManager] ⚠️ Map file not found at {self.map_path}")
            return

        with open(self.map_path, "r") as f:
            content = f.read()

        # Check if already exists
        if f"papers/{safe_name}" in content:
            print(f"[ProjectManager] Project {name} already registered.")
            return

        # Prepare Entry
        entry = f"- **{name}** (`papers/{safe_name}`): {description}. Status: Initialized.\n"

        # Find Category Header or Append to End
        # We look for "## [Category]" or just append to end if not found complex matching.
        # For robustness, we simply append a new section if category not found, or append to end.
        
        # Simple Logic: Append to end for now to avoid breaking file structure
        # (Ideal: Regex match category, but that's fragile without standardized headers)
        
        new_content = content + f"\n{entry}"
        
        with open(self.map_path, "w") as f:
            f.write(new_content)
            
        print(f"[ProjectManager] 📖 Registered {name} in Knowledge Map.")
