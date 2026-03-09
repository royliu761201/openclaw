
import asyncio
import os
import sys
# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from skills.grant_writer import GrantWriter
from core.model_client import ModelClient
from skills.git_executor import GitExecutor

async def test_grant_writer():
    print("🧪 Starting GrantWriter Verification...")
    
    # Mock Clients
    model_client = ModelClient()
    git_manager = GitExecutor(repo_path=os.getcwd())
    
    writer = GrantWriter(model_client, git_manager, root_dir=os.getcwd())
    
    topic = "Test_Grant_AI4S"
    context = "We propose an Autonomous Scientist that runs 24/7."
    guidelines = "Budget Limit: 200万元. Duration: 3 years. Focus: Artificial Intelligence for Science."
    team_info = "PI: Dr. Roy, Expert in AI Agents. Lab has 100 H100 GPUs."
    
    # Run Draft
    try:
        path = await writer.draft_proposal(topic, context, guidelines, team_info)
        print(f"✅ Draft Successful. Path: {path}")
        
        # Verify Files
        sections = ["00_summary.tex", "01_background.tex", "budget.tex"]
        project_dir = os.path.join("grant_output", "Test_Grant_AI4S")
        
        for s in sections:
            p = os.path.join(project_dir, "sections", s)
            if os.path.exists(p):
                print(f"  - Found {s}")
            else:
                print(f"  ❌ Missing {s}")
                
    except Exception as e:
        print(f"❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_grant_writer())
