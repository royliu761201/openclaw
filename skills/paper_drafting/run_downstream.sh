#!/bin/bash
# Downstream Paper Pipeline
# Boss-Friendly 1-Click Execution

PAPER_PATH=$1
PROJECT_NAME=$2
BOARD_PATH="/Users/roy-jd/workspace/docs/projects_pdca/00_CORE_EXPERIMENTS_DASHBOARD.md"
SKILL_DIR="/Users/roy-jd/openclaw/skills/paper_drafting/scripts"

if [ -z "$PAPER_PATH" ] || [ -z "$PROJECT_NAME" ]; then
    echo "Usage: $0 <path_to_paper_file> <project_name: PhysDiff|CaLaM|Frenet|PESSO>"
    echo "Example: $0 ~/workspace/papers/calam/calam.tex CaLaM"
    exit 1
fi

echo "======================================================"
echo "🚀 Initiating Downstream Paper Review Pipeline"
echo "Target: $PAPER_PATH ($PROJECT_NAME)"
echo "======================================================"

echo ""
echo "==== 1. Executing Style Polisher ===="
python3 $SKILL_DIR/style_polisher.py --paper "$PAPER_PATH"

echo ""
echo "==== 2. Executing Visual Metric Review ===="
python3 $SKILL_DIR/visual_reviewer.py --paper "$PAPER_PATH" --board "$BOARD_PATH" --project "$PROJECT_NAME"

echo ""
echo "======================================================"
echo "🏁 Pipeline Execution Complete"
echo "======================================================"
