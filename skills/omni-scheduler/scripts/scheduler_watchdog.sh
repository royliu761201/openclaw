#!/bin/bash
# -----------------------------------------------------------------------------
# Omni-Scheduler Watchdog (Auto-Heal Sentinel)
# Usage: nohup bash scheduler_watchdog.sh > watchdog.log 2>&1 &
# -----------------------------------------------------------------------------

set -e

WORKSPACE_DIR="/jhdx0003008/workspace"
SCHEDULER_SCRIPT="${WORKSPACE_DIR}/openclaw/skills/omni-scheduler/scripts/auto_scheduler.py"
LOG_FILE="/root/auto_scheduler_daemon_new.log"
POLL_INTERVAL=60

if [ ! -d "${WORKSPACE_DIR}" ]; then
    echo "[Watchdog] CRITICAL: Workspace ${WORKSPACE_DIR} not found. Watchdog terminating."
    exit 1
fi

echo "[Watchdog] Starting Omni-Scheduler Sentinel in infinite loop mode..."

while true; do
    # Check if the process is running
    if ! pgrep -f "python3 ${SCHEDULER_SCRIPT}" > /dev/null; then
        echo "[Watchdog] $(date): Scheduler is DEAD. Initiating Auto-Heal restart..."
        # Respawn the scheduler
        export PYTHONPATH="${WORKSPACE_DIR}:${PYTHONPATH}"
        nohup python3 "${SCHEDULER_SCRIPT}" --poll ${POLL_INTERVAL} >> "${LOG_FILE}" 2>&1 &
        echo "[Watchdog] $(date): Scheduler successfully respawned."
    fi
    
    # Sleep before next health check
    sleep 30
done
