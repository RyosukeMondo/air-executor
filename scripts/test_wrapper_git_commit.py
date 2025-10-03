#!/usr/bin/env python3
"""
Test claude_wrapper git commit functionality.

This is the CRITICAL test - verifies that wrapper actually creates commits
when Claude says it succeeded. This is the issue the user identified.
"""

import subprocess
import json
import sys
import time
import tempfile
import shutil
from pathlib import Path

def run_command(cmd, cwd):
    """Run shell command and return output."""
    result = subprocess.run(
        cmd,
        shell=True,
        cwd=cwd,
        capture_output=True,
        text=True
    )
    return result.returncode, result.stdout, result.stderr

def test_wrapper_with_commit():
    """Test that wrapper actually creates git commits."""
    project_root = Path(__file__).parent.parent
    wrapper_path = project_root / "scripts" / "claude_wrapper.py"
    python = project_root / ".venv" / "bin" / "python3"

    print("="*80)
    print("🧪 Testing claude_wrapper Git Commit Functionality")
    print("="*80)
    print(f"Wrapper: {wrapper_path}")
    print(f"Python: {python}")
    print()

    # Create temporary git repo for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        test_repo = Path(tmpdir) / "test_project"
        test_repo.mkdir()

        print(f"📁 Test repo: {test_repo}")

        # Initialize git repo
        run_command("git init", test_repo)
        run_command("git config user.email 'test@example.com'", test_repo)
        run_command("git config user.name 'Test User'", test_repo)

        # Create a simple file
        test_file = test_repo / "example.py"
        test_file.write_text("def hello():\n    print('Hello, World!')\n")

        # Initial commit
        run_command("git add .", test_repo)
        run_command("git commit -m 'Initial commit'", test_repo)

        # Get initial commit
        rc, initial_commit, _ = run_command("git rev-parse HEAD", test_repo)
        initial_commit = initial_commit.strip()
        print(f"📍 Initial commit: {initial_commit[:8]}")

        # Build prompt that SHOULD create a commit
        prompt = """Make a small change to example.py:
1. Add a docstring to the hello() function
2. Save the file
3. Create a git commit with message: "docs: Add docstring to hello function"

IMPORTANT: You MUST create a git commit. This is required.
Run: git add . && git commit -m "docs: Add docstring to hello function"
"""

        # Build command
        command = {
            "action": "prompt",
            "prompt": prompt,
            "options": {
                "cwd": str(test_repo),
                "permission_mode": "bypassPermissions",
                "exit_on_complete": True
            }
        }

        print("\n📤 Sending command to wrapper...")
        print(f"  Prompt: Add docstring + create commit")

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
        print("\n📥 Wrapper events:")
        print("-"*80)

        try:
            timeout_time = time.time() + 120  # 2 minute timeout
            while time.time() < timeout_time:
                line = proc.stdout.readline()
                if not line:
                    break

                line = line.strip()
                if not line:
                    continue

                try:
                    event = json.loads(line)
                    event_type = event.get('event')
                    events.append(event)
                    print(f"  {event_type}")

                    # Stop on shutdown
                    if event_type in ['shutdown', 'auto_shutdown']:
                        break

                except json.JSONDecodeError:
                    pass

            # Kill if still running
            if proc.poll() is None:
                proc.kill()

            duration = time.time() - start

        except Exception as e:
            proc.kill()
            print(f"\n❌ Exception: {e}")
            return False

        print("-"*80)

        # Check wrapper result
        has_run_completed = any(e.get('event') == 'run_completed' for e in events)
        has_run_failed = any(e.get('event') == 'run_failed' for e in events)
        wrapper_claims_success = has_run_completed and not has_run_failed

        print(f"\n⏱️  Duration: {duration:.1f}s")
        print(f"🔚 Exit code: {proc.returncode}")
        print(f"{'✅' if wrapper_claims_success else '❌'} Wrapper claims success: {wrapper_claims_success}")

        # Now the CRITICAL check: Did a commit actually happen?
        rc, current_commit, _ = run_command("git rev-parse HEAD", test_repo)
        current_commit = current_commit.strip()

        commit_was_created = (current_commit != initial_commit)

        print(f"\n🔍 Git Verification:")
        print(f"  Initial commit: {initial_commit[:8]}")
        print(f"  Current commit: {current_commit[:8]}")
        print(f"  {'✅' if commit_was_created else '❌'} Commit created: {commit_was_created}")

        if commit_was_created:
            # Show commit details
            rc, commit_msg, _ = run_command("git log -1 --pretty=format:'%s'", test_repo)
            print(f"  Commit message: {commit_msg}")

            rc, files_changed, _ = run_command("git diff --name-only HEAD~1", test_repo)
            print(f"  Files changed: {files_changed.strip()}")

        # The CRITICAL test
        if wrapper_claims_success and not commit_was_created:
            print("\n" + "="*80)
            print("❌ CRITICAL FAILURE: Wrapper Claims Success but No Commit!")
            print("="*80)
            print("This is the exact issue the user reported:")
            print("  - claude_wrapper says 'run_completed'")
            print("  - But NO git commit was actually created")
            print("  - This causes the autonomous fixer to fail")
            print()
            print("Possible causes:")
            print("  1. Claude didn't actually create the commit")
            print("  2. Claude created commit in wrong directory")
            print("  3. Git command failed silently")
            print("  4. Permission issues")
            print("="*80)
            return False

        elif wrapper_claims_success and commit_was_created:
            print("\n" + "="*80)
            print("✅ TEST PASSED - Commit Verification Working!")
            print("="*80)
            print("Wrapper correctly:")
            print("  ✅ Executed the prompt")
            print("  ✅ Created git commit")
            print("  ✅ Reported success")
            print("="*80)
            return True

        else:
            print("\n" + "="*80)
            print("❓ INCONCLUSIVE - Wrapper Failed or Timeout")
            print("="*80)
            print(f"Wrapper claimed success: {wrapper_claims_success}")
            print(f"Commit was created: {commit_was_created}")
            print("\nThis might be OK if the prompt was too hard or timed out.")
            print("="*80)
            return False

if __name__ == "__main__":
    try:
        success = test_wrapper_with_commit()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n💥 Test crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
