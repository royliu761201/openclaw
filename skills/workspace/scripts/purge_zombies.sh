#!/bin/bash
# GPU Zombie Purger Execution Script

TARGET_HOST=$1
PORT=${2:-22}
SSH_USER=${3:-root}

if [ -z "$TARGET_HOST" ]; then
    echo "Usage: $0 <TARGET_HOST> [PORT] [USER]"
    echo "Example: $0 10.190.30.220 30305 root"
    exit 1
fi

echo "🚀 [GPU-Zombie-Purger] Initiating deep scan and purge on $TARGET_HOST:$PORT..."
echo "🛠️ Target User Context: $SSH_USER"

# Payload: Gracefully handles 'No process found' without failing the script via || true
PAYLOAD="
echo '=== Killing PyTorch Dynamo compile_workers ===' ;
pkill -9 -u \$USER -f compile_worker || true ;

echo '=== Killing orphaned W&B cores ===' ;
pkill -9 -u \$USER -f wandb-core || true ;

echo '=== Sweeping remaining ghost Python handles ===' ;
pkill -9 -u \$USER -f python || true ;

echo '=== Verifying VRAM Teardown ===' ;
nvidia-smi
"

ssh -p "$PORT" -o ConnectTimeout=10 "$SSH_USER@$TARGET_HOST" "$PAYLOAD"

echo "✅ [GPU-Zombie-Purger] Purge payload executed. Ensure target VRAM reflects 1MiB usage."
