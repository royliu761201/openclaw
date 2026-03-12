#!/usr/bin/env python3
import os
import sys
import argparse
import warnings
import re
from pathlib import Path

# Suppress urllib3 warnings about OpenSSL
warnings.filterwarnings("ignore", category=UserWarning, module="urllib3")
warnings.filterwarnings("ignore", message="urllib3 v2 only supports OpenSSL 1.1.1+")

def load_openclaw_env():
    # Cron environments are absolutely bare. We explicitly parse the Node's SSoT env file.
    env_file = Path(os.path.expanduser("~/.openclaw_env"))
    if env_file.exists():
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("export "):
                    parts = line[7:].split("=", 1)
                    if len(parts) == 2:
                        key, val = parts[0].strip(), parts[1].strip()
                        # Remove bounding quotes
                        val = re.sub(r'^["\']|["\']$', '', val)
                        os.environ[key] = val

try:
    from exa_py import Exa
except ImportError:
    print("Error: 'exa_py' module not found. Please install it via: pip install exa_py")
    sys.exit(1)

def get_exa_client():
    # SSoT: Pure environment variable injection
    load_openclaw_env()
    api_key = os.environ.get("EXA_API_KEY")
    if not api_key:
        print("Error: EXA_API_KEY environment variable not set. Please configure ~/.openclaw_env")
        sys.exit(1)
    return Exa(api_key)

def format_results(results):
    for idx, res in enumerate(results):
        print(f"### Result {idx + 1}: {res.title}")
        print(f"**URL:** {res.url}")
        if getattr(res, 'author', None):
            print(f"**Author:** {res.author}")
        if getattr(res, 'published_date', None):
            print(f"**Published Date:** {res.published_date}")
        if getattr(res, 'text', None):
            text = res.text[:3000] + ("..." if len(res.text) > 3000 else "")
            print(f"\n{text}\n")
        print("-" * 40)

def main():
    parser = argparse.ArgumentParser(description="Pure-Python Exa Search CLI Wrapper")
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
        if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
            args.command = "web"
            args.query = sys.argv[1]
            args.num = 5
            args.type = "auto"
        else:
            parser.print_help()
            sys.exit(0)

    try:
        exa = get_exa_client()
        
        if args.command == "web":
            # Native exa API call for generic web search
            response = exa.search_and_contents(
                args.query,
                num_results=args.num,
                text=True
            )
            format_results(response.results)

        elif args.command == "code":
            # Focused Exa API search for code/github
            response = exa.search_and_contents(
                args.query,
                num_results=args.num if hasattr(args, 'num') else 3,
                text={"max_characters": args.tokens * 4}
            )
            format_results(response.results)

        elif args.command == "company":
            # Company focus 
            response = exa.search_and_contents(
                args.name,
                category="company",
                num_results=args.num,
                text=True
            )
            format_results(response.results)

    except Exception as e:
        print(f"Error querying Exa: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
