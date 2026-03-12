---
name: tavily
description: AI-optimized web search via Tavily API. Returns concise, relevant results for AI agents.
homepage: https://tavily.com
metadata:
  {
    "openclaw":
      {
        "emoji": "🔍",
        "requires": { "bins": ["python3"], "env": ["TAVILY_API_KEY"] },
        "primaryEnv": "TAVILY_API_KEY",
      },
  }
---

# Tavily Search

AI-optimized web search using Tavily API. Designed for AI agents - returns clean, relevant content.

## Search

```bash
./scripts/search_tavily.py "query"
./scripts/search_tavily.py "query" -n 10
./scripts/search_tavily.py "query" --deep
./scripts/search_tavily.py "query" --topic news
```

## Options

- `-n <count>`: Number of results (default: 5, max: 20)
- `--deep`: Use advanced search for deeper research (slower, more comprehensive)
- `--topic <topic>`: Search topic - `general` (default) or `news`
- `--days <n>`: For news topic, limit to last n days

## Extract content from URL

```bash
./scripts/extract_tavily.py "https://example.com/article"
```

Notes:

- Needs `TAVILY_API_KEY` from https://tavily.com
- Tavily is optimized for AI - returns clean, relevant snippets
- Use `--deep` for complex research questions
- Use `--topic news` for current events
