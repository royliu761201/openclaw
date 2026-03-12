#!/usr/bin/env python3
import sys
import argparse
import urllib.request
import urllib.error
import json
import os
import re
from pathlib import Path

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

def main():
    parser = argparse.ArgumentParser(description="Pure-Python Tavily Extract CLI Wrapper")
    parser.add_argument("urls", nargs="+", help="URLs to extract")
    args = parser.parse_args()

    load_openclaw_env()
    api_key = os.environ.get("TAVILY_API_KEY", "").strip()
    if not api_key:
        print("Error: Missing TAVILY_API_KEY environment variable. Have you configured ~/.openclaw_env?", file=sys.stderr)
        sys.exit(1)

    body = {
        "api_key": api_key,
        "urls": args.urls,
    }

    try:
        req = urllib.request.Request(
            "https://api.tavily.com/extract",
            data=json.dumps(body).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        text = e.read().decode('utf-8') if e.read else str(e)
        print(f"Error: Tavily Extract failed ({e.code}): {text}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    results = data.get("results", [])
    failed = data.get("failed_results", [])

    for r in results:
        url = str(r.get("url", "")).strip()
        content = str(r.get("raw_content", "")).strip()
        
        print(f"# {url}\n")
        print(content if content else "(no content extracted)")
        print("\n---\n")

    if failed:
        print("## Failed URLs\n")
        for f in failed:
            print(f"- {f.get('url')}: {f.get('error')}")

if __name__ == "__main__":
    main()
