#!/bin/bash
# ==============================================================================
# OMNI-SCHEDULER DAEMON LAUNCHER (Standard Operating Procedure)
# ==============================================================================
# This script ensures the scheduler daemon is launched with a fully initialized
# shell environment inherited from Conda, preventing "command not found" crashes
# when the daemon attempts to subprocess `conda run`.
# ==============================================================================

set -e

# 1. Source Conda directly to ensure `conda` command is available in subshells
source /root/miniconda3/etc/profile.d/conda.sh

# 2. Activate the dedicated orchestrator environment
conda activate pesso

# 3. Navigate to SSoT workspace
cd /jhdx0003008/workspace/projects_core

# 4. Standardized Launch Parameters
POLL_INTERVAL=300
QUEUE_FILE="/jhdx0003008/workspace/projects_core/experiment_queue.json"

echo "🚀 [Omni-Launcher] Bootstrapping auto_scheduler.py in tmux..."
echo " > Poll Interval : ${POLL_INTERVAL}s"
echo " > Queue File    : ${QUEUE_FILE}"

# 5. Kill existing session & rogue processes
tmux kill-session -t scheduler 2>/dev/null || true
pgrep -f "auto_scheduler.py" | grep -v $$ | xargs -r kill -9 || true

# 6. Spawn formal bash-wrapped tmux session to preserve PATH
tmux new-session -d -s scheduler -n daemon "bash -c 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate pesso && python auto_scheduler.py --mode local --poll ${POLL_INTERVAL} --queue ${QUEUE_FILE}'"

echo "✅ [Omni-Launcher] Daemon is online. Attach via 'tmux a -t scheduler'."
