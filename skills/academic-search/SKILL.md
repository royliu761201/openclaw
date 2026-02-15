---
name: academic-search
description: Search for academic papers on ArXiv.
metadata: { "openclaw": { "emoji": "📚", "requires": { "bins": ["python3"] } } }
---

# Academic Search Skill

Tools for searching academic papers from ArXiv.

## Tools

### `search_papers`

Search for papers on ArXiv.

- **query** (string, required): The search query (e.g., "distributed reinforcement learning").
- **max_results** (number, optional): Number of results to return (default: 5).

## Usage Examples

```bash
# Search for papers
./scripts/search_arxiv.py search --query "attention is all you need"
```
