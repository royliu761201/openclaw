#!/usr/bin/env python3
import os
import sys
import shutil
import argparse
import datetime
import uuid

def copy_artifacts(src_dir, dest_dir):
    """
    Safely copies specific artifacts from the temporary brain directory
    into the rigid workspace directory.
    """
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir, exist_ok=True)
        
    copied = 0
    # Let's target the exact artifacts (.md, .json, .log, .txt) to avoid blindly 
    # copying everything including temp scratchpads, but since gems generate mostly 
    # .md files in the artifact dir, copying the whole dir except certain dirs is also an option.
    # To be totally safe and not lose anything, we'll try to just copy the whole directory recursively.
    
    try:
        if os.path.exists(src_dir):
            for item in os.listdir(src_dir):
                s = os.path.join(src_dir, item)
                d = os.path.join(dest_dir, item)
                if os.path.isdir(s):
                    shutil.copytree(s, d, dirs_exist_ok=True)
                else:
                    shutil.copy2(s, d)
                copied += 1
            print(f"✅ 已物理归档至: {dest_dir} (共搬运 {copied} 个部件)")
        else:
            print(f"❌ 错误：兵营源目录 {src_dir} 不存在，无法归档。")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ 归档致命错误 (FATAL_ARCHIVE_ERROR): {str(e)}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Archive the current session's brain to persistent storage.")
    parser.add_argument("--source", type=str, required=True, help="Absolute path to the current session's brain directory")
    args = parser.parse_args()
    
    src_dir = args.source
    home_dir = os.path.expanduser("~")
    
    # Generate timestamp and unique ID for the archive folder
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    short_id = str(uuid.uuid4())[:8]
    folder_name = f"session_{timestamp}_{short_id}"
    
    dest_dir = os.path.join(home_dir, "workspace", "docs", "session_archives", folder_name)
    
    print(f"开始强制抽取会话兵营: {src_dir}")
    print(f"目标永久冻结金库: {dest_dir}")
    
    copy_artifacts(src_dir, dest_dir)

if __name__ == "__main__":
    main()
