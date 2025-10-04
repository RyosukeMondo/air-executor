#!/bin/bash
# Test script to verify wrapper monitoring works
# Run this to diagnose issues with the monitoring system

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo "🧪 Testing Wrapper Monitor System"
echo "=================================="
echo ""

# Test 1: Check if rich is installed
echo "[1/5] Checking rich library..."
if .venv/bin/python3 -c "import rich" 2>/dev/null; then
    echo "✅ Rich library installed"
else
    echo "❌ Rich library not found"
    echo "   Install with: pip install rich"
    exit 1
fi
echo ""

# Test 2: Check if log directory exists
echo "[2/5] Checking log directory..."
if [ -d "logs" ]; then
    echo "✅ logs/ directory exists"
else
    echo "⚠️  Creating logs/ directory"
    mkdir -p logs
fi
echo ""

# Test 3: Test monitor can parse events
echo "[3/5] Testing event parsing..."
cat > /tmp/test_events.jsonl << 'EOF'
{"event": "ready", "timestamp": "2025-10-04T09:00:00.000000Z", "state": "idle", "version": 1}
{"event": "run_started", "run_id": "test-123", "timestamp": "2025-10-04T09:00:01.000000Z", "state": "executing"}
{"event": "phase_detected", "timestamp": "2025-10-04T09:00:02.000000Z", "run_id": "test-123", "phase": "P1: Test Phase"}
{"event": "run_completed", "timestamp": "2025-10-04T09:00:10.000000Z", "run_id": "test-123", "reason": "ok"}
{"event": "shutdown", "timestamp": "2025-10-04T09:00:11.000000Z"}
EOF

if timeout 2 cat /tmp/test_events.jsonl | .venv/bin/python3 scripts/watch_wrapper.py > /dev/null 2>&1; then
    echo "✅ Monitor can parse events"
else
    echo "❌ Monitor failed to parse events"
    exit 1
fi
echo ""

# Test 4: Test tail -F works
echo "[4/5] Testing tail -F with log truncation..."
TEST_LOG="/tmp/test_tail_truncation.log"
> "$TEST_LOG"

# Start tail -F
timeout 5 tail -F "$TEST_LOG" > /tmp/tail_test_output.txt 2>&1 &
TAIL_PID=$!

sleep 1
echo "line1" >> "$TEST_LOG"
sleep 0.5
> "$TEST_LOG"  # Truncate
sleep 0.5
echo "line2" >> "$TEST_LOG"
sleep 1

kill $TAIL_PID 2>/dev/null || true

if grep -q "line2" /tmp/tail_test_output.txt; then
    echo "✅ tail -F handles file truncation"
else
    echo "❌ tail -F failed to handle truncation"
    exit 1
fi
echo ""

# Test 5: Verify log file can be written
echo "[5/5] Testing log file write..."
if touch logs/wrapper-realtime.log 2>/dev/null; then
    echo "✅ Can write to logs/wrapper-realtime.log"
else
    echo "❌ Cannot write to logs/wrapper-realtime.log"
    exit 1
fi
echo ""

echo "=================================="
echo "✅ All tests passed!"
echo ""
echo "To use the monitor:"
echo "  Terminal 1: ./scripts/monitor.sh"
echo "  Terminal 2: ./scripts/autonomous_fix.sh config/projects/warps.yaml"
echo ""
echo "Note: The monitor requires a real terminal (TTY) to display the dashboard."
echo "      It will not work when output is redirected to a file."
