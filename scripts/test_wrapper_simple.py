#!/usr/bin/env python3
"""
Simple test to verify claude_wrapper responds correctly.
Tests the actual JSON protocol without expecting git commits.
"""

import subprocess
import json
import sys
import time
from pathlib import Path

def test_wrapper_basic():
    """Test basic wrapper functionality."""
    project_root = Path(__file__).parent.parent
    wrapper_path = project_root / "scripts" / "claude_wrapper.py"
    python = project_root / ".venv" / "bin" / "python3"

    print("="*80)
    print("🧪 Testing claude_wrapper Basic Functionality")
    print("="*80)
    print(f"Wrapper: {wrapper_path}")
    print(f"Python: {python}")

    # Build command
    command = {
        "action": "prompt",
        "prompt": "Say 'Test successful' and nothing else",
        "options": {
            "cwd": str(project_root),
            "permission_mode": "bypassPermissions",
            "exit_on_complete": True
        }
    }

    print("\n📤 Sending command:")
    print(json.dumps(command, indent=2))

    # Run wrapper
    start = time.time()
    proc = subprocess.Popen(
        [str(python), str(wrapper_path)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Send command
    command_json = json.dumps(command) + "\n"
    proc.stdin.write(command_json)
    proc.stdin.flush()

    # Collect events
    events = []
    response_text = []

    print("\n📥 Received events:")
    print("-"*80)

    try:
        for line in proc.stdout:
            line = line.strip()
            if not line:
                continue

            try:
                event = json.loads(line)
                event_type = event.get('event')
                events.append(event)

                # Print event summary
                print(f"  {event_type}")

                # Extract response text
                if event_type == 'stream':
                    payload = event.get('payload', {})
                    content = payload.get('content', [])
                    if isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict) and item.get('type') == 'text':
                                text = item.get('text', '')
                                if text:
                                    response_text.append(text)

                # Stop on shutdown
                if event_type in ['shutdown', 'auto_shutdown']:
                    break

            except json.JSONDecodeError as e:
                print(f"  ⚠️  JSON error: {e}")
                print(f"  Line: {line[:100]}")

        # Wait for process
        proc.wait(timeout=10)
        duration = time.time() - start

    except subprocess.TimeoutExpired:
        proc.kill()
        print("\n❌ TIMEOUT after 10s")
        return False

    print("-"*80)

    # Analyze results
    print(f"\n⏱️  Duration: {duration:.1f}s")
    print(f"📊 Total events: {len(events)}")
    print(f"🔚 Exit code: {proc.returncode}")

    # Check for critical events
    has_ready = any(e.get('event') == 'ready' for e in events)
    has_run_started = any(e.get('event') == 'run_started' for e in events)
    has_run_completed = any(e.get('event') == 'run_completed' for e in events)
    has_shutdown = any(e.get('event') in ['shutdown', 'auto_shutdown'] for e in events)
    has_error = any(e.get('event') == 'run_failed' for e in events)

    print(f"\n✅ Event checklist:")
    print(f"  {'✓' if has_ready else '✗'} ready")
    print(f"  {'✓' if has_run_started else '✗'} run_started")
    print(f"  {'✓' if has_run_completed else '✗'} run_completed")
    print(f"  {'✓' if has_shutdown else '✗'} shutdown")
    print(f"  {'✗' if has_error else '✓'} no errors")

    if response_text:
        print(f"\n💬 Response:")
        print("  " + " ".join(response_text))

    # Determine success
    success = (
        proc.returncode == 0 and
        has_ready and
        has_run_started and
        has_run_completed and
        has_shutdown and
        not has_error
    )

    print("\n" + "="*80)
    if success:
        print("✅ TEST PASSED - Wrapper is working correctly")
    else:
        print("❌ TEST FAILED - Wrapper has issues")
        print("\n🔍 Event details:")
        for event in events:
            print(f"  {json.dumps(event, indent=4)}")
    print("="*80)

    return success

if __name__ == "__main__":
    success = test_wrapper_basic()
    sys.exit(0 if success else 1)
