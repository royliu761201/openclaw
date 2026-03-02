#!/bin/bash
# OpenClaw Unified Fetcher (Standard: aria2c 16-parallel)

URL=$1
FILENAME=$2
TYPE=${3:-raw} # raw, processed, weights
PROVIDER=${4:-misc}

if [ -z "$URL" ] || [ -z "$FILENAME" ]; then
    echo "Usage: claw-fetch <URL> <FILENAME> [TYPE] [PROVIDER]"
    exit 1
fi

DATA_ROOT=""
[ -d "/jxdxxxx" ] && DATA_ROOT="/jxdxxxx/openclaw_data" || DATA_ROOT="$HOME/openclaw_data"

DEST_DIR="$DATA_ROOT/$TYPE"
mkdir -p "$DEST_DIR"

echo "🚀 Fetching $FILENAME via aria2c (16 parallel segments)..."
aria2c -x 16 -s 16 -d "$DEST_DIR" -o "$FILENAME" "$URL"

# Generate spec.yaml (Metadata)
CAT_FILE="$DEST_DIR/${FILENAME}.spec.yaml"
cat <<EOF > "$CAT_FILE"
id: ${PROVIDER}_${FILENAME}
source: $URL
timestamp: $(date +%Y-%m-%d)
checksum: $(md5sum "$DEST_DIR/$FILENAME" | awk '{print $1}')
status: completed
EOF

echo "✅ Download complete. Metadata stored in $CAT_FILE"
