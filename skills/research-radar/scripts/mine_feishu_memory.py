import os
import sys
import sqlite3
import json
import re
import datetime
from pathlib import Path
import subprocess

WORKSPACE_DIR = Path(os.path.expanduser("~/workspace"))
DB_PATH = Path(os.path.expanduser("~/.openclaw/memory/main.sqlite"))
OUT_FILE = WORKSPACE_DIR / "docs" / "research_ideation" / "radar_raw_data" / "feishu_inbox.json"

def get_db_connection():
    if not DB_PATH.exists():
        print(f"Error: OpenClaw database not found at {DB_PATH}")
        sys.exit(1)
    return sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)

def mine_memory():
    # Only mine records from the last 24 hours
    one_day_ago = int((datetime.datetime.now() - datetime.timedelta(days=1)).timestamp() * 1000)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # We query the chunks table which stores conversation history.
    # Looking for pieces of text containing http:// or https://
    query = """
        SELECT id, text, updated_at
        FROM chunks 
        WHERE text LIKE '%http://%' OR text LIKE '%https://%'
        AND updated_at > ?
        ORDER BY updated_at ASC
    """
    
    cursor.execute(query, (one_day_ago,))
    rows = cursor.fetchall()
    
    inbox_items = []
    
    for row in rows:
        chunk_id, text, updated_at = row
        
        # Extract URLs
        urls = re.findall(r'(https?://[A-Za-z0-9\.\-\_\/\?\&\=\%]+)', text)
        if not urls:
            continue
            
        # Optional: Try to find a subsequent assistant response around the same time to grab the web_fetch context
        # In a generic SQLite pull, we just grab everything near it.
        context_query = """
            SELECT text
            FROM chunks
            WHERE updated_at > ? AND updated_at < ?
            AND text NOT LIKE '%http://%' AND text NOT LIKE '%https://%'
            ORDER BY updated_at ASC
            LIMIT 3
        """
        # Look 5 minutes ahead
        future_time = updated_at + (5 * 60 * 1000)
        cursor.execute(context_query, (updated_at, future_time))
        context_rows = cursor.fetchall()
        
        context_str = "\n".join([c[0] for c in context_rows]) if context_rows else "No immediate assistant context found."
        
        for url in urls:
            inbox_items.append({
                "url": url,
                "timestamp": updated_at,
                "context": context_str
            })
            
    conn.close()
    
    # Deduplicate in the inbox itself to save space
    unique_items = {}
    for item in inbox_items:
        unique_items[item["url"]] = item # Keep the latest
        
    final_list = list(unique_items.values())
    
    # Save to file
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    with open(OUT_FILE, "w") as f:
        json.dump(final_list, f, indent=4, ensure_ascii=False)
        
    print(f"✅ Mined {len(final_list)} URLs from OpenClaw memory in the last 24h.")

def git_sync():
    print("🔄 Pushing Feishu Inbox to SSoT Git...")
    try:
        subprocess.run(["git", "add", str(OUT_FILE)], cwd=str(WORKSPACE_DIR), check=True)
        
        # Check if there are staged changes to commit
        diff_status = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=str(WORKSPACE_DIR))
        if diff_status.returncode == 0:
            print("   [Skip] No new links to commit.")
            return
            
        subprocess.run(["git", "commit", "-m", "[Auto] Update Feishu Inbox from Memory Miner"], cwd=str(WORKSPACE_DIR), check=True)
        subprocess.run(["git", "pull", "--rebase", "--autostash"], cwd=str(WORKSPACE_DIR), check=True)
        subprocess.run(["git", "push"], cwd=str(WORKSPACE_DIR), check=True)
        print("✅ Git Sync Complete.")
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Git Sync Error: {e}")

if __name__ == "__main__":
    mine_memory()
    git_sync()
