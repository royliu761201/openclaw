---
name: academic-search
description: Search for academic papers on ArXiv.
metadata: { "openclaw": { "emoji": "📚", "requires": { "bins": ["python3"] } } }
---

# Academic Search Skill

Tools for searching academic papers from ArXiv.

## Anti-Hallucination Clause
> **[L1 Constitution Block]**: Agents are STRICTLY FORBIDDEN from attempting to write custom Python `requests` or `BeautifulSoup` scrapers targeting arXiv. You MUST use this `academic-search` tool natively. Writing ad-hoc scrapers for standard academic repositories violates the PURE Response Protocol (Unify & Trim).

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
