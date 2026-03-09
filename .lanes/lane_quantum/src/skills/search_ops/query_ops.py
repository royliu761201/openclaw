import json
from typing import List, Dict, Any, Optional

"""
Atomic Search Query & Parsing Operations.
Pure functions for constructing prompts and parsing results.
"""

def build_grounding_query(query: str) -> str:
    """Constructs the grounding prompt."""
    return (
        f"Perform a Google Search to find 5 recent research papers (2024-2026) about: '{query}'.\n"
        "Return the results as a JSON list of objects with keys: 'title', 'authors' (string), 'year' (int), 'url' (direct link to arXiv/PDF if possible, avoid tracking redirects).\n"
        "Example: [{\"title\": \"Deep Learning...\", \"authors\": \"Smith et al.\", \"year\": 2024, \"url\": \"https://arxiv.org/abs/...\"}]"
        "\nENSURE VALID JSON."
    )

def parse_llm_json(text_response: str) -> List[Dict]:
    """Parses JSON from LLM response text."""
    try:
        clean_json = text_response.replace("```json", "").replace("```", "").strip()
        papers = json.loads(clean_json)
        
        valid_papers = []
        for p in papers:
            if isinstance(p, dict) and "title" in p:
                 # Filter out garbage domains
                 url = p.get("url", "").lower()
                 if "google.com/grounding-api-redirect" in url:
                     p["url"] = "" 
                 if "amazonaws.com" in p.get("title", "").lower():
                     continue
                 valid_papers.append(p)
        return valid_papers
    except Exception:
        return []

def filter_grounding_metadata(chunks: List[Any], max_results: int) -> List[Dict]:
    """Parses GroundingMetadata chunks."""
    results = []
    seen = set()
    
    for chunk in chunks:
        if chunk.web:
            url = chunk.web.uri
            title = chunk.web.title
            
            if "grounding-api-redirect" in url.lower():
                continue
            if "amazonaws.com" in title.lower() or "google cloud" in title.lower():
                continue
            
            if title not in seen:
                seen.add(title)
                results.append({
                    "title": title,
                    "url": url,
                    "year": 2024,
                    "authors": "Unknown",
                    "snippet": "Referenced in grounding source."
                })
                
    return results[:max_results]
