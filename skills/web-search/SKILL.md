---
name: web-search
description: Search the web using DuckDuckGo (free, no API key required). Supports web, news, images, and videos with filtering options. Use python3 to run the script.
homepage: https://duckduckgo.com
metadata:
  openclaw:
    emoji: 🦆
    requires:
      bins: ["python3"]
      packages: ["duckduckgo-search"]
---

# Web Search Skill

Free web search powered by DuckDuckGo. No API keys required.

## CLI Usage

### Basic Web Search

```bash
# Simple web search
python3 skills/web-search/scripts/search.py "python asyncio tutorial"

# Limit results
python3 skills/web-search/scripts/search.py "machine learning" --max-results 20

# Time filter (d=day, w=week, m=month, y=year)
python3 skills/web-search/scripts/search.py "AI news" --time-range w
```

### News Search

```bash
# Recent news
python3 skills/web-search/scripts/search.py "climate change" --type news --time-range w

# More news results
python3 skills/web-search/scripts/search.py "technology" --type news --max-results 15
```

### Image Search

```bash
# Basic image search
python3 skills/web-search/scripts/search.py "sunset" --type images --max-results 20

# Image with size filter
python3 skills/web-search/scripts/search.py "landscape" --type images --image-size Large

# Image with color filter
python3 skills/web-search/scripts/search.py "abstract art" --type images --image-color Blue
```

**Image filters**:

- Size: `Small`, `Medium`, `Large`, `Wallpaper`
- Color: `Red`, `Orange`, `Yellow`, `Green`, `Blue`, `Purple`, `Pink`, `Monochrome`, etc.
- Type: `photo`, `clipart`, `gif`, `transparent`, `line`
- Layout: `Square`, `Tall`, `Wide`

### Video Search

```bash
# Video search
python3 skills/web-search/scripts/search.py "python tutorial" --type videos --max-results 15

# Short videos
python3 skills/web-search/scripts/search.py "cooking recipes" --type videos --video-duration short
```

**Video filters**:

- Duration: `short`, `medium`, `long`
- Resolution: `high`, `standard`

## Output Formats

### Text (Default)

```bash
python3 skills/web-search/scripts/search.py "quantum computing"
```

### Markdown

```bash
python3 skills/web-search/scripts/search.py "AI research" --format markdown
```

### JSON

```bash
python3 skills/web-search/scripts/search.py "machine learning" --format json
```

## Save to File

```bash
# Save web results
python3 skills/web-search/scripts/search.py "AI trends" --output results.txt

# Save news as markdown
python3 skills/web-search/scripts/search.py "tech news" --type news --format markdown --output news.md

# Save as JSON
python3 skills/web-search/scripts/search.py "research" --format json --output data.json
```

## Advanced Options

### Region-Specific Search

```bash
python3 skills/web-search/scripts/search.py "local news" --region us-en --type news
```

Common regions: `us-en`, `uk-en`, `ca-en`, `au-en`, `wt-wt` (worldwide)

### Safe Search

```bash
python3 skills/web-search/scripts/search.py "medical info" --safe-search on
```

Options: `on`, `moderate` (default), `off`

## Common Parameters

- `--type` or `-t`: Search type (`web`, `news`, `images`, `videos`)
- `--max-results` or `-n`: Maximum results (default: 10)
- `--time-range`: Time filter (`d`, `w`, `m`, `y`)
- `--region` or `-r`: Region code (default: `wt-wt`)
- `--format` or `-f`: Output format (`text`, `markdown`, `json`)
- `--output` or `-o`: Save to file

## Output Examples

**Text format**:

```
1. Page Title
   URL: https://example.com
   Description of the page...
```

**Markdown format**:

```markdown
## 1. Page Title

**URL:** https://example.com
Description of the page...
```

**JSON format**:

```json
[{ "title": "Page Title", "href": "https://example.com", "body": "Description..." }]
```

## Installation

Install required dependency:

```bash
pip install duckduckgo-search
```

## Full Help

```bash
python3 skills/web-search/scripts/search.py --help
```
