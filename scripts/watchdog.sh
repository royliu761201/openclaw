#!/bin/bash
# OpenClaw Watchdog: Auto-Self-Healing for Research Processes
# Usage: bash scripts/watchdog.sh <process_pattern> <check_interval_seconds>

PATTERN=$1
INTERVAL=${2:-180}

echo "🛡️ Watchdog active for: $PATTERN (Check every ${INTERVAL}s)"

while true; do
  # Check if process is running
  PID=$(pgrep -f "$PATTERN")
  
  if [ -z "$PID" ]; then
    echo "⚠️ Process '$PATTERN' not found. 24h Resilience triggered: Restarting..."
    # Notify user via OpenClaw notification system if possible
    # Add project-specific restart logic here
  else
    # Check for I/O activity (optional but recommended in Manifesto)
    # If no IO growth in 3 minutes -> pkill and restart
    echo "✅ Process $PATTERN (PID: $PID) is pulse-alive."
  fi
  
  sleep $INTERVAL
done
