import argparse
import os

def read_file(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            print(f.read())
    except Exception as e:
        print(f"Error: {e}")

def write_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Wrote to {path}")

def replace_in_file(path, old, new):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {path}: {e}")
        return
    
    if old not in content:
        print(f"Error: '{old}' not found in {path}")
        # Print snippet for debugging
        print(f"Snippet: {content[:100]}...")
        return

    new_content = content.replace(old, new)
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"Replaced text in {path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Read
    r_parser = subparsers.add_parser("read")
    r_parser.add_argument("path")
    
    # Write
    w_parser = subparsers.add_parser("write")
    w_parser.add_argument("path")
    w_parser.add_argument("content")
    
    # Replace
    rep_parser = subparsers.add_parser("replace")
    rep_parser.add_argument("path")
    rep_parser.add_argument("old")
    rep_parser.add_argument("new")
    
    args = parser.parse_args()
    
    if args.command == "read":
        read_file(args.path)
    elif args.command == "write":
        write_file(args.path, args.content)
    elif args.command == "replace":
        replace_in_file(args.path, args.old, args.new)
