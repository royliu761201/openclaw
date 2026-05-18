#!/bin/bash
# install_fa2_cluster.sh - Solidified Cluster Installation for FlashAttention-2
# Targets heterogeneous Sm89 (L20/4090) nodes (ARM & x86_64) in a containerized cluster.

set -e

# --- Configuration & SSoT ---
SSOT_PY="/usr/bin/python3"  # Local cluster python standard
CACHE_ROOT="/jhdx0003008/cache/wheels"
FA2_VERSION="2.8.4"
BUILD_ROOT="/tmp/fa2_localized_build"

# Detect Architecture
ARCH=$(uname -m)
GPU_ARCH="89" # Optimized for Sm89 (Ada Lovelace)

# Identification
echo "🚀 Starting FlashAttention-2 Installation Solidification Phase"
echo "📍 Node Arhitecture: $ARCH"
echo "📍 Targeting GPU Sm: $GPU_ARCH"

# 1. Environment Detection
if ! command -v nvcc &> /dev/null; then
    echo "❌ Error: nvcc not found. Ensure CUDA toolkit is in PATH."
    exit 1
fi

# 2. Check for Pre-compiled Wheels in NAS Cache
WHEEL_PATTERN="flash_attn-${FA2_VERSION}*${ARCH}*.whl"
EGG_PATTERN="flash_attn-${FA2_VERSION}*${ARCH}*.egg"

FOUND_BINARY=$(find "$CACHE_ROOT" -name "$WHEEL_PATTERN" -o -name "$EGG_PATTERN" | head -n 1)

if [ -n "$FOUND_BINARY" ]; then
    echo "✅ Found pre-compiled binary in NAS cache: $FOUND_BINARY"
    echo "📦 Installing from cache..."
    $SSOT_PY -m pip install "$FOUND_BINARY"
    echo "✨ Installation Successful (from Cache)"
    exit 0
fi

# 3. Compilation Logic (Fallback)
echo "🔍 Binary not found in cache. Starting accelerated localized build..."

# Prerequisites for High-Speed Build
export FLASH_ATTN_CUDA_ARCHS="$GPU_ARCH"
export MAX_JOBS=$(nproc)
export LDFLAGS="-Wl,--threads=$MAX_JOBS -Wl,--fuse-ld=gold"

# Localize source
if [ ! -d "csrc" ]; then
    echo "❌ Error: This script must be run from the FlashAttention-2 source root."
    exit 1
fi

mkdir -p "$BUILD_ROOT"
cp -r . "$BUILD_ROOT"
cd "$BUILD_ROOT"

# Trigger Accelerated Build
echo "⚡ Building with MAX_JOBS=$MAX_JOBS and ld.gold..."
$SSOT_PY setup.py bdist_wheel

# 4. Installation & Cache Flush
WHEEL_FILE=$(ls dist/flash_attn*.whl | head -n 1)
if [ -z "$WHEEL_FILE" ]; then
    WHEEL_FILE=$(ls dist/flash_attn*.egg | head -n 1)
fi

echo "📦 Installing generated binary: $WHEEL_FILE"
$SSOT_PY -m pip install "$WHEEL_FILE"

echo "💾 Flushing binary to NAS cache: $CACHE_ROOT"
mkdir -p "$CACHE_ROOT"
cp "$WHEEL_FILE" "$CACHE_ROOT/"

echo "✨ Solidified Cluster Installation Complete."
