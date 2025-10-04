#!/usr/bin/env python3
"""
Test script to verify claude_wrapper.py works correctly.

This script simulates what the Airflow DAG does:
1. Start claude_wrapper.py
2. Send a prompt
3. Collect the response
"""

import subprocess
import json
import sys
from pathlib import Path


def _send_prompt_command(process):
    """Send a prompt command to the wrapper process."""
    command = {
        "action": "prompt",
        "prompt": "Say 'Hello from Airflow test!' and nothing else",
        "options": {
            "exit_on_complete": True,
            "permission_mode": "bypassPermissions",
        }
    }
    process.stdin.write(json.dumps(command) + "\n")
    process.stdin.flush()


def _extract_stream_text(payload, conversation):
    """Extract and collect text from stream event payload."""
    # Extract text content from content array
    content = payload.get("content", [])
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text = item.get("text", "")
                if text:
                    conversation.append(text)
                    print(f"💬 {text}")

    # Extract direct text field
    if payload.get("text"):
        text = payload["text"]
        conversation.append(text)
        print(f"💬 {text}")


def _handle_event(event, process, conversation):
    """Handle a single event from the wrapper. Returns True if should break loop."""
    event_type = event.get("event")
    print(f"📨 {event_type}")

    if event_type == "ready":
        print("✅ Wrapper ready! Sending prompt...")
        _send_prompt_command(process)
        return False

    if event_type == "stream":
        _extract_stream_text(event.get("payload", {}), conversation)
        return False

    if event_type == "run_completed":
        print("✅ Run completed!")
        return False

    if event_type == "run_failed":
        error = event.get("error", "Unknown")
        print(f"❌ Failed: {error}")
        return True

    if event_type == "shutdown":
        print("✅ Shutdown")
        return True

    return False


def _process_wrapper_output(process, conversation):
    """Process output from wrapper and collect conversation."""
    for line in process.stdout:
        if not line.strip():
            continue

        try:
            event = json.loads(line)
            should_break = _handle_event(event, process, conversation)
            if should_break:
                break
        except json.JSONDecodeError:
            print(f"⚠️  Non-JSON: {line.strip()}")


def _check_result(process, conversation):
    """Check process result and print output."""
    return_code = process.wait(timeout=60)

    print("\n" + "="*60)
    if return_code == 0:
        print("✅ TEST PASSED")
        print("="*60)
        print("Response:")
        print("\n".join(conversation))
        print("="*60)
        return True

    stderr = process.stderr.read()
    print(f"❌ TEST FAILED (exit code: {return_code})")
    print(f"stderr: {stderr}")
    return False


def test_claude_wrapper():
    """Test the claude_wrapper.py with a simple prompt."""
    project_root = Path(__file__).parent.parent
    wrapper_path = project_root / "scripts" / "claude_wrapper.py"
    venv_python = project_root / ".venv" / "bin" / "python"

    print("🧪 Testing claude_wrapper.py")
    print("="*60)
    print(f"Wrapper: {wrapper_path}")
    print(f"Python: {venv_python}")
    print("="*60)

    # Start wrapper
    print("\n🚀 Starting wrapper...")
    process = subprocess.Popen(
        [str(venv_python), str(wrapper_path)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    conversation = []

    try:
        _process_wrapper_output(process, conversation)
        return _check_result(process, conversation)

    except subprocess.TimeoutExpired:
        process.kill()
        print("❌ TEST FAILED: Timeout")
        return False

    except Exception as e:
        process.kill()
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_claude_wrapper()
    sys.exit(0 if success else 1)
