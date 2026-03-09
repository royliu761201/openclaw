import os
from utils.file_ops import write_text, read_text

JOURNAL_PATH = "research_vault/knowledge/experience.md"

def append_insight(insight: str, path: str = JOURNAL_PATH):
    """
    Atomic Op: Appends a reflection/insight to the experience log.
    """
    current = read_text(path) or "# Experience Log\n"
    new_entry = f"\n\n## Insight\n{insight}"
    write_text(path, current + new_entry)

def read_history(path: str = JOURNAL_PATH) -> str:
    """
    Atomic Op: Retrieves past experience.
    """
    return read_text(path) or ""
