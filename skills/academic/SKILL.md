---
name: academic
description: Search for academic papers on ArXiv and download them.
metadata: { "openclaw": { "emoji": "📚", "requires": { "bins": ["python"] } } }
---

# Academic Research Skill

Tools for searching and retrieving academic papers from ArXiv.

## Tools

### `search_papers`
Search for papers on ArXiv.

- **query** (string, required): The search query (e.g., "distributed reinforcement learning").
- **max_results** (number, optional): Number of results to return (default: 5).

### `download_paper`
Download a specific paper map to the workspace.

- **paper_id** (string, required): The ArXiv ID (e.g., "1706.03762").
- **filename** (string, optional): specific filename to save as.

## Usage Examples

```bash
# Search for papers
python skills/academic/scripts/search_arxiv.py search --query "attention is all you need"

# Download a paper
python skills/academic/scripts/search_arxiv.py download --id "1706.03762"
```
