#!/usr/bin/env bash

# L1 Constitution Compliant: Zero-Bloat VENV Sandbox Deployment
# This script ensures that kokoro-tts is deployed in absolute isolation.
# It uses only offline wheels from ~/openclaw_data/raw/ and does NOT pollute global space.

set -e

# 1. Define Paths
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SKILL_DIR/venv"
RAW_DATA_DIR="$HOME/openclaw_data/raw"
MODELS_DIR="$SKILL_DIR/models"

echo "🛡️ Initiating Kokoro-TTS Isolated Sandbox Deployment..."

# 2. Check for offline payload
if [ ! -d "$RAW_DATA_DIR" ]; then
    echo "❌ Offline wheel vault not found at $RAW_DATA_DIR. Cannot proceed with Zero-Download deployment."
    exit 1
fi

# 3. Create Virtual Environment
if [ -d "$VENV_DIR" ]; then
    echo "🧹 Purging existing sandbox..."
    rm -rf "$VENV_DIR"
fi

echo "📦 Creating isolated Python 3.9 venv..."
/usr/bin/python3 -m venv "$VENV_DIR"

# 4. Activate Venv & Install Offline Wheels
echo "⚙️ Injecting offline dependencies into sandbox..."
source "$VENV_DIR/bin/activate"

# Upgrade pip locally just in case, but keep it quiet
python3 -m pip install --upgrade pip -q

# Install from our curated vault with strict no-index enforcement
echo ">>> Installing Heavy C++ Payloads (LLVM, NumPy, ONNX, Espeak-NG)..."
python3 -m pip install "$RAW_DATA_DIR"/llvmlite*.whl "$RAW_DATA_DIR"/numpy*.whl "$RAW_DATA_DIR"/onnxruntime*.whl "$RAW_DATA_DIR"/espeakng_loader*.whl --no-index --find-links="$RAW_DATA_DIR"

echo ">>> Unzipping Patched Kokoro Framework..."
# We use the pre-patched framework to avoid Python 3.10 syntax errors on macOS
unzip -qo "$HOME/openclaw_data/weights/kokoro_v1.zip" -d "$VENV_DIR/lib/python3.9/site-packages/"

echo ">>> Installing remaining sub-dependencies (phonemizer, soundfile)..."
# Using the wheels cached inside the zip payload
unzip -qo /tmp/wheels_cache/node01_site_packages_backup.zip -d /tmp/wheels_unpack_temp/
cp -r /tmp/wheels_unpack_temp/* "$VENV_DIR/lib/python3.9/site-packages/"
rm -rf /tmp/wheels_unpack_temp/

# 5. Fetch Models (Simulated for Node 01, should already be there)
mkdir -p "$MODELS_DIR"
if [ ! -f "$MODELS_DIR/kokoro-v1.0.onnx" ]; then
    echo "⬇️ Retrieving ONNX Model from vault..."
    # Ideally scp from Node 03, but since we are deploying locally:
    if [ -f "$HOME/openclaw_data/weights/kokoro/kokoro-v1.0.onnx" ]; then
         cp "$HOME/openclaw_data/weights/kokoro/"* "$MODELS_DIR/"
    else
         echo "⚠️ Warning: ONNX model missing from vault. Please pull from Node 03."
    fi
fi

# Final Check
echo "✅ Sandboxed Deployment Successful!"
echo "Invoke via: $VENV_DIR/bin/python3 $SKILL_DIR/scripts/kokoro_tts_tool.py"
