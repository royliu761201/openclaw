#!/bin/bash
# Description: Minimal and safe network probe to verify topology and port reachability
# Usage: ./probe.sh <host> [port] [timeout_seconds]

TARGET=$1
PORT=${2:-22}
TIMEOUT=${3:-3}

if [ -z "$TARGET" ]; then
  echo "Usage: $0 <target_host_or_ip> [port] [timeout]"
  echo "Example: $0 node-02"
  echo "         $0 10.190.30.220 8080 5"
  exit 1
fi

echo "[net-probe] 🔍 Probing $TARGET on port $PORT (Timeout: ${TIMEOUT}s)..."

# Use native `nc` for TCP port probing
nc -z -G "$TIMEOUT" "$TARGET" "$PORT" 2>/dev/null
STATUS=$?

if [ $STATUS -eq 0 ]; then
  echo "[net-probe] ✅ SUCCESS: $TARGET:$PORT is reachable."
  exit 0
else
  echo "[net-probe] ❌ FAILURE: $TARGET:$PORT is unreachable or timed out."
  exit 1
fi
