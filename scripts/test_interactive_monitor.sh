#!/bin/bash
# Test script for interactive monitor with sample events

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "🧪 Testing Interactive Wrapper Monitor"
echo ""
echo "This will send sample events to test the new interactive features:"
echo "  - Split header layout (state/phase/runtime | stats)"
echo "  - Event list with selection cursor (▶)"
echo "  - Event detail panel with JSON syntax highlighting"
echo "  - Keyboard navigation (↑/↓ or j/k keys)"
echo "  - Press 'q' to quit"
echo ""
echo "Press Enter to start..."
read

# Generate sample events
(
    # Monitor ready
    echo '{"event":"monitor_ready","timestamp":"'$(date -u +%Y-%m-%dT%H:%M:%S)'Z","message":"Monitor started"}'
    sleep 0.5

    # Run started
    echo '{"event":"run_started","timestamp":"'$(date -u +%Y-%m-%dT%H:%M:%S)'Z","run_id":"test-123"}'
    sleep 0.5

    # Tool use events
    echo '{"event":"stream","timestamp":"'$(date -u +%Y-%m-%dT%H:%M:%S)'Z","payload":{"message_type":"AssistantMessage","content":[{"name":"Read","id":"tool1","input":{"file_path":"/test/file.py"}}]}}'
    sleep 0.3

    echo '{"event":"stream","timestamp":"'$(date -u +%Y-%m-%dT%H:%M:%S)'Z","payload":{"message_type":"UserMessage","content":[{"tool_use_id":"tool1","content":"file content here","is_error":false}]}}'
    sleep 0.3

    echo '{"event":"stream","timestamp":"'$(date -u +%Y-%m-%dT%H:%M:%S)'Z","payload":{"message_type":"AssistantMessage","content":[{"name":"Edit","id":"tool2","input":{"file_path":"/test/file.py","old_string":"x = 1","new_string":"x = 2"}}]}}'
    sleep 0.3

    echo '{"event":"stream","timestamp":"'$(date -u +%Y-%m-%dT%H:%M:%S)'Z","payload":{"message_type":"UserMessage","content":[{"tool_use_id":"tool2","content":"edit successful","is_error":false}]}}'
    sleep 0.3

    # Text response
    echo '{"event":"stream","timestamp":"'$(date -u +%Y-%m-%dT%H:%M:%S)'Z","payload":{"message_type":"AssistantMessage","content":[{"text":"I'\''ve updated the file successfully. The variable x is now set to 2."}]}}'
    sleep 0.5

    # Completion
    echo '{"event":"run_completed","timestamp":"'$(date -u +%Y-%m-%dT%H:%M:%S)'Z","reason":"ok","outcome":"success"}'
    sleep 1

    # More events to test scrolling
    for i in {1..15}; do
        echo '{"event":"stream","timestamp":"'$(date -u +%Y-%m-%dT%H:%M:%S)'Z","payload":{"message_type":"AssistantMessage","content":[{"text":"Event '$i' - testing event scrolling and navigation"}]}}'
        sleep 0.2
    done

    # Keep feeding events slowly to test live updates
    while true; do
        sleep 2
        echo '{"event":"stream","timestamp":"'$(date -u +%Y-%m-%dT%H:%M:%S)'Z","payload":{"message_type":"AssistantMessage","content":[{"text":"Periodic event - monitor is still running"}]}}'
    done
) | .venv/bin/python3 scripts/watch_wrapper.py
