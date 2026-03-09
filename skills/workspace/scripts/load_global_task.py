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
    parser.add_argument("--session_task", required=True, help="Path to the session task.md")
    args = parser.parse_args()

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
    os.makedirs(os.path.dirname(args.session_task), exist_ok=True)

    with open(args.session_task, 'w', encoding='utf-8') as f:
        f.write(resolved_content)

    print(f"✅ Successfully loaded and resolved links from {args.global_board} to {args.session_task}")

if __name__ == "__main__":
    main()
