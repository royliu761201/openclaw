import os

def write_text(path: str, content: str):
    """Atomic Op: Write text to file, ensuring dirs exist."""
    # Safety: Ensure we don't write outside valid areas if needed, but for now robust IO.
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)

def read_text(path: str) -> str:
    """Atomic Op: Read text from file."""
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        return f.read()

def list_files(path: str) -> list:
    if not os.path.exists(path):
        return []
    return os.listdir(path)
