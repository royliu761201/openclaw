#!/bin/bash
# OpenClaw Research Core: Standardized Action Scripts for Research Teams
# Ensures alignment with Data & Exp Standard (v1.0)

COMMAND=$1
shift

case $COMMAND in
  "init")
    # Initialize directory structure on local node
    PROJECT_NAME=$1
    if [ -z "$PROJECT_NAME" ]; then echo "Usage: research-core init <project_name>"; exit 1; fi
    
    echo "🏗️ Initializing standard environment for $PROJECT_NAME..."
    if [ -d "/jxdxxxx" ]; then
        BASE="/jxdxxxx/openclaw_data/experiments/$PROJECT_NAME"
        mkdir -p "$BASE"
        ln -sfn "$BASE" outputs
        echo "✅ Hard storage linked: outputs -> $BASE"
    else
        mkdir -p outputs
        echo "⚠️ /jxdxxxx not found. Using local outputs/."
    fi
    ;;
    
  "trace")
    # Generate run_info.yaml
    EXP_ID=$1
    DATA_ID=$2
    if [ -z "$EXP_ID" ]; then echo "Usage: research-core trace <exp_id> <dataset_id>"; exit 1; fi
    
    cat <<EOF > outputs/run_info.yaml
experiment_id: $EXP_ID
timestamp: $(date +"%Y-%m-%d %H:%M:%S")
git_commit: $(git rev-parse --short HEAD 2>/dev/null || echo "no_git")
dataset_id: ${DATA_ID:-"unknown"}
hardware: $(hostname)
status: "started"
EOF
    echo "📝 run_info.yaml generated."
    ;;
    
  "vault-sync")
    # Sync outputs to Mac 03 Vault
    PROJECT_NAME=$1
    if [ -z "$PROJECT_NAME" ]; then echo "Usage: research-core vault-sync <project_name>"; exit 1; fi
    echo "🏦 Syncing to Mac 03 Vault..."
    rsync -avz --checksum outputs/ roy-003:~/openclaw_data/archive/$(date +%Y-%m-%d)_$PROJECT_NAME/
    ;;

  *)
    echo "Commands: init, trace, vault-sync"
    ;;
esac
