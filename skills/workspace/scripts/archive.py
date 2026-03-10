#!/usr/bin/env python3
import os
import sys
import shutil
import argparse
import datetime
import uuid
import subprocess
import json

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

def remediate_links(workspace_dir, old_brain_str, new_archive_str):
    """
    Scans the docs directory for any dead links pointing to the old volatile brain cache
    and rewrites them to point to the new permanent archive directory.
    """
    docs_dir = os.path.join(workspace_dir, "docs")
    modified_files = []
    
    if not os.path.exists(docs_dir):
        return modified_files
        
    for root, _, files in os.walk(docs_dir):
        for file in files:
            if file.endswith('.md'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    if old_brain_str in content:
                        new_content = content.replace(old_brain_str, new_archive_str)
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        modified_files.append(file_path)
                except Exception as e:
                    print(f"⚠️ 无法扫描文件 {file_path}: {e}")
                    
    return modified_files


def main():
    parser = argparse.ArgumentParser(description="Archive the current session's brain to persistent storage.")
    parser.add_argument("--source", type=str, required=True, help="Absolute path to the current session's brain directory")
    parser.add_argument("--push", action="store_true", help="Push to git remote after archiving")
    parser.add_argument("--no-sync", action="store_true", help="Skip global board synchronization")
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
    
    # 1. Generate Metadata Manifest
    manifest_path = os.path.join(dest_dir, "manifest.json")
    manifest = {
        "session_uuid": session_uuid,
        "short_id": short_id,
        "timestamp": timestamp,
        "source_dir": src_dir,
        "archived_dir": dest_dir
    }
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=4)
        
    print(f"📄 已生成元数据: {manifest_path}")

    # 2. Integrate with sync_global.py
    task_md = os.path.join(dest_dir, "task.md")
    workspace_dir = os.path.join(home_dir, "workspace")
    global_board = os.path.join(workspace_dir, "docs", "system_core", "memory_core", "01_GLOBAL_TASK_BOARD.md")
    
    synced = False
    if not args.no_sync and os.path.exists(task_md):
        with open(task_md, "r") as f:
            content = f.read()
            if "GLOBAL_TASK_SYNC" in content:
                print(f"🔄 检测到 GLOBAL_TASK_SYNC，正在触发大盘同步...")
                sync_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sync_global.py")
                if os.path.exists(sync_script):
                    try:
                        subprocess.run([sys.executable, sync_script, "--global_board", global_board, "--session_task", task_md, "--commit"], check=True)
                        synced = True
                    except subprocess.CalledProcessError as e:
                        print(f"⚠️ 大盘同步失败: {e}")
                else:
                    print(f"⚠️ 未找到 sync_global.py 脚本。")

    # 3. Link Remediation Loop (Kill Dead Links)
    old_brain_path = src_dir
    # Handle the fact that markdown links might be prefixed with file://
    old_brain_uri = f"file://{src_dir}"
    new_archive_uri = f"file://{dest_dir}"
    
    print(f"🔍 正在执行 SSoT 死链扫描与修正 (Link Remediation)...")
    rem_files = remediate_links(workspace_dir, old_brain_uri, new_archive_uri)
    rem_files_raw = remediate_links(workspace_dir, old_brain_path, dest_dir)
    all_remediated = list(set(rem_files + rem_files_raw))
    
    if all_remediated:
        print(f"🔗 成功修复了以下文件中的死链:")
        for rf in all_remediated:
            print(f"   - {rf}")
    else:
        print(f"✅ 全局大盘未发现指向此会话老地址的死链。")

    # 4. Git Operations Loop
    print(f"📦 正在执行 Git 全链路闭环...")
    try:
        subprocess.run(["git", "add", dest_dir], cwd=workspace_dir, check=True)
        if synced:
            subprocess.run(["git", "add", global_board], cwd=workspace_dir, check=True)
            
        for rf in all_remediated:
            subprocess.run(["git", "add", rf], cwd=workspace_dir, check=True)
            
        status = subprocess.run(["git", "status", "--porcelain"], cwd=workspace_dir, capture_output=True, text=True)
        if not status.stdout.strip():
            print(f"🛑 当前会话无新变更，已跳过 Git Commit。")
        else:
            commit_msg = f"Auto-archive session {short_id} with Link Remediation"
            subprocess.run(["git", "commit", "-m", commit_msg], cwd=workspace_dir, check=True)
            print(f"✅ Git Commit 成功: {commit_msg}")
            
            if args.push:
                print(f"🚀 正在推送到远程仓库...")
                subprocess.run(["git", "push"], cwd=workspace_dir, check=True)
                print(f"✅ Git Push 成功！")
    except subprocess.CalledProcessError as e:
        print(f"❌ Git 操作失败: {e}")

if __name__ == "__main__":
    main()
