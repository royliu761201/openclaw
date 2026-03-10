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
    # The Filtered Vacuum: Only whitelisted extensions are allowed into the permanent vault.
    # No media, no giant logs, no temp bins.
    ALLOWED_EXTS = ('.md', '.json', '.py', '.sh', '.txt')
    
    try:
        if os.path.exists(src_dir):
            for root, dirs, files in os.walk(src_dir):
                for file in files:
                    if file.endswith(ALLOWED_EXTS):
                        src_path = os.path.join(root, file)
                        # We flatten the structure to just keep the core artifacts in one folder
                        dest_path = os.path.join(dest_dir, file)
                        shutil.copy2(src_path, dest_path)
                        copied += 1
            print(f"✅ 已物理归档至: {dest_dir} (共搬运 {copied} 个核心净件)")
            print(f"==========================================")
            print(f"🔒 您的金库提取凭证锚点为: {os.path.basename(dest_dir)}")
            print(f"==========================================")
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
    dest_base = os.path.join(home_dir, "workspace", "docs", "session_archives")
    
    # 核心改造：使用源脑目录（Brain UUID）的前 8 位作为该会话的固定 DNA，确保单次会话多次物理闭环能被互相溯源
    session_uuid = os.path.basename(os.path.normpath(src_dir))
    short_id = session_uuid[:8] if len(session_uuid) >= 8 else str(uuid.uuid4())[:8]
    
    # 去重清理：扫荡该会话之前产生的旧版快照 (保留最后一份的策略)
    if os.path.exists(dest_base):
        for d in os.listdir(dest_base):
            if d.startswith("session_") and d.endswith(f"_{short_id}"):
                old_path = os.path.join(dest_base, d)
                if os.path.isdir(old_path):
                    shutil.rmtree(old_path)
                    print(f"🧹 自动瘦身：已清理该会话的过时过期快照 [{d}]")
                    
    # 生成带最新时间戳的新快照目录
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    folder_name = f"session_{timestamp}_{short_id}"
    
    dest_dir = os.path.join(dest_base, folder_name)
    
    print(f"开始强制抽取会话兵营: {src_dir}")
    print(f"目标永久冻结金库: {dest_dir}")
    
    copy_artifacts(src_dir, dest_dir)

if __name__ == "__main__":
    main()
