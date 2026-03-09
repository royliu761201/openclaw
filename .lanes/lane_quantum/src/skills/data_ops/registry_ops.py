from typing import Dict, Any, Optional

"""
Atomic Data Registry Operations.
Pure functions for looking up dataset metadata.
"""

def resolve_dataset_source(registry: Dict[str, Any], dataset_name: str) -> Optional[Dict[str, str]]:
    """
    Looks up dataset in registry.
    Returns dict with 'url', 'type' etc or None.
    """
    if dataset_name not in registry:
        return None
        
    entry = registry[dataset_name]
    return {
        "url": entry.get("path"),
        "source": entry.get("source", "url")
    }
