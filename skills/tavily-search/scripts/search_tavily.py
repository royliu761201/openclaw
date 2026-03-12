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
    parser = argparse.ArgumentParser(description="Pure-Python Tavily Search CLI Wrapper")
    parser.add_argument("query", help="Search query")
    parser.add_argument("-n", type=int, default=5, help="Number of results")
    parser.add_argument("--deep", action="store_true", help="Use advanced search depth")
    parser.add_argument("--topic", choices=["general", "news"], default="general", help="Topic of the search")
    parser.add_argument("--days", type=int, help="Number of days (only relevant for news topic)")
    args = parser.parse_args()

    load_openclaw_env()
    api_key = os.environ.get("TAVILY_API_KEY", "").strip()
    if not api_key:
        print("Error: Missing TAVILY_API_KEY environment variable. Have you configured ~/.openclaw_env?", file=sys.stderr)
        sys.exit(1)

    search_depth = "advanced" if args.deep else "basic"

    body = {
        "api_key": api_key,
        "query": args.query,
        "search_depth": search_depth,
        "topic": args.topic,
        "max_results": max(1, min(args.n, 20)),
        "include_answer": True,
        "include_raw_content": False,
    }

    if args.topic == "news" and args.days is not None:
        body["days"] = args.days

    try:
        req = urllib.request.Request(
            "https://api.tavily.com/search",
            data=json.dumps(body).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        text = e.read().decode('utf-8') if e.read else str(e)
        print(f"Error: Tavily Search failed ({e.code}): {text}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Print AI-generated answer if available
    ans = data.get("answer")
    if ans:
        print("## Answer\n")
        print(ans)
        print("\n---\n")

    # Print results
    results = data.get("results", [])[:args.n]
    print("## Sources\n")

    for r in results:
        title = str(r.get("title", "")).strip()
        url = str(r.get("url", "")).strip()
        content = str(r.get("content", "")).strip()
        score = f" (relevance: {int(r['score'] * 100)}%)" if "score" in r else ""
        
        if not title or not url:
            continue
            
        print(f"- **{title}**{score}")
        print(f"  {url}")
        if content:
            short_content = content[:300] + ("..." if len(content) > 300 else "")
            print(f"  {short_content}")
        print()

if __name__ == "__main__":
    main()
