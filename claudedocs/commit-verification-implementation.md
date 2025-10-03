# Git Commit Verification Implementation

## Summary

Implemented commit verification to catch when Claude says "fixed successfully" but doesn't actually commit changes.

## Problem Identified

From debug logs, we discovered:
- Claude wrapper returns `"success": true`
- Console shows "✓ Tests created successfully"
- But next iteration shows `"Tests: 0/0 passed"` (no tests found!)
- **Root cause**: Claude didn't actually commit the changes

This caused:
- Rapid iterations (6-8 seconds each)
- Time gate correctly detected and aborted
- Wasteful API usage

## Solution Implemented

### 1. Created `core/git_verifier.py`

New GitVerifier class that:
- Gets HEAD commit hash before fix
- Gets HEAD commit hash after fix
- Compares them to verify a commit was made
- Returns detailed verification result

Key methods:
```python
get_head_commit(project_path) -> str
    Get current HEAD commit hash

verify_commit_made(project_path, before_commit, operation) -> Dict
    Verify that a new commit was made
    Returns: {'verified': bool, 'commit_made': bool, 'new_commit': str, 'message': str}

get_commit_message(project_path, commit_hash) -> str
    Get commit message for a commit
```

### 2. Integrated into `core/fixer.py`

Added commit verification to all fix operations:

#### `_fix_single_issue()` - Static issue fixes
```python
# Get HEAD before fix
before_commit = self.git_verifier.get_head_commit(issue['project'])

# Call Claude
result = self.claude.query(...)

# Verify commit
if result.get('success'):
    verification = self.git_verifier.verify_commit_made(...)
    if not verification['verified']:
        print("❌ ABORT: Claude said success but no commit detected!")
        return False
    print(f"✅ Verified: {verification['message']}")
    return True
```

#### `_fix_failing_tests()` - Test fixes
Same pattern: check before → fix → verify after

#### `_create_tests_for_project()` - Test creation
Same pattern: check before → create → verify after

## Expected Behavior

### Before (Problem):
```
Creating tests for cc-task-manager (javascript)
   ✓ Tests created successfully

ITERATION 2:
Tests: 0/0 passed  ← No tests!
⚠️  CRITICAL: No tests found
```

### After (With Verification):
```
Creating tests for cc-task-manager (javascript)
   ❌ ABORT: Claude said success but no commit detected!
   No commit detected after creating tests
   This indicates tests were not actually created.
   ✗ Test creation failed

Job aborted - investigate why no commit was made.
```

## Benefits

### 1. Early Detection
Catches the issue immediately instead of wasting iterations

### 2. Clear Diagnostics
```
❌ ABORT: Claude said success but no commit detected!
No commit detected after creating tests
This indicates tests were not actually created.
```

User knows exactly what went wrong.

### 3. Prevents API Waste
Stops after first failed commit verification instead of:
- 3 rapid iterations
- Time gate abort
- 3+ wrapper calls wasted

### 4. Actionable
When you see "no commit detected":
1. Check claude_wrapper output manually
2. Check if git is configured properly in the project
3. Check if Claude actually made changes
4. Investigate why no commit was created

## Testing

### Manual Test
```bash
# Run directly to see commit verification in action
/home/rmondo/.venv/air-executor/bin/python \
    airflow_dags/autonomous_fixing/multi_language_orchestrator.py \
    config/projects/cc-task-manager.yaml
```

Look for these messages:
- `❌ ABORT: Claude said success but no commit detected!` - Verification caught the issue
- `✅ Verified: Commit verified: abc12345` - Fix was committed properly

### Expected Results

**If Claude makes a commit**:
```
[1/8] Fixing error in file.js
   ✅ Verified: Commit verified: a1b2c3d4
```

**If Claude says success but no commit**:
```
[1/8] Fixing error in file.js
   ❌ ABORT: Claude said success but no commit detected!
   No commit detected after fixing error
   This indicates a problem with claude_wrapper or the fix.
   ✗ Fix failed
```

Job will abort and you can investigate.

## Debug Log Integration

The debug logger will show:
```json
{
  "event": "fix_result",
  "fix_type": "static_issue",
  "success": false,
  "details": {
    "verification_failed": true,
    "message": "No commit detected after fixing error"
  }
}
```

## Files Modified

- `core/git_verifier.py` - NEW: Git commit verification
- `core/fixer.py` - Added commit verification to all fix methods
  - `_fix_single_issue()`
  - `_fix_failing_tests()`
  - `_create_tests_for_project()`

## How It Works

```
┌─────────────────────────────────────────┐
│ 1. Get HEAD commit (before)            │
│    before_commit = abc123               │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ 2. Call Claude to fix/create tests     │
│    result = claude.query(...)           │
│    → Claude says: {"success": true}     │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ 3. Get HEAD commit (after)             │
│    after_commit = ???                   │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ 4. Compare                              │
│    if after == before:                  │
│        ❌ ABORT: No commit!             │
│    else:                                │
│        ✅ Verified: def456              │
└─────────────────────────────────────────┘
```

## Next Steps

1. **Test with one project** to see verification in action
2. **Investigate why no commits** when you see the abort message
3. **Fix claude_wrapper** if it's not committing properly
4. **Update prompts** if Claude needs better instructions about committing

## Configuration

No configuration needed - verification runs automatically for all fix operations.

To disable (not recommended):
```python
# In fixer.py __init__
self.git_verifier = None  # Disable verification
```

But this defeats the purpose of catching the issue!
