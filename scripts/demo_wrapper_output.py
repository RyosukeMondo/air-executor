#!/usr/bin/env python3
"""
Demo script that simulates claude_wrapper.py output for testing watch_wrapper.py

Usage:
    python scripts/demo_wrapper_output.py | python scripts/watch_wrapper.py
"""

import json
import sys
import time
from datetime import datetime, timezone


def emit_event(event_type, **kwargs):
    """Emit a JSON event to stdout."""
    event = {"event": event_type, "timestamp": datetime.now(timezone.utc).isoformat(), **kwargs}
    print(json.dumps(event), flush=True)
    time.sleep(0.5)  # Simulate processing delay


def simulate_test_discovery():
    """Simulate a test discovery run."""
    run_id = "demo-run-001"

    # Wrapper ready
    emit_event("ready", state="ready", version=1, outcome="running", reason="boot", tags=[])

    # Run started
    emit_event("run_started", run_id=run_id, state="executing", options={})

    # Phase detected
    emit_event("phase_detected", run_id=run_id, phase="P1: Test Discovery")

    # Tool execution sequence
    tools = [
        ("Read", "package.json"),
        ("Bash", "npm test --listTests"),
        ("Glob", "**/*.test.js"),
        ("Read", "jest.config.js"),
        ("Bash", "npm test -- --dry-run"),
        ("Write", ".test-config.json"),
    ]

    for i, (tool, target) in enumerate(tools):
        # Tool started
        emit_event("tool_started", run_id=run_id, tool=tool, progress=f"{i}/{len(tools)}")

        # Simulate some stream events
        emit_event(
            "stream",
            run_id=run_id,
            payload={"message_type": "TextBlock", "text": f"Processing {target}..."},
        )

        # Tool completed
        emit_event("tool_completed", run_id=run_id, tool=tool, progress=f"{i+1}/{len(tools)}")

    # Final text output
    emit_event(
        "stream",
        run_id=run_id,
        payload={
            "message_type": "TextBlock",
            "text": "Test configuration successfully discovered and documented.",
        },
    )

    # Run completed
    emit_event("run_completed", run_id=run_id, version=1, outcome="completed", reason="ok", tags=[])

    # State change to idle
    emit_event("state", state="idle", last_session_id="session-abc123")

    # Shutdown
    time.sleep(1)
    emit_event(
        "shutdown",
        state="idle",
        last_session_id="session-abc123",
        version=1,
        outcome="shutdown",
        reason="graceful",
        tags=[],
    )


if __name__ == "__main__":
    try:
        print("# Starting demo wrapper output simulation...", file=sys.stderr)
        print("# Pipe this to watch_wrapper.py to see the live dashboard", file=sys.stderr)
        print(
            "# Example: python scripts/demo_wrapper_output.py | python scripts/watch_wrapper.py",
            file=sys.stderr,
        )
        print("", file=sys.stderr)
        time.sleep(1)

        simulate_test_discovery()

        print("\n# Demo completed!", file=sys.stderr)
    except KeyboardInterrupt:
        print("\n# Demo interrupted", file=sys.stderr)
    except Exception as e:
        print(f"\n# Demo error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc(file=sys.stderr)
