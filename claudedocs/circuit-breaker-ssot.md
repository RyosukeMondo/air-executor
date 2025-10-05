# Circuit Breaker & Progress Tracking - Single Source of Truth

## Overview

Unified git-based progress detection and circuit breaker logic across all orchestrators.

**SSOT Module**: `airflow_dags/common/progress_tracker.py`

## Architecture

```
airflow_dags/
├── common/
│   ├── __init__.py
│   └── progress_tracker.py          # ⭐ SSOT for progress tracking
├── simple_autonomous_iteration/
│   └── simple_orchestrator.py       # ✓ Uses ProgressTracker
└── autonomous_fixing/
    └── adapters/git/
        └── git_verifier.py          # ✓ Compatibility wrapper around ProgressTracker
```

## Core Functionality

### ProgressTracker Class

```python
from airflow_dags.common.progress_tracker import ProgressTracker

tracker = ProgressTracker(
    project_path="/path/to/repo",
    circuit_breaker_threshold=3,
    require_git_changes=True
)

# Check for progress (new commits OR uncommitted changes)
has_progress, msg = tracker.check_progress()
# Returns: (True, "New commit detected: abc12345 (was def67890)")

# Check circuit breaker
should_abort, reason = tracker.should_trigger_circuit_breaker()
# Returns: (False, "Circuit breaker OK (1/3 iterations without progress)")
```

### Detection Strategy

**Dual Detection System**:
1. **Commit ID comparison** (primary, most reliable)
   - Uses `git rev-parse HEAD`
   - Detects when work is committed

2. **Diff hash comparison** (secondary)
   - Uses `git diff HEAD` + MD5 hash
   - Detects work in progress (uncommitted)

### Why This Fixed the Bug

**Previous Bug** (simple_orchestrator.py only):
```
Iteration 1: work → commit → git diff empty → hash B
Iteration 2: work → commit → git diff empty → hash B (SAME!)
Circuit breaker: "No changes detected" ❌ (FALSE POSITIVE)
```

**Fixed Behavior**:
```
Iteration 1: baseline commit abc12345
Iteration 2: work → commit def67890 → "New commit detected" ✓
Iteration 3: work → commit xyz11111 → "New commit detected" ✓
```

## Usage Patterns

### Pattern 1: Simple Orchestrator (New Code)

```python
from common.progress_tracker import ProgressTracker

class SimpleOrchestrator:
    def __init__(self, config):
        self._progress_tracker = ProgressTracker(
            project_path=self.project_path,
            circuit_breaker_threshold=config.circuit_breaker_threshold,
            require_git_changes=config.require_git_changes,
        )

    def run(self):
        for iteration in range(self.max_iterations):
            # ... execute iteration ...

            # Check progress
            has_progress, msg = self._progress_tracker.check_progress()
            print(f"📝 Progress check: {msg}")

            # Check circuit breaker
            should_abort, reason = self._progress_tracker.should_trigger_circuit_breaker()
            if should_abort:
                print(f"❌ {reason}")
                break
```

### Pattern 2: GitVerifier (Backward Compatibility)

```python
from airflow_dags.autonomous_fixing.adapters.git.git_verifier import GitVerifier

# Still works! (now a wrapper around ProgressTracker)
verifier = GitVerifier()

before = verifier.get_head_commit(project_path)
# ... do work ...
result = verifier.verify_commit_made(project_path, before, "fix")

if result["verified"]:
    print(f"Commit made: {result['new_commit']}")
```

### Pattern 3: Direct Usage (Recommended for New Code)

```python
from airflow_dags.common.progress_tracker import ProgressTracker

# One-off commit verification
tracker = ProgressTracker("/path/to/repo")

before = tracker.get_current_commit_id()
# ... do work ...
after = tracker.get_current_commit_id()

if after != before:
    print(f"New commit: {after}")
```

## Diagnostic Messages

### Progress Check Messages

```python
# First iteration
"First check (baseline: abc12345)"

# New commit detected
"New commit detected: def67890 (was abc12345)"

# Uncommitted changes
"Uncommitted changes detected (commit: abc12345)"

# No changes
"No changes detected (commit: abc12345, no uncommitted changes)"

# Git tracking disabled
"Git change tracking disabled"

# Not a git repo
"Not a git repo or git error (skipping check)"
```

### Circuit Breaker Messages

```python
# Normal operation
"Circuit breaker OK (2/3 iterations without progress)"

# Triggered
"""Circuit breaker triggered: 3 iterations without progress (threshold: 3) (current commit: abc12345)
  Expected: New commits OR uncommitted changes
  Detected: No new commits since abc12345, no uncommitted changes"""
```

## Migration Guide

### From Old Circuit Breaker Code

**Before** (manual implementation):
```python
@dataclass
class _CircuitBreakerState:
    threshold: int
    iterations_without_progress: int = 0
    last_git_diff_hash: Optional[str] = None

class MyOrchestrator:
    def __init__(self):
        self._breaker = _CircuitBreakerState(threshold=3)

    def check_git_changes(self):
        # ... manual git diff logic ...
        current_hash = get_git_diff_hash()
        if current_hash != self._breaker.last_git_diff_hash:
            # ... reset counter ...
```

**After** (unified tracker):
```python
from common.progress_tracker import ProgressTracker

class MyOrchestrator:
    def __init__(self):
        self._progress_tracker = ProgressTracker(
            project_path=self.project_path,
            circuit_breaker_threshold=3
        )

    def check_progress(self):
        has_progress, msg = self._progress_tracker.check_progress()
        # Done! All logic handled by ProgressTracker
```

### From GitVerifier

**Before**:
```python
from airflow_dags.autonomous_fixing.adapters.git.git_verifier import GitVerifier

verifier = GitVerifier()
before = verifier.get_head_commit(project_path)
# ... work ...
result = verifier.verify_commit_made(project_path, before, "operation")
```

**After** (same API, now uses ProgressTracker internally):
```python
# No changes needed! GitVerifier is now a compatibility wrapper
from airflow_dags.autonomous_fixing.adapters.git.git_verifier import GitVerifier

verifier = GitVerifier()  # Still works!
before = verifier.get_head_commit(project_path)
# ... work ...
result = verifier.verify_commit_made(project_path, before, "operation")
```

**Or migrate to ProgressTracker directly**:
```python
from airflow_dags.common.progress_tracker import ProgressTracker

tracker = ProgressTracker(project_path)
before = tracker.get_current_commit_id()
# ... work ...
result = tracker.verify_commit_made(project_path, before, "operation")
```

## Testing

Run the integration test:

```bash
.venv/bin/python3 -c "
from airflow_dags.common.progress_tracker import ProgressTracker
import tempfile, subprocess
from pathlib import Path

with tempfile.TemporaryDirectory() as tmpdir:
    tmpdir = Path(tmpdir)
    subprocess.run(['git', 'init'], cwd=tmpdir, capture_output=True)
    subprocess.run(['git', 'config', 'user.email', 'test@test.com'], cwd=tmpdir, capture_output=True)
    subprocess.run(['git', 'config', 'user.name', 'Test'], cwd=tmpdir, capture_output=True)
    (tmpdir / 'f.txt').write_text('1')
    subprocess.run(['git', 'add', '.'], cwd=tmpdir, capture_output=True)
    subprocess.run(['git', 'commit', '-m', 'Initial'], cwd=tmpdir, capture_output=True)

    tracker = ProgressTracker(tmpdir, circuit_breaker_threshold=3)

    # Test 1: First check
    has_progress, msg = tracker.check_progress()
    assert has_progress and 'baseline' in msg

    # Test 2: No changes
    has_progress, msg = tracker.check_progress()
    assert not has_progress and 'No changes' in msg

    # Test 3: New commit
    (tmpdir / 'f.txt').write_text('2')
    subprocess.run(['git', 'add', '.'], cwd=tmpdir, capture_output=True)
    subprocess.run(['git', 'commit', '-m', 'Change'], cwd=tmpdir, capture_output=True)
    has_progress, msg = tracker.check_progress()
    assert has_progress and 'New commit' in msg

    print('✅ All tests passed!')
"
```

## Benefits

1. **Single Source of Truth**: One implementation, no duplication
2. **Robust Detection**: Tracks both commits and uncommitted changes
3. **Better Diagnostics**: Detailed messages with commit IDs
4. **Backward Compatible**: GitVerifier still works as wrapper
5. **Testable**: Isolated from orchestrator logic
6. **Reusable**: Can be used by any orchestrator

## Future Enhancements

- [ ] Add support for tracking specific branches
- [ ] Add commit count threshold (e.g., "stop after 10 commits")
- [ ] Add time-based circuit breaker (e.g., "stop after 1 hour")
- [ ] Add progress metrics (commits/hour, lines changed, etc.)
- [ ] Add integration with state persistence (Redis, etc.)
