#!/usr/bin/env python3
import os
import re
import sys
import argparse
import urllib.parse

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
    Finds the block related to the keyword.
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
        
    with open(global_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
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
    
    with open(global_path, 'r', encoding='utf-8') as f:
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
            if line.strip() != "" and not line.startswith(" ") and not line.startswith("\t") and current_indent <= base_indent and keyword.lower() not in line.lower():
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
        with open(global_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_global_lines))
        print(f"✅ 已成功将 '{keyword}' 的本地进展同步到全局大盘。")
    else:
        print(f"⚠️ 全局大盘中 '{keyword}' 无需任何进展更新（本地无新打勾项）。")

def do_create(global_path, task_text, category):
    with open(global_path, 'r', encoding='utf-8') as f:
        lines = f.read().split('\n')
        
    target_idx = -1
    for i, line in enumerate(lines):
        if category.lower() in line.lower() and line.startswith("##"):
            target_idx = i
            break
            
    if target_idx == -1:
        # Just append at bottom if category not found
        lines.append(f"- [ ] {task_text}")
    else:
        # Insert after the header
        lines.insert(target_idx + 1, f"- [ ] {task_text}")
        
    with open(global_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f"✅ 已在全局大盘的 '{category}' 分类下新建任务：'{task_text}'")

def main():
    parser = argparse.ArgumentParser(description="Two-way Global Task Sync")
    parser.add_argument("--global_board", required=True, help="Path to 01_GLOBAL_TASK_BOARD.md")
    parser.add_argument("--session_task", required=False, default="", help="Path to the session task.md (auto-detected if blank)")
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--checkout", type=str, help="Keyword of the task to isolate into current session")
    group.add_argument("--commit", action="store_true", help="Sync completed items back to the parent task")
    group.add_argument("--create", type=str, help="Task description to add to global board")
    
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

if __name__ == "__main__":
    main()
