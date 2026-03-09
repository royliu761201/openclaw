
import asyncio
import os
import shutil
import json
from unittest.mock import MagicMock, AsyncMock
from skills.submission_manager import SubmissionManager
from core.model_client import ModelClient
from skills.search_client import SearchClient

async def run_test():
    print("🧪 Starting Verification: SubmissionManager (Updated)")
    
    # 1. Setup Environment
    root_dir = os.path.abspath(os.getcwd())
    template_root = os.path.join(root_dir, "research_vault/templates")
    kb_path = os.path.join(os.path.dirname(template_root), "knowledge_base/venues.yaml")
    
    print(f"   - Template Root: {template_root}")
    print(f"   - KB Path: {kb_path}")
    
    if not os.path.exists(kb_path):
        print(f"❌ critical: venues.yaml not found at {kb_path}")
        return

    # 2. Mock Clients
    mock_model = MagicMock(spec=ModelClient)
    # Mock suggestion response
    mock_model.chat = AsyncMock(return_value='[{"name": "NeurIPS", "reason": "Good fit"}]')
    
    mock_search = MagicMock(spec=SearchClient)
    mock_search.search_web = AsyncMock(return_value=[{"snippet": "Deadline is May 22, 2025"}])
    
    # 3. Initialize Skill
    manager = SubmissionManager(mock_model, mock_search, template_root)
    
    # 4. Test: Suggest Venues
    print("\n[Test 1] Suggest Venues")
    suggestions = await manager.suggest_venues("Deep Learning for Biology", "Abstract...")
    print(f"   - Suggestions: {suggestions}")
    if suggestions[0]['name'] == "NeurIPS" and suggestions[0]['tier'] == "CCF-A":
        print("   ✅ Suggestion Logic & KB Enrichment: PASS")
    else:
        print("   ❌ Suggestion Logic: FAIL")
        
    # 5. Test: Get Venue Details (NeurIPS - KB Hit)
    print("\n[Test 2] Get Details (NeurIPS - KB Hit)")
    details = await manager.get_venue_details("NeurIPS")
    print(f"   - Details: {details}")
    
    deadline_val = str(details.get('deadline_context', ''))
    if "2025" in deadline_val and details['tier'] == "CCF-A":
        print("   ✅ KB Retrieval (Deadline): PASS")
    else:
        print(f"   ❌ KB Retrieval (Deadline): FAIL - Got {deadline_val}")

    # 6. Test: Get Venue Details (Nature - Impact Factor Check)
    print("\n[Test 3] Get Details (Nature - Impact Factor & Structure)")
    details_nature = await manager.get_venue_details("Nature")
    print(f"   - Details: {details_nature}")
    if details_nature.get('impact_factor'):
        print(f"   ✅ Impact Factor Found: {details_nature['impact_factor']}")
    else:
        print("   ❌ Impact Factor Missing")
        
    if "appendix" in details_nature and "structure" in details_nature:
        print(f"   ✅ Structure Info Found: {len(details_nature['structure'])} sections defined")
    else:
        print("   ❌ Structure/Appendix Missing")

    # 7. Test: Prepare Workspace
    print("\n[Test 4] Prepare Workspace")
    test_output = "test_output_submission"
    if os.path.exists(test_output): shutil.rmtree(test_output)
    
    env_config = manager.prepare_workspace(details, test_output)
    
    if os.path.exists(os.path.join(test_output, "main.tex")):
        print("   ✅ main.tex created: PASS")
    else:
        print("   ❌ main.tex missing: FAIL")
        
    if template_root in env_config['TEXINPUTS']:
        print("   ✅ TEXINPUTS config: PASS")
    else:
        print("   ❌ TEXINPUTS config: FAIL")
        
    # Cleanup
    shutil.rmtree(test_output)
    print("\n🎉 Verification Complete.")

if __name__ == "__main__":
    asyncio.run(run_test())
