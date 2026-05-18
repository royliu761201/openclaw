#!/bin/bash

if [ -z "$1" ]; then
    echo "Usage: bash deploy.sh [ENV_NAME]"
    exit 1
fi

ENV_NAME=$1
SHARED_NAS_DIR="/jhdx0003008/envs"
TARGET_PATH="$SHARED_NAS_DIR/$ENV_NAME"

echo "================================================="
echo "🌍 OpenClaw NAS-Shared GPU Environment Deployer"
echo "================================================="

ssh 90-1 << EOF
set -e
echo "[1/3] Sweeping old isolated bounds and ghosts..."
pkill -f "run_rebuttal_sweep" || true
pkill -f "src/main.py" || true

if [ -d "$TARGET_PATH" ]; then
    echo "⚠️ Target $TARGET_PATH already exists. Purging..."
    rm -rf "$TARGET_PATH"
fi

echo "[2/3] Executing Zero-Copy Hardlink Clone from base-research..."
/home/kaixin/miniconda3/bin/conda create -p "$TARGET_PATH" --clone base-research -y

echo "[3/3] Injecting Project Setup Bindings..."
/home/kaixin/miniconda3/bin/conda run -p "$TARGET_PATH" pip install -e /jhdx0003008/workspace/projects_core/SynergyFL

echo "✅ Environment '$ENV_NAME' is now globally accessible at $TARGET_PATH"
EOF

echo "Deployment Successful!"
