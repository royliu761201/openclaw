import sys
import os
import shutil
import time
from git import Repo

sys.path.append(os.path.join(os.getcwd(), "src"))

from skills.git_executor import GitExecutor

TEST_REPO = os.path.abspath("./test_grant_repo")

def setup_test_env():
    if os.path.exists(TEST_REPO):
        shutil.rmtree(TEST_REPO)
    os.makedirs(TEST_REPO)
    
    # Initialize GitExecutor with this new repo
    print(f"Initializing GitExecutor in {TEST_REPO}")
    gm = GitExecutor(TEST_REPO)
    return gm

def test_grant_lifecycle():
    print("\n--- Testing Grant Lifecycle ---")
    gm = setup_test_env()
    
    grant_id = "grant_demo_123"
    tag_name = f"v1.0-{grant_id}"
    
    # 1. Start Grant (Branching)
    print(f"1. Checkout Grant Branch: {grant_id}")
    gm.checkout_grant_branch(grant_id)
    
    assert gm.repo.active_branch.name == f"grant/{grant_id}"
    print("✅ Branch Verification Passed")
    
    # 2. Simulate Work (Commits)
    print("2. Simulating Draft Work...")
    draft_file = os.path.join(TEST_REPO, "draft.txt")
    with open(draft_file, "w") as f:
        f.write("This is a grant draft.")
    
    gm.atom_commit("GRANT_WRITER", "DRAFT", "Initial Draft", [draft_file])
    
    # Check log
    last_commit = gm.repo.head.commit.message
    print(f"   Last Commit: {last_commit}")
    assert "Initial Draft" in last_commit
    
    # 3. Finalize (Merge & Tag)
    print("3. Finalizing Grant (Merge & Tag)...")
    gm.merge_and_tag(f"grant/{grant_id}", tag_name, "Finalized Grant")
    
    # Verify Tag
    tags = [t.name for t in gm.repo.tags]
    print(f"   Tags: {tags}")
    assert tag_name in tags
    print("✅ Tag Verification Passed")
    
    # Verify Branch Switch (Back to Main)
    current_branch = gm.repo.active_branch.name
    print(f"   Current Branch: {current_branch}")
    assert current_branch == "main"
    print("✅ Merge & Return Verification Passed")
    
    # Cleanup
    # shutil.rmtree(TEST_REPO) 
    print("\n🎉 Grant Lifecycle Test Passed!")

if __name__ == "__main__":
    test_grant_lifecycle()
