#!/usr/bin/env python3
import argparse
import subprocess
import json
import sys
import shutil

# Check for mcporter binary
MCPORTER_BIN = shutil.which("mcporter")
if not MCPORTER_BIN:
    # Try looking in common locations
    import os
    home = os.path.expanduser("~")
    # Try looking in common locations
    paths_to_check = [
        f"{home}/.cargo/bin/mcporter",
        "/usr/local/bin/mcporter",
        "/opt/homebrew/bin/mcporter"
    ]
    
    for path in paths_to_check:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            MCPORTER_BIN = path
            break

if not MCPORTER_BIN:
    # Fallback: check if 'mcporter' is in PATH even if shutil.which failed earlier context
    try:
        result = subprocess.run(["which", "mcporter"], capture_output=True, text=True)
        if result.returncode == 0:
            MCPORTER_BIN = result.stdout.strip()
    except Exception:
        pass

if not MCPORTER_BIN:
    print("Error: 'mcporter' binary not found in PATH or standard locations.")
    print("Please install via: npm install -g mcporter")
    sys.exit(1)

def run_mcporter(server_name, tool_name, args):
    """Executes an MCP tool call via mcporter."""
    # Construct arguments string for mcporter call format
    # Example: exa.web_search_exa(query: "search term", numResults: 5)
    
    arg_str = ", ".join([f'{k}: {json.dumps(v)}' for k, v in args.items() if v is not None])
    call_str = f"{server_name}.{tool_name}({arg_str})"
    
    # Explicitly point to the config file we know about
    config_path = "/Users/roy-jd/Documents/openclaw/config/mcporter.json"
    cmd = [MCPORTER_BIN, "--config", config_path, "call", call_str]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error calling {tool_name}: {e.stderr}")
        sys.exit(e.returncode)

def main():
    parser = argparse.ArgumentParser(description="Exa Web Search CLI Wrapper")
    subparsers = parser.add_subparsers(dest="command", help="Search type")

    # Web Search
    web_parser = subparsers.add_parser("web", help="Search the web")
    web_parser.add_argument("query", help="Search query")
    web_parser.add_argument("--num", type=int, default=5, help="Number of results")
    web_parser.add_argument("--type", choices=["auto", "fast", "deep"], default="auto", help="Search type")

    # Code Search
    code_parser = subparsers.add_parser("code", help="Search for code/docs")
    code_parser.add_argument("query", help="Search query")
    code_parser.add_argument("--tokens", type=int, default=3000, help="Max tokens (context)")
    
    # Company Research
    company_parser = subparsers.add_parser("company", help="Research a company")
    company_parser.add_argument("name", help="Company name")
    company_parser.add_argument("--num", type=int, default=5, help="Number of results")

    args = parser.parse_args()

    if not args.command:
        # Default to web search if no subcommand provided but query exists? 
        # Actually ArgumentParser handles this by showing help usually, but let's be flexible
        if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
            # Treat as web search query
            args.command = "web"
            args.query = sys.argv[1]
            args.num = 5
            args.type = "auto"
        else:
            parser.print_help()
            sys.exit(0)

    server = "exa" 
    # Check if 'exa' or 'exa-full' is available? Assuming 'exa' for basic tools.
    
    if args.command == "web":
        output = run_mcporter(server, "web_search_exa", {
            "query": args.query,
            "numResults": args.num,
            # "type": args.type # mcporter/exa API might verify this
        })
        print(output)

    elif args.command == "code":
        output = run_mcporter(server, "get_code_context_exa", {
            "query": args.query,
            "tokensNum": args.tokens
        })
        print(output)

    elif args.command == "company":
        output = run_mcporter(server, "company_research_exa", {
            "companyName": args.name,
            "numResults": args.num
        })
        print(output)

if __name__ == "__main__":
    main()
