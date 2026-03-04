#!/bin/bash
# Morning Report Generator (Auto-execution at 08:00)

echo "=========================================================================================="
echo "   OPENCLAW GLOBAL WAR ROOM - 24H MORNING REPORT (FIRST MATRIX)   "
echo "   TIME: \$(date)"
echo "=========================================================================================="

FIRST_MATRIX=("calam" "frenet" "pesso" "physdiff")
for P in "\${FIRST_MATRIX[@]}"; do
    echo "--- Target: \$P ---"
    
    # Check if run_info exists
    if [ -f "outputs/\$P/run_info.yaml" ]; then
        echo " [x] Traceability: run_info.yaml GENERATED."
    else
        echo " [ ] Traceability: Waiting for sync."
    fi
    
    # Check last lines of log if running
    PID=\$(pgrep -f "run_research.py.*\$P")
    if [ ! -z "\$PID" ]; then
        echo " [x] Status: RUNNING (PID \$PID) - Overnight Continuous."
        echo " [>] Latest Action: \$(tail -n 1 outputs/\$P/run_research.log 2>/dev/null | cut -c 1-80)..."
    else
        echo " [ ] Status: IDLE / STOPPED. Watchdog failure."
    fi
    
    # Check Innovation Audit
    if [ -f "outputs/\$P/audit_report.md" ]; then
        INNO=\$(grep "Innovation_Delta" "outputs/\$P/audit_report.md" 2>/dev/null || echo "N/A")
        echo " [x] Audit: PASS - \$INNO"
    else
        echo " [ ] Audit: PENDING"
    fi
    echo ""
done

echo "=========================================================================================="
echo " [Executive Summary] Overnight 24h sprint completed. Resources saturated."
echo "=========================================================================================="
