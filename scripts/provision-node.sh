#!/bin/bash
# OpenClaw Node Provisioning Script
# Automates Pillar 1 (Auth-Zero) and Pillar 3 (Lean-Node) standards.

set -e

echo "========================================"
echo " OpenClaw Node Provisioning Scaffold"
echo "========================================"

# 1. Generate Ed25519 Key (Auth-Zero)
echo "[1/5] Checking SSH Keys..."
if [ ! -f ~/.ssh/id_ed25519 ]; then
    echo "  -> Generating new Ed25519 keypair..."
    ssh-keygen -t ed25519 -q -N "" -f ~/.ssh/id_ed25519
else
    echo "  -> Ed25519 key already exists."
fi

# 2. Inject Domestic Mirrors (Lean-Node)
echo "[2/5] Injecting Domestic Mirrors into shell profile..."
PROFILE=~/.zshrc
if ! grep -q "TUNA" "$PROFILE"; then
    echo "  -> Appending Pip & Homebrew mirrors to $PROFILE..."
    cat << 'EOF' >> "$PROFILE"

# OpenClaw Lean-Node Mirrors (TUNA)
export HOMEBREW_API_DOMAIN="https://mirrors.tuna.tsinghua.edu.cn/homebrew-bottles/api"
export HOMEBREW_BOTTLE_DOMAIN="https://mirrors.tuna.tsinghua.edu.cn/homebrew-bottles"
export HOMEBREW_BREW_GIT_REMOTE="https://mirrors.tuna.tsinghua.edu.cn/git/homebrew/brew.git"
export HOMEBREW_CORE_GIT_REMOTE="https://mirrors.tuna.tsinghua.edu.cn/git/homebrew/homebrew-core.git"
export PIP_INDEX_URL="https://pypi.tuna.tsinghua.edu.cn/simple"
EOF
else
    echo "  -> Mirrors already configured."
fi

# 3. Check for PM2 Daemon Manager (Lean-Node)
echo "[3/5] Checking PM2 Manager..."
if ! command -v pm2 &> /dev/null; then
    echo "  -> PM2 not found. Attempting to install via npm..."
    if command -v npm &> /dev/null; then
        npm install -g pm2
    else
        echo "  [!] npm not found. Please install Node.js first."
    fi
else
    echo "  -> PM2 is installed."
fi

# 4. Enforce Tailscale Network (Mesh-Route)
echo "[4/5] Checking Tailscale Connectivity..."
if command -v tailscale &> /dev/null; then
    TS_IP=$(tailscale ip -4)
    echo "  -> Tailscale IP: $TS_IP"
else
    echo "  [!] Tailscale CLI not found in PATH."
fi

# 5. Output Public Key for GPU Authorization
echo "[5/5] Provisioning Complete!"
echo "========================================"
echo "ACTION REQUIRED: Add the following public key to the GPU ~/.ssh/authorized_keys:"
cat ~/.ssh/id_ed25519.pub
echo "========================================"

echo "Please run 'source ~/.zshrc' to apply mirror modifications."
