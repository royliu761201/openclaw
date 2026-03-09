from src.skills.project_archivist import ProjectArchivist
from src.core.config_manager import ConfigManager
import os

# Initialize
config_mgr = ConfigManager()
# Manually construct config dict for verification since we know the path
config_dict = {
    "RESEARCH_VAULT_DIR": "/Users/roy-jd/Documents/ResearchBot/research_vault"
}
archivist = ProjectArchivist(config=config_dict)

# Target path (It's already in the library, so the skill should handle the "in-place" cleanup)
target_path = "/Users/roy-jd/Documents/ResearchBot/research_vault/library/papers/micro_to_macro_physics_informed_neural_constitutiv"

print(f"Running Archivist Deep Cleanup on: {target_path}")

# We call archive_project. Since it's already in the library, it should detect that, 
# skip the move, and proceed to cleanup and registration.
log = archivist.archive_project(
    source_path=target_path,
    category="AI Blast", 
    status="Polished", 
    notes="Needs Experiments (Verified)"
)

print("--- Archivist Log ---")
print(log)
