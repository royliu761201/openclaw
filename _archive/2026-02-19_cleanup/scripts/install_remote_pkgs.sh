#!/bin/bash

# Define paths
VENDOR_DIR=$(find /root/research_bot/archive -name "vendor" -type d | head -n 1)
ENVS=("pesso" "calam" "cogd" "frenet" "medgemma" "medtime")

echo "📦 Found downloaded packages in: $VENDOR_DIR"
ls -lh $VENDOR_DIR/*.whl 2>/dev/null

if [ -z "$VENDOR_DIR" ]; then
    echo "❌ No vendor directory found!"
    exit 1
fi

# Define Python executable path pattern
# Assuming standard Miniconda location
CONDA_BASE="/root/miniconda3"

echo "🚀 Starting installation across environments..."

for env in "${ENVS[@]}"; do
    PYTHON="$CONDA_BASE/envs/$env/bin/python"
    
    if [ -f "$PYTHON" ]; then
        echo "---------------------------------------------------"
        echo "🔧 Installing into environment: $env"
        # Force reinstall from local wheels to ensure we use the downloaded versions
        "$PYTHON" -m pip install --no-index --find-links "$VENDOR_DIR" google_genai lightning gdown rapidfuzz matplotlib --force-reinstall
        echo "✅ $env updated."
    else
        echo "⚠️  Environment $env not found (skipping)."
    fi
done

echo "🎉 All installations complete!"
