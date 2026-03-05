#!/usr/bin/env python3
import os
import glob
import subprocess

def find_latest_task_board():
    """
    Search natively for the latest task.md in either the rigid workspace docs
    or the current AI brain artifact directory.
    """
    # 废弃低效且极度耗时的全盘递归 glob (**/*)。
    # 改为定点扫描合法会话层，避免在大量日志产生严重的 IO 阻塞（即非常慢的原因）
    home_dir = os.path.expanduser("~")
    search_paths = [
        os.path.join(home_dir, "Documents/workspace/docs/system_core/node02_sessions/*/task.md"),
        os.path.join(home_dir, ".gemini/antigravity/brain/*/task.md")
    ]
    
    latest_file = None
    latest_time = 0
    
    for pattern in search_paths:
        try:
            for filepath in glob.iglob(pattern, recursive=True):
                if os.path.exists(filepath):
                    mtime = os.path.getmtime(filepath)
                    if mtime > latest_time:
                        latest_time = mtime
                        latest_file = filepath
        except Exception as e:
            pass # Ignore access errors gracefully
            
    if latest_file:
        print(f"✅ FOUND_LATEST_TASK_BOARD: {latest_file}")
        
        # [NEW] Execute the auto-updating skill indexer before handing over
        try:
            indexer_path = os.path.join(os.path.dirname(__file__), "generate_skill_index.py")
            subprocess.run(["python3", indexer_path], check=True, capture_output=True)
            skills_index = os.path.join(os.path.expanduser("~"), "Documents", "projects", "openclaw", "skills", "OPENCLAW_SKILLS_INDEX.md")
            print(f"✅ SKILL_MENU_READY: Agent MUST also `view_file {skills_index}` to understand available actions.")
        except Exception as e:
            print(f"⚠️ WARNING: Failed to update skill index: {e}")

        print(">> INSTRUCTION: Agent MUST now use `view_file` on the task board path above to recover its context.")
    else:
        print("❌ NO_TASK_BOARD_FOUND: The agent must rely on MASTER_INDEX or initialize a new project task board.")

if __name__ == "__main__":
    find_latest_task_board()
