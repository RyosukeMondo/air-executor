#!/bin/bash
# Sync claude_wrapper.py to Airflow scripts directory

set -e

PROJECT_ROOT="/home/rmondo/repos/air-executor"
AIRFLOW_SCRIPTS="/home/rmondo/airflow/scripts"

echo "📦 Syncing claude_wrapper.py to Airflow"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Create directory if needed
mkdir -p "$AIRFLOW_SCRIPTS"

# Copy wrapper
cp "$PROJECT_ROOT/scripts/claude_wrapper.py" "$AIRFLOW_SCRIPTS/"
chmod +x "$AIRFLOW_SCRIPTS/claude_wrapper.py"

echo "✅ Copied: claude_wrapper.py"
echo "   From: $PROJECT_ROOT/scripts/"
echo "   To:   $AIRFLOW_SCRIPTS/"
echo ""
echo "✅ Sync complete!"
