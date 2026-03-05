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
    workspace_dir = os.environ.get("WORKSPACE_DIR", os.path.join(home_dir, "Documents", "workspace"))
    search_paths = [
        # 1. 优先扫描当前 Antigravity 会话的默认存储核心区
        os.path.join(home_dir, ".gemini/antigravity/brain/*/task.md"),
        # 2. 备选扫描 SSoT 沉淀的各节点会话备份池（灵活适配当前 Node）
        os.path.join(workspace_dir, "docs/system_core/node*_sessions/*/task.md")
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
        


        print(">> INSTRUCTION: Agent MUST now use `view_file` on the task board path above to recover its context.")
    else:
        print("❌ NO_TASK_BOARD_FOUND: The agent must rely on MASTER_INDEX or initialize a new project task board.")

if __name__ == "__main__":
    find_latest_task_board()
