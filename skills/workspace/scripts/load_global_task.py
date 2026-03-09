import os
import re
import sys
import argparse
import urllib.parse

def resolve_markdown_links(content, base_dir):
    # Regex to catch Markdown links: [text](url)
    def replacer(match):
        text = match.group(1)
        url = match.group(2)
        
        # Skip external http/https or already absolute file:// links
        if url.startswith("http://") or url.startswith("https://") or url.startswith("file://") or url.startswith("/"):
            return match.group(0)
            
        # Optional: handle URL decoding if there are spaces (%20)
        unquoted_url = urllib.parse.unquote(url)
        
        # Resolve the absolute path
        abs_path = os.path.normpath(os.path.join(base_dir, unquoted_url))
        
        # Convert spaces to %20 to be safe for URI
        encoded_path = urllib.parse.quote(abs_path)
        
        return f"[{text}](file://{encoded_path})"

    # Pattern explanation: \[([^\]]+)\]\(([^)]+)\)
    # Group 1: Link text
    # Group 2: URL
    return re.sub(r'\[(.*?)\]\((.*?)\)', replacer, content)

def main():
    parser = argparse.ArgumentParser(description="Load Global Task Board into Session task.md with absolute links.")
    parser.add_argument("--global_board", required=True, help="Path to 01_GLOBAL_TASK_BOARD.md")
    parser.add_argument("--session_task", required=False, default="", help="Path to the session task.md (auto-detected if blank)")
    args = parser.parse_args()

    session_task = args.session_task
    # Auto-detect the current Antigravity brain directory if omitted or literally passed as a raw bash variable
    if not session_task or session_task.startswith("$") or "BRAIN_DIR" in session_task:
        import glob
        brain_base = os.path.expanduser("~/.gemini/antigravity/brain")
        try:
            # Find the most recently modified directory in the brain folder
            latest_brain = max(glob.glob(os.path.join(brain_base, "*/")), key=os.path.getmtime)
            session_task = os.path.join(latest_brain, "task.md")
            print(f"🧠 Auto-detected active session brain: {session_task}")
        except Exception as e:
            print(f"Error auto-detecting brain dir: {e}")
            sys.exit(1)

    if not os.path.exists(args.global_board):
        print(f"Error: Global board not found at {args.global_board}")
        sys.exit(1)

    with open(args.global_board, 'r', encoding='utf-8') as f:
        content = f.read()

    base_dir = os.path.dirname(os.path.abspath(args.global_board))
    resolved_content = resolve_markdown_links(content, base_dir)

    # Normalize list items with checkboxes to strictly use '- [ ]' or '- [x]'
    # This prevents UI bugs where '* [ ]' fails to render as a task.
    resolved_content = re.sub(r'^\s*[*+]\s+\[( |x|/)\]', lambda m: m.group(0).replace(m.group(0).strip()[0], '-', 1), resolved_content, flags=re.MULTILINE)

    # Ensure the directory for session task exists
    os.makedirs(os.path.dirname(session_task), exist_ok=True)

    with open(session_task, 'w', encoding='utf-8') as f:
        f.write(resolved_content)

    print(f"✅ Successfully loaded and resolved links from {args.global_board} to {session_task}")

if __name__ == "__main__":
    main()
