#!/bin/bash
# Monitor wrapper execution in real-time
# Usage: ./scripts/monitor.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# Ensure log directory exists
mkdir -p logs

# Touch the log file to ensure it exists for tail -f
touch logs/wrapper-realtime.log

# Write a startup marker to the log
echo '{"event":"monitor_ready","timestamp":"'$(date -u +%Y-%m-%dT%H:%M:%S)'Z","message":"Monitor started - waiting for wrapper events"}' >> logs/wrapper-realtime.log

echo "🔍 Monitoring wrapper execution..."
echo "   Log file: logs/wrapper-realtime.log"
echo "   Filtering: $PROJECT_ROOT"
echo ""
echo "📋 Waiting for wrapper events..."
echo "   (Run './scripts/autonomous_fix.sh config/...' in another terminal)"
echo ""

# Export cwd for watch_wrapper to filter by current project
export MONITOR_CWD="$PROJECT_ROOT"

# Start monitoring (show last 100 lines for context, then follow new lines)
# This ensures we catch ready/run_started events even if monitor starts late
(tail -n 100 logs/wrapper-realtime.log; tail -F logs/wrapper-realtime.log) | .venv/bin/python3 scripts/watch_wrapper.py
