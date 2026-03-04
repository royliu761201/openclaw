#!/bin/bash
# robust_tunnel.sh - Auto-healing SSH Tunnel Watchdog

PROXY="nc -x 100.108.106.119:1080 %h %p"
DEST="root@10.190.30.220"
PORT="30305"
PASS="sdYcl\$YyzOmv0AdOd?biUYPc^@096s%u"

echo "[Watchdog] Starting auto-healing tunnel..."

while true; do
    echo "[Watchdog] Initiating SSH connection at $(date)..."
    # ExitOnForwardFailure ensures the process dies if ports are taken
    # ServerAliveInterval sends a ping every 10s to keep NAT/firewalls open
    /opt/homebrew/bin/sshpass -p 'sdYcl$YyzOmv0AdOd?biUYPc^@096s%u' /usr/bin/ssh -N \
        -p $PORT \
        -o StrictHostKeyChecking=no \
        -o UserKnownHostsFile=/dev/null \
        -o "ProxyCommand=$PROXY" \
        -o ServerAliveInterval=10 \
        -o ServerAliveCountMax=3 \
        -o ExitOnForwardFailure=yes \
        -L 127.0.0.1:18100:127.0.0.1:8100 \
        -L 127.0.0.1:18200:127.0.0.1:8200 \
        $DEST

    EXIT_CODE=$?
    echo "[Watchdog] Tunnel collapsed with exit code $EXIT_CODE. Respawning in 3 seconds..."
    sleep 3
done
