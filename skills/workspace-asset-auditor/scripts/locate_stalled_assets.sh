#!/bin/bash
# workspace-asset-auditor forensic script v1.0

TARGET_SIZE_MIN=$1
TARGET_SIZE_MAX=$2
TIME_MINUTES=120

if [ -z "$TARGET_SIZE_MIN" ] || [ -z "$TARGET_SIZE_MAX" ]; then
    echo "Usage: $0 [min_size_bytes] [max_size_bytes]"
    exit 1
fi

echo "--- Blue Team Asset Recovery Pulse ---"

# Step 1: mdfind metadata sweep
echo "[+] Performing Spotlight metadata sweep for files between $TARGET_SIZE_MIN and $TARGET_SIZE_MAX bytes..."
mdfind "kMDItemFSSize > $TARGET_SIZE_MIN && kMDItemFSSize < $TARGET_SIZE_MAX" | while read -r line; do
    ls -lh "$line" 2>/dev/null | grep -E "Apr  [0-9]{1,2}|$(date +'%b %e')"
done

# Step 2: Chrome History Surgical Query
HISTORY_DB="$HOME/Library/Application Support/Google/Chrome/Default/History"
TEMP_DB="/tmp/chrome_history_audit"

if [ -f "$HISTORY_DB" ]; then
    echo "[+] Interrogating Chrome History SQLite database..."
    cp "$HISTORY_DB" "$TEMP_DB"
    sqlite3 "$TEMP_DB" "SELECT target_path FROM downloads WHERE total_bytes > $TARGET_SIZE_MIN AND total_bytes < $TARGET_SIZE_MAX ORDER BY start_time DESC LIMIT 5;"
    rm "$TEMP_DB"
fi

# Step 3: Playwright Sandbox Check
echo "[+] Auditing Playwright Artifact sandboxes..."
ls -R /private/var/folders/ 2>/dev/null | grep "playwright-artifacts" | xargs -I {} find /private/var/folders/ -name "{}" -type d 2>/dev/null | xargs -I {} find {} -type f -size +100M 2>/dev/null

echo "--- Pulse Complete ---"
