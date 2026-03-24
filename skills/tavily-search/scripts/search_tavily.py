#!/usr/bin/env python3
"""
Tavily Search — Python implementation with dual-key rotation.

Key priority:
  1. TAVILY_API_KEY_1  (primary account)
  2. TAVILY_API_KEY_2  (backup account)
  3. TAVILY_API_KEY    (legacy single-key fallback)

On HTTP 432 (quota exhausted), automatically rotates to the next key.

Usage: python3 search_tavily.py "query string" -n 3
"""
import os
import sys
import json
import argparse
import urllib.request
import urllib.error

TAVILY_API_URL = "https://api.tavily.com/search"


def search(query: str, max_results: int = 3) -> dict:
    """Try keys in order: KEY_1 → KEY_2 → TAVILY_API_KEY (legacy)."""
    key1 = os.environ.get("TAVILY_API_KEY_1", "")
    key2 = os.environ.get("TAVILY_API_KEY_2", "")
    legacy = os.environ.get("TAVILY_API_KEY", "")

    # Build priority list (deduplicated, non-empty)
    candidates = []
    for k in [key1, key2, legacy]:
        if k and k not in candidates:
            candidates.append(k)

    if not candidates:
        print("❌ No Tavily API key found. Set TAVILY_API_KEY_1, TAVILY_API_KEY_2, or TAVILY_API_KEY.", file=sys.stderr)
        sys.exit(1)

    last_error = None
    for i, key in enumerate(candidates):
        label = f"KEY_{i+1}" if i < 2 else "TAVILY_API_KEY"
        payload = json.dumps({
            "query": query,
            "max_results": max_results,
            "search_depth": "basic",
            "include_answer": True,
        }).encode("utf-8")

        req = urllib.request.Request(
            TAVILY_API_URL,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            is_quota = e.code == 432 or "usage limit" in body.lower()
            last_error = f"Tavily Search failed ({e.code}): {body}"
            if is_quota and i + 1 < len(candidates):
                print(f"⚠️ [{label}] Quota exhausted (432). Rotating to next key...", file=sys.stderr)
                continue
            # Non-quota error or last key → exit
            print(last_error, file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            last_error = f"Tavily request error: {e}"
            print(last_error, file=sys.stderr)
            sys.exit(1)

    print(f"❌ All Tavily keys exhausted. Last error: {last_error}", file=sys.stderr)
    sys.exit(1)


def format_output(data: dict) -> str:
    lines = []
    answer = data.get("answer", "")
    if answer:
        lines.append(f"## Answer\n\n{answer}\n")
    results = data.get("results", [])
    if results:
        lines.append("---\n\n## Sources\n")
        for r in results:
            score = int(r.get("score", 0) * 100)
            lines.append(f"- **{r.get('title', 'Untitled')}** (relevance: {score}%)")
            lines.append(f"  {r.get('url', '')}")
            snippet = r.get("content", "")[:200]
            if snippet:
                lines.append(f"  {snippet}\n")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Tavily Search (Python, dual-key rotation)")
    parser.add_argument("query", help="Search query")
    parser.add_argument("-n", "--num", type=int, default=3, help="Max results (default: 3)")
    args = parser.parse_args()

    data = search(args.query, args.num)
    print(format_output(data))


if __name__ == "__main__":
    main()
