#!/bin/bash
# Monitor wrapper execution in real-time
# Usage: ./scripts/monitor.sh [--project /path/to/project]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Parse arguments
PROJECT_ROOT=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --project)
            PROJECT_ROOT="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--project /path/to/project]"
            exit 1
            ;;
    esac
done

# Default to current directory if not specified
if [ -z "$PROJECT_ROOT" ]; then
    PROJECT_ROOT="$(pwd)"
fi

# Ensure absolute path
PROJECT_ROOT="$(cd "$PROJECT_ROOT" && pwd)"

# Ensure log directory exists
mkdir -p logs

# Touch the log file to ensure it exists for tail -f
touch logs/wrapper-realtime.log

# Write a startup marker to the log
echo '{"event":"monitor_ready","timestamp":"'$(date -u +%Y-%m-%dT%H:%M:%S)'Z","message":"Monitor started - waiting for wrapper events"}' >> logs/wrapper-realtime.log

echo "🔍 Monitoring wrapper execution..."
echo "   Log file: logs/wrapper-realtime.log"
echo "   Filtering: $PROJECT_ROOT"
echo "   Python: $PYTHON_EXEC"
echo ""
echo "📋 Waiting for wrapper events..."
echo "   (Run autonomous iteration script in another terminal)"
echo ""

# Export cwd for watch_wrapper to filter by current project
export MONITOR_CWD="$PROJECT_ROOT"

# Use air-executor's venv (where monitor script lives)
PYTHON_EXEC="$SCRIPT_DIR/../.venv/bin/python3"

if [ ! -f "$PYTHON_EXEC" ]; then
    echo "❌ Error: Python venv not found at $PYTHON_EXEC"
    echo "   Run: cd $(dirname $SCRIPT_DIR) && python3 -m venv .venv && .venv/bin/pip install rich"
    exit 1
fi

# Start monitoring (show last 100 lines for context, then follow new lines)
# This ensures we catch ready/run_started events even if monitor starts late
(tail -n 100 logs/wrapper-realtime.log; tail -F logs/wrapper-realtime.log) | "$PYTHON_EXEC" "$SCRIPT_DIR/watch_wrapper.py"
