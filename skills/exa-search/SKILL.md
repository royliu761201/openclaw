---
name: exa-search
description: High-quality AI web search using Exa (CLI optimized). Search for web content, code snippets/docs, or company info. No API key needed.
homepage: https://exa.ai
metadata:
  openclaw:
    emoji: 🔍
    requires:
      bins: ["python3", "mcporter"]
---

# Exa Web Search (CLI)

Perform deep neural searches on the web, retrieve code snippets, or research companies using the Exa engine.

## Usage

### 1. Web Search

Search for general information, news, or facts.

```bash
./scripts/exa_search.py web "latest AI news" --num 5
```

**Parameters:**

- `query`: The search query string.
- `--num`: Number of results (default: 5).

### 2. Code Search

Find code examples, library documentation, or programming solutions.

```bash
./scripts/exa_search.py code "react useEffect hook example" --tokens 2000
```

**Parameters:**

- `query`: What code/docs you are looking for.
- `--tokens`: Max context tokens to retrieve (default: 3000).

### 3. Company Research

Get structured information about a specific company.

```bash
./scripts/exa_search.py company "Anthropic" --num 3
```

**Parameters:**

- `name`: Name of the company.
- `--num`: Number of results.

## Requirements

- `mcporter` must be installed and configured with Exa.
  - Check: `mcporter list`
  - Install: `mcporter config add exa https://mcp.exa.ai/mcp`
