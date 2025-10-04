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
echo ""
echo "📋 Waiting for wrapper events..."
echo "   (Run './scripts/autonomous_fix.sh config/...' in another terminal)"
echo ""

# Start monitoring (tail -F follows by name and handles file truncation)
tail -F logs/wrapper-realtime.log | .venv/bin/python3 scripts/watch_wrapper.py
