#!/usr/bin/env python3
"""
Test IssueFixer integration with claude_wrapper.

This tests the full flow:
1. IssueFixer._fix_single_issue() calls ClaudeClient.query()
2. ClaudeClient sends JSON to claude_wrapper
3. Wrapper executes prompt
4. ClaudeClient parses events (should recognize 'run_completed' now)
5. GitVerifier checks for commit
"""

import sys
import tempfile
import subprocess
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from airflow_dags.autonomous_fixing.core.fixer import IssueFixer
from airflow_dags.autonomous_fixing.adapters.ai.claude_client import ClaudeClient
from airflow_dags.autonomous_fixing.adapters.git.git_verifier import GitVerifier

def setup_test_repo():
    """Create test git repo with an error to fix."""
    tmpdir = tempfile.mkdtemp()
    test_repo = Path(tmpdir)

    # Initialize git
    subprocess.run(["git", "init"], cwd=test_repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=test_repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=test_repo, check=True)

    # Create Python file with error
    test_file = test_repo / "example.py"
    test_file.write_text("# This file has a TODO\ndef hello():\n    # TODO: add docstring\n    print('hello')\n")

    # Initial commit
    subprocess.run(["git", "add", "."], cwd=test_repo, check=True)
    subprocess.run(["git", "commit", "-m", "Initial"], cwd=test_repo, check=True)

    return test_repo

def test_issue_fixer():
    """Test IssueFixer with ClaudeClient fix."""
    print("="*80)
    print("🧪 Testing IssueFixer Integration")
    print("="*80)

    # Setup test repo
    test_repo = setup_test_repo()
    print(f"📁 Test repo: {test_repo}")

    # Get initial commit
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=test_repo,
        capture_output=True,
        text=True
    )
    initial_commit = result.stdout.strip()
    print(f"📍 Initial commit: {initial_commit[:8]}")

    # Create config
    config = {
        'wrapper': {
            'path': str(Path(__file__).parent / 'claude_wrapper.py'),
            'python_executable': str(Path(__file__).parent.parent / '.venv' / 'bin' / 'python3')
        }
    }

    # Create IssueFixer (without debug logger to avoid clutter)
    fixer = IssueFixer(config, debug_logger=None)

    # Create test issue
    issue = {
        'project': str(test_repo),
        'language': 'python',
        'type': 'error',
        'file': 'example.py',
        'line': 3,
        'message': 'Add docstring to hello() function and remove TODO comment'
    }

    print("\n🔧 Testing fix...")
    print(f"  Issue: {issue['message']}")

    # Attempt fix (this calls ClaudeClient.query)
    success = fixer._fix_single_issue(issue)

    print(f"\n{'✅' if success else '❌'} Fix result: {'SUCCESS' if success else 'FAILED'}")

    # Check if commit was created
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=test_repo,
        capture_output=True,
        text=True
    )
    current_commit = result.stdout.strip()

    commit_created = (current_commit != initial_commit)
    print(f"{'✅' if commit_created else '❌'} Commit created: {commit_created}")

    if commit_created:
        # Show commit
        result = subprocess.run(
            ["git", "log", "-1", "--oneline"],
            cwd=test_repo,
            capture_output=True,
            text=True
        )
        print(f"  Commit: {result.stdout.strip()}")

    # Cleanup
    import shutil
    shutil.rmtree(test_repo)

    print("\n" + "="*80)
    if success and commit_created:
        print("✅ INTEGRATION TEST PASSED")
        print("  ✅ ClaudeClient handled events correctly")
        print("  ✅ Wrapper created commit")
        print("  ✅ GitVerifier detected commit")
    elif success and not commit_created:
        print("❌ INTEGRATION TEST FAILED")
        print("  ❌ ClaudeClient said success but no commit!")
        print("  This is the bug we're trying to fix.")
    else:
        print("❓ INTEGRATION TEST INCONCLUSIVE")
        print(f"  Fix success: {success}")
        print(f"  Commit created: {commit_created}")
    print("="*80)

    return success and commit_created

if __name__ == "__main__":
    try:
        success = test_issue_fixer()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n💥 Test crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
