#!/usr/bin/env python3
"""
Test claude_wrapper directly to see stderr and understand why no stream events.
"""

import subprocess
import json
import sys
from pathlib import Path

def test_wrapper_direct():
    """Run wrapper and capture ALL output."""
    project_root = Path(__file__).parent.parent
    wrapper_path = project_root / "scripts" / "claude_wrapper.py"
    python = project_root / ".venv" / "bin" / "python3"

    print("Testing claude_wrapper directly...")
    print(f"Wrapper: {wrapper_path}")
    print(f"Python: {python}")
    print()

    # Simple prompt
    command = {
        "action": "prompt",
        "prompt": "Say 'Hello' and create a file called test.txt with 'hello' in it. Then run: git add test.txt && git commit -m 'test'",
        "options": {
            "cwd": str(project_root),
            "permission_mode": "bypassPermissions",
            "exit_on_complete": True
        }
    }

    # Run wrapper
    proc = subprocess.Popen(
        [str(python), str(wrapper_path)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Send command
    stdin_data = json.dumps(command) + "\n"
    stdout, stderr = proc.communicate(input=stdin_data, timeout=30)

    print("="*80)
    print("STDOUT:")
    print("="*80)
    print(stdout)

    print("\n" + "="*80)
    print("STDERR:")
    print("="*80)
    print(stderr)

    print("\n" + "="*80)
    print(f"Exit code: {proc.returncode}")
    print("="*80)

    # Parse events
    print("\nEvents received:")
    for line in stdout.strip().split('\n'):
        if line.strip():
            try:
                event = json.loads(line)
                print(f"  - {event.get('event')}")
            except:
                pass

if __name__ == "__main__":
    test_wrapper_direct()
