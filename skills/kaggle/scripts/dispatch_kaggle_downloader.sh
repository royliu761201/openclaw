#!/bin/bash
# ==============================================================================
# 🚀 OpenClaw: Kaggle Downloader Proxy Dispatcher
# ==============================================================================
# This script automates the process of using Kaggle's high-speed internet as a 
# proxy to download massive datasets or pip packages, then securely pulling the 
# zipped artifact straight into the 10.190 GPU Server's physical data drive.
# ==============================================================================

set -e

if [ $# -lt 3 ]; then
    echo "Usage: ./dispatch_kaggle_downloader.sh <username> <slug_name> <pip_package_or_url> [gpu_target_dir]"
    echo "Example: ./dispatch_kaggle_downloader.sh roylxh5147 mantra-downloader mantra-dataset /jhdx0003008/data/mantra"
    exit 1
fi

USERNAME=$1
SLUG=$2
TARGET_DEB=$3
GPU_TARGET_DIR=${4:-"/jhdx0003008/data/$SLUG"}

# 1. Ensure Local Vault context is available
if [ ! -f "$HOME/.openclaw_env" ]; then
    echo "❌ FATAL: ~/.openclaw_env not found. Aborting."
    exit 1
fi
source "$HOME/.openclaw_env"

# Extract API Key dynamically based on Username
# Expects KAGGLE_XIAOHUALIU_KEY or KAGGLE_ROYLXH_KEY etc.
UPPER_USER=$(echo "$USERNAME" | tr '[:lower:]' '[:upper:]')
KEY_VAR_NAME="KAGGLE_${UPPER_USER}_KEY"
API_KEY="${!KEY_VAR_NAME}"

if [ -z "$API_KEY" ]; then
    # Hard fallback to ROYLXH
    API_KEY="$KAGGLE_ROYLXH_KEY"
    USERNAME="roylxh5147"
    echo "⚠️ Warning: Specific API key not found in vault. Falling back to proxy account: $USERNAME"
fi

export KAGGLE_USERNAME="$USERNAME"
export KAGGLE_KEY="$API_KEY"

# Force Kaggle connection outside local TUN proxy blocks
unset http_proxy https_proxy all_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY

# 2. Build Kaggle Kernel Workspace
WORKDIR="/tmp/kaggle_proxy_out_$SLUG"
rm -rf "$WORKDIR"
mkdir -p "$WORKDIR"
cd "$WORKDIR"

echo "=================================="
echo "📦 1. Generating Cloud Fetch Payload constraint..."

cat <<EOF > download_payload.py
import os
import shutil

print("Executing Cloud Proxy Download Task...")
# Example execution: Either a pip install -d or direct curl/wget execution
# Depending on TARGET_DEB type, we decide the python logic.
target = "$TARGET_DEB"

if target.startswith("http"):
    os.system(f"wget -q {target} -O /kaggle/working/download_artifact")
else:
    # Try as a pip package / dataset library
    os.system(f"pip install {target}")
    # User might need to adapt the exact scraping logic depending on the package
    # This is a generic python scrape baseline
    with open('/kaggle/working/README_PROXY.txt', 'w') as f:
        f.write("Package installed in kernel. Write custom logic to dump data here.")

print("Zipping the /kaggle/working directory...")
shutil.make_archive('/kaggle/working/proxy_output', 'zip', '/kaggle/working')
print("✅ Done! Zipped to proxy_output.zip")
EOF

cat <<EOF > kernel-metadata.json
{
  "id": "$USERNAME/$SLUG",
  "title": "Proxy Downloader $SLUG",
  "code_file": "download_payload.py",
  "language": "python",
  "kernel_type": "script",
  "is_private": "true",
  "enable_gpu": "false",
  "enable_internet": "true",
  "dataset_sources": [],
  "competition_sources": [],
  "kernel_sources": []
}
EOF

# 3. Push to Kaggle
echo "=================================="
echo "🚀 2. Launching target into Kaggle Cloud..."
python3 ~/openclaw/skills/kaggle/scripts/kaggle_tool.py kernel_push "$WORKDIR" || { echo "❌ Kaggle Push Failed."; exit 1; }

echo "=================================="
echo "⏳ 3. You must wait for the kernel to finish on Kaggle's website (~1-5 mins)."
echo "When it finishes, run the following command directly on your GPU Server terminal:"
echo "----------------------------------------------------------------------------------------------------------"
echo "ssh gpu \"source /opt/conda/etc/profile.d/conda.sh; conda activate base-research; export KAGGLE_USERNAME=$USERNAME; export KAGGLE_KEY=$API_KEY; mkdir -p $GPU_TARGET_DIR && cd $GPU_TARGET_DIR && kaggle kernels output $USERNAME/$SLUG -p . && unzip -o proxy_output.zip\""
echo "----------------------------------------------------------------------------------------------------------"
echo "✅ Workflow deployed successfully! You can track execution via 'kaggle kernels status $USERNAME/$SLUG'"
