#!/usr/bin/env python3
import os
import re
import sys
import argparse
import urllib.parse
import fcntl
import time

def with_file_lock(filepath, mode, callback):
    """
    Executes a read/write callback while holding an exclusive OS-level file lock.
    This absolutely prevents microsecond I/O concurrency corruption across agents.
    """
    with open(filepath, mode, encoding='utf-8') as f:
        print(f"🔒 正在获取大盘 I/O 物理锁 ({filepath})...")
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            return callback(f)
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)
            print("🔓 大盘物理锁已释放。")

def resolve_markdown_links(content, base_dir):
    def replacer(match):
        text = match.group(1)
        url = match.group(2)
        if url.startswith("http://") or url.startswith("https://") or url.startswith("file://") or url.startswith("/"):
            return match.group(0)
        unquoted_url = urllib.parse.unquote(url)
        abs_path = os.path.normpath(os.path.join(base_dir, unquoted_url))
        encoded_path = urllib.parse.quote(abs_path)
        return f"[{text}](file://{encoded_path})"
    return re.sub(r'\[(.*?)\]\((.*?)\)', replacer, content)

def extract_section(content, keyword):
    """
    Finds the block related to the keyword, INCLUDING any > [!Whiteboard] blocks that follow it.
    """
    lines = content.split('\n')
    extracted = []
    in_section = False
    base_indent = 0
    
    for line in lines:
        if keyword.lower() in line.lower() and re.match(r'^\s*[-*+]\s+', line):
            in_section = True
            base_indent = len(line) - len(line.lstrip())
            extracted.append(line)
            continue
            
        if in_section:
            current_indent = len(line) - len(line.lstrip())
            if line.strip() != "" and not line.startswith(" ") and not line.startswith("\t") and current_indent <= base_indent:
                break
            extracted.append(line)
            
    return '\n'.join(extracted)

def get_checkbox_items(content):
    """Returns a dict mapping clean task text to its status"""
    items = {}
    pattern = re.compile(r'^\s*[-*+]\s+\[(.+?)\]\s+(.*)$')
    for line in content.split('\n'):
        m = pattern.match(line)
        if m:
            status = m.group(1).lower().strip()
            text = m.group(2).strip()
            items[text] = status
    return items

def do_checkout(global_path, session_path, keyword):
    if not os.path.exists(global_path):
        print(f"❌ 错误：未找到全局大盘文件 {global_path}")
        return
        
    def _read_board(f):
        return f.read()
        
    content = with_file_lock(global_path, 'r', _read_board)
        
    base_dir = os.path.dirname(os.path.abspath(global_path))
    content = resolve_markdown_links(content, base_dir)
    
    section = extract_section(content, keyword)
    if not section.strip():
        print(f"❌ 错误：在大盘中未找到匹配关键词 '{keyword}' 的任务区块。")
        return
        
    os.makedirs(os.path.dirname(session_path), exist_ok=True)
    
    header = f"<!-- GLOBAL_TASK_SYNC: {keyword} -->\n"
    header += f"# Active Task: {keyword}\n\n"
    
    with open(session_path, 'w', encoding='utf-8') as f:
        f.write(header + section)
        
    print(f"✅ 成功检出任务区块 '{keyword}' 至本地 {session_path}")

def do_commit(global_path, session_path):
    if not os.path.exists(session_path):
        print(f"❌ 错误：未找到本地任务会话文件 {session_path}")
        return
        
    with open(session_path, 'r', encoding='utf-8') as f:
        local_content = f.read()
        
    m = re.search(r'<!-- GLOBAL_TASK_SYNC:\s*(.*?)\s*-->', local_content)
    if not m:
        print("❌ 错误：在 task.md 中未找到 GLOBAL_TASK_SYNC 元数据，拒绝盲目提交通步。")
        return
    keyword = m.group(1)
    
    local_items = get_checkbox_items(local_content)
    
    def _commit_logic(f):
        global_lines = f.read().split('\n')
        modified = False
        in_section = False
        base_indent = 0
        new_global_lines = []
        
        for line in global_lines:
            if keyword.lower() in line.lower() and re.match(r'^\s*[-*+]\s+', line):
                in_section = True
                base_indent = len(line) - len(line.lstrip())
                
            if in_section:
                current_indent = len(line) - len(line.lstrip())
                # FIX: If the line doesn't start with whitespace and it isn't an empty line, or it's a new header, break section
                # But allowing > for blockquotes (Whiteboard)
                if line.strip() != "" and not line.startswith(" ") and not line.startswith("\t") and not line.startswith(">") and current_indent <= base_indent and keyword.lower() not in line.lower():
                    in_section = False
                    
            if in_section:
                match = re.match(r'^(\s*[-*+]\s+)\[(.+?)\](\s+)(.*)$', line)
                if match:
                    prefix = match.group(1)
                    curr_status = match.group(2).lower().strip()
                    space = match.group(3)
                    text = match.group(4).strip()
                    
                    if text in local_items and local_items[text] == 'x' and curr_status != 'x':
                        line = f"{prefix}[x]{space}{text}"
                        modified = True
                        print(f"✅ 已在全局大盘标记完成: {text}")
                        
            new_global_lines.append(line)
            
        if modified:
            # We rewrite the whole file, but under the same lock, we must seek to 0 and truncate
            f.seek(0)
            f.truncate()
            f.write('\n'.join(new_global_lines))
            print(f"✅ 已成功将 '{keyword}' 的本地进展同步到全局大盘。")
        else:
            print(f"⚠️ 全局大盘中 '{keyword}' 无需任何进展更新（本地无新打勾项）。")

    with_file_lock(global_path, 'r+', _commit_logic)

def do_create(global_path, task_text, category):
    def _create_logic(f):
        lines = f.read().split('\n')
        target_idx = -1
        for i, line in enumerate(lines):
            if category.lower() in line.lower() and line.startswith("##"):
                target_idx = i
                break
                
        if target_idx == -1:
            lines.append(f"- [ ] {task_text}")
        else:
            lines.insert(target_idx + 1, f"- [ ] {task_text}")
            
        f.seek(0)
        f.truncate()
        f.write('\n'.join(lines))
        print(f"✅ 已在全局大盘的 '{category}' 分类下新建任务：'{task_text}'")

    with_file_lock(global_path, 'r+', _create_logic)

def do_board_write(global_path, keyword, message):
    def _write_logic(f):
        lines = f.read().split('\n')
        in_section = False
        base_indent = 0
        target_idx = -1
        has_whiteboard = False
        
        for i, line in enumerate(lines):
            if keyword.lower() in line.lower() and re.match(r'^\s*[-*+]\s+', line):
                in_section = True
                base_indent = len(line) - len(line.lstrip())
                target_idx = i  # Mark the start, we will append at the very bottom of this block
                continue
                
            if in_section:
                current_indent = len(line) - len(line.lstrip())
                if "> [!Whiteboard]" in line:
                    has_whiteboard = True
                # Break if new sibling or parent block
                if line.strip() != "" and not line.startswith(" ") and not line.startswith("\t") and not line.startswith(">") and current_indent <= base_indent:
                    break
                target_idx = i
                
        if target_idx == -1:
            print(f"❌ 错误：未找到任务 '{keyword}'，无法写入白板。")
            return
            
        if not has_whiteboard:
            # Inject the whiteboard header
            lines.insert(target_idx + 1, f"    > [!Whiteboard] 跨会话共享内存区")
            lines.insert(target_idx + 2, f"    > - {message}")
        else:
            # Append to existing whiteboard
            lines.insert(target_idx + 1, f"    > - {message}")
            
        f.seek(0)
        f.truncate()
        f.write('\n'.join(lines))
        print(f"✅ 已将共享记忆写入 '{keyword}' 的白板区块。")

    with_file_lock(global_path, 'r+', _write_logic)

def do_board_clear(global_path, keyword):
    def _clear_logic(f):
        lines = f.read().split('\n')
        in_section = False
        base_indent = 0
        new_lines = []
        cleared = 0
        
        for line in lines:
            if keyword.lower() in line.lower() and re.match(r'^\s*[-*+]\s+', line):
                in_section = True
                base_indent = len(line) - len(line.lstrip())
                new_lines.append(line)
                continue
                
            if in_section:
                current_indent = len(line) - len(line.lstrip())
                if line.strip() != "" and not line.startswith(" ") and not line.startswith("\t") and not line.startswith(">") and current_indent <= base_indent:
                    in_section = False
                    
            if in_section and line.strip().startswith(">"):
                cleared += 1
                continue # Skip adding whiteboard lines
                
            new_lines.append(line)
            
        f.seek(0)
        f.truncate()
        f.write('\n'.join(new_lines))
        print(f"🗑️ 已清空 '{keyword}' 的白板内存区 (移除了 {cleared} 行)。")

    with_file_lock(global_path, 'r+', _clear_logic)

def main():
    parser = argparse.ArgumentParser(description="Two-way Global Task Sync")
    parser.add_argument("--global_board", required=True, help="Path to 01_GLOBAL_TASK_BOARD.md")
    parser.add_argument("--session_task", required=False, default="", help="Path to the session task.md (auto-detected if blank)")
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--checkout", type=str, help="Keyword of the task to isolate into current session")
    group.add_argument("--commit", action="store_true", help="Sync completed items back to the parent task")
    group.add_argument("--create", type=str, help="Task description to add to global board")
    group.add_argument("--board-write", nargs=2, metavar=('KEYWORD', 'MESSAGE'), help="Write a message to the Cross-Session Whiteboard block of a task")
    group.add_argument("--board-clear", type=str, metavar='KEYWORD', help="Clear the Cross-Session Whiteboard block of a task")
    
    parser.add_argument("--category", type=str, default="Permanent Assistant", help="Category/Heading to place new task under")
    
    args = parser.parse_args()
    
    session_task = args.session_task
    if not session_task or session_task.startswith("$") or "BRAIN_DIR" in session_task:
        import glob
        brain_base = os.path.expanduser("~/.gemini/antigravity/brain")
        try:
            latest_brain = max(glob.glob(os.path.join(brain_base, "*/")), key=os.path.getmtime)
            session_task = os.path.join(latest_brain, "task.md")
            print(f"🧠 自动探测到当前活跃的会话兵营: {session_task}")
        except Exception:
            session_task = "/tmp/dummy_task_sync.md"

    if args.checkout:
        do_checkout(args.global_board, session_task, args.checkout)
    elif args.commit:
        do_commit(args.global_board, session_task)
    elif args.create:
        do_create(args.global_board, args.create, args.category)
    elif args.board_write:
        do_board_write(args.global_board, args.board_write[0], args.board_write[1])
    elif args.board_clear:
        do_board_clear(args.global_board, args.board_clear)

if __name__ == "__main__":
    main()
