#!/bin/bash
set -e
echo "🛡️ Initiating Hermetic Drop Installation..."
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "1/3 Destroying old world..."
rm -rf venv # clear sandbox cache
python3 -m venv venv

echo "2/3 Engaging Sandbox Vacuum (No-Network Policy Limit)..."
# IMPORTANT: Change RAW_DATA_DIR to point to your physical WHEELS_CACHE_DIR on the target node.
RAW_DATA_DIR="/tmp/wheels_cache/intel-fetch"
if [ ! -d "$RAW_DATA_DIR" ]; then
    echo "❌ Missing RAW Data. Did you sync the wheels from Vault?"
    exit 1
fi

echo "3/3 Blind Injection (__NO__ Http Traffic allowed)..."
./venv/bin/pip install --no-index --find-links="$RAW_DATA_DIR" --no-deps "$RAW_DATA_DIR"/*.whl
echo "✅ Hermetic Drop Complete."
