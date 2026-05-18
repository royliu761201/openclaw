#!/bin/bash
# CodeX CLI: Safe Thread Resume Protocol

THREAD_ID=$1
PROMPT_FILE=$2
OUTPUT_REPORT=$3

if [ -z "$THREAD_ID" ] || [ -z "$PROMPT_FILE" ] || [ -z "$OUTPUT_REPORT" ]; then
    echo "Usage: $0 <thread_id> <prompt_file> <output_report_file>"
    echo "Example: $0 019d4102-xxx /tmp/prompt.txt /tmp/out.md"
    exit 1
fi

if [ ! -f "$PROMPT_FILE" ]; then
    echo "Error: Prompt file not found at $PROMPT_FILE"
    exit 1
fi

echo "🚀 [Codex-Safe-Resume] Targeting precise historical session context..."
echo "  - Target ID: $THREAD_ID"
echo "  - Prompt File: $PROMPT_FILE"
echo "  - Output append: $OUTPUT_REPORT"

# Execute codex headless RESUME targeting the explicit THREAD_ID.
# Do NOT use -C or --color parameters as resume natively inherits them safely.
codex exec resume "$THREAD_ID" \
  --dangerously-bypass-approvals-and-sandbox \
  --json \
  -o "$OUTPUT_REPORT" \
  "$(cat "$PROMPT_FILE")" \
  >> /tmp/codex_events_solidified_${THREAD_ID}.jsonl 2>&1 &
  
CODEX_PID=$!
echo "✅ [Codex-Safe-Resume] Follow-up Agent deployed successfully!"
echo "  - PID: $CODEX_PID"
echo "  - JSON Log: /tmp/codex_events_solidified_${THREAD_ID}.jsonl"
