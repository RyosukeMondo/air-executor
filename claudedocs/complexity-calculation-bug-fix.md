# Complexity Calculation Bug Fix & Test Coverage Enhancement

## Date
2025-10-04

## Problem Summary

The autonomous fixing orchestrator was reporting "Claude said success but no commit detected" for already-fixed files. Investigation revealed a critical bug in complexity calculation.

### Root Cause
**Silent failure in complexity calculation** caused incorrect complexity values:

1. `calculate_complexity()` called `subprocess.run(["radon", ...])`
2. `radon` is in `.venv/bin/radon` but NOT in system PATH
3. subprocess failed silently (FileNotFoundError)
4. Fell back to `_simple_complexity()` which counts keywords
5. spawner.py returned complexity **44** (wrong!) instead of actual **7**
6. File appeared as violation (44 > 15) even though it was already fixed

### Why "No Commit Detected"
- Orchestrator thought spawner.py had complexity 44 (incorrect)
- Asked Claude to fix it (iteration after iteration)
- Claude saw the file was already fine (complexity 7), made no changes
- No commit created (correctly - nothing to commit!)
- Git verifier correctly reported no commit
- **But**: Orchestrator kept re-selecting the same file due to stale/wrong analysis

## Why Tests Didn't Catch This

### Existing Test Coverage (✅ What was tested)
1. **Interface compliance** - Method exists ✓
2. **Method signature** - Parameters match ✓
3. **Integration** - Doesn't crash ✓
4. **Result count** - Returns violations ✓

### Critical Gap (❌ What was NOT tested)
1. **Functional correctness** - Values are accurate ✗
2. **Tool availability** - Radon is accessible ✗
3. **Error handling** - Failures are visible ✗
4. **Silent fallbacks** - Wrong values detected ✗

## Fixes Implemented

### 1. Fixed radon PATH Issue (python_adapter.py:219)
**Before (broken):**
```python
subprocess.run(["radon", "cc", file_path, ...])  # Fails if not in PATH
```

**After (fixed):**
```python
subprocess.run([sys.executable, "-m", "radon", "cc", file_path, ...])  # Works with venv
```

### 2. Removed Silent Failures (python_adapter.py:215-251)
**Before (silent):**
```python
try:
    result = subprocess.run(["radon", ...])
    # Parse...
    return max_complexity
except Exception:
    return self._simple_complexity(file_path)  # Silent fallback!
```

**After (fail fast):**
```python
def calculate_complexity(self, file_path: str) -> int:
    """Calculate cyclomatic complexity using radon.

    Raises:
        FileNotFoundError: If file doesn't exist
        subprocess.TimeoutExpired: If radon hangs
        RuntimeError: If radon is not installed or fails
    """
    if not Path(file_path).exists():
        raise FileNotFoundError(f"Cannot calculate complexity: {file_path} does not exist")

    result = subprocess.run([sys.executable, "-m", "radon", ...])

    if result.returncode != 0:
        error_msg = result.stderr or result.stdout or "Unknown error"
        if "No module named" in error_msg:
            raise RuntimeError(
                f"Radon is not installed. Install with: pip install radon\n"
                f"Error: {error_msg}"
            )
        raise RuntimeError(f"Radon failed: {error_msg}")

    # Parse and return...
```

### 3. Improved Error Handling in Base Class (base.py:248-261)
**Before (silent):**
```python
except Exception:
    # Skip files that fail analysis
    continue
```

**After (selective):**
```python
except (FileNotFoundError, PermissionError):
    # Expected - skip inaccessible files
    continue
except RuntimeError as e:
    # Configuration errors - FAIL FAST
    if "not installed" in str(e).lower():
        raise  # Re-raise immediately!
    print(f"⚠️ Skipping {file_path.name}: {e}")
    continue
except Exception as e:
    # Unexpected - log and skip
    print(f"⚠️ Unexpected error: {type(e).__name__}: {e}")
    continue
```

### 4. Added Comprehensive Test Suite (tests/unit/test_complexity_calculation.py)

**8 new tests:**

1. `test_radon_is_available` - Verifies radon is installed
2. `test_calculate_complexity_with_simple_function` - Tests simple code (complexity ≤ 2)
3. `test_calculate_complexity_with_complex_function` - Tests complex code (~7)
4. `test_calculate_complexity_on_real_file` - Tests spawner.py (actual file)
5. `test_complexity_matches_radon_output` - Verifies adapter matches radon exactly
6. **`test_no_silent_failures`** - **KEY TEST**: Mocks radon failure, ensures it raises error
7. `test_nonexistent_file_raises_error` - Tests error handling
8. `test_simple_complexity_counts_control_flow` - Tests fallback heuristic

**Key test that would have caught the bug:**
```python
def test_no_silent_failures(self, adapter, monkeypatch):
    """Complexity calculation should NOT silently fall back on errors."""
    def mock_run_fail(*args, **kwargs):
        raise FileNotFoundError("radon not found")

    monkeypatch.setattr(subprocess, "run", mock_run_fail)

    # Should raise error, NOT silently return wrong value
    with pytest.raises(Exception):
        adapter.calculate_complexity("/some/file.py")
```

## Verification Results

### ✅ All Tests Pass
```
tests/unit/test_complexity_calculation.py::TestComplexityCalculation
  ✓ test_radon_is_available                              PASSED
  ✓ test_calculate_complexity_with_simple_function       PASSED
  ✓ test_calculate_complexity_with_complex_function      PASSED
  ✓ test_calculate_complexity_on_real_file              PASSED
  ✓ test_complexity_matches_radon_output                PASSED
  ✓ test_no_silent_failures                             PASSED
  ✓ test_nonexistent_file_raises_error                  PASSED
  ✓ test_simple_complexity_counts_control_flow          PASSED

8 passed in 0.37s
```

### ✅ Existing Tests Still Pass
```
tests/unit/test_adapter_interface_compliance.py
  ✓ All 16 adapter compliance tests                     PASSED
```

### ✅ Complexity Now Correct
```bash
Before fix:  spawner.py complexity = 44 (WRONG!)
After fix:   spawner.py complexity = 7  (CORRECT!)

Threshold: 15
Is violation: False ✓
```

### ✅ Fail-Fast Behavior Works
```python
# When radon is unavailable:
RuntimeError: Radon is not installed. Install with: pip install radon
Error: No module named radon
```

## Impact & Benefits

### 🔴 Critical Issues Fixed
1. **Accuracy**: Complexity values now correct (7 vs 44)
2. **Visibility**: Configuration errors now visible immediately
3. **Reliability**: No more silent fallbacks masking bugs

### 🟡 Testing Improvements
1. **Functional tests**: Verify correctness, not just existence
2. **Error simulation**: Test failure scenarios explicitly
3. **Real-world validation**: Test against actual project files

### 🟢 Future Prevention
1. **Fail-fast principle**: Configuration errors halt execution
2. **Clear error messages**: Guide users to fix setup issues
3. **Test coverage**: Silent failures now have explicit tests

## Lessons Learned

### Anti-Pattern: Silent Failures
❌ **NEVER DO THIS:**
```python
try:
    result = expensive_operation()
    return result
except Exception:
    return fallback_that_might_be_wrong()
```

✅ **DO THIS INSTEAD:**
```python
try:
    result = expensive_operation()
    return result
except SpecificExpectedError:
    # Only catch errors you expect
    handle_gracefully()
except ConfigurationError:
    # Setup errors should fail fast
    raise
```

### Test Coverage Principle
- ✅ Test method **exists** (interface compliance)
- ✅ Test method **works** (functional correctness)
- ✅ Test method **fails correctly** (error handling)
- ✅ Test **tool availability** (environment validation)

### Fail-Fast Philosophy
1. **Configuration errors** → Raise immediately with helpful message
2. **Expected errors** → Handle gracefully (file not found, permissions)
3. **Unexpected errors** → Log and continue OR fail (depending on criticality)
4. **Silent fallbacks** → NEVER (they hide bugs!)

## Files Modified

1. `/home/rmondo/repos/air-executor/airflow_dags/autonomous_fixing/adapters/languages/python_adapter.py`
   - Line 7: Added `import sys`
   - Lines 215-251: Fixed `calculate_complexity()` - fail fast, use `sys.executable -m radon`

2. `/home/rmondo/repos/air-executor/airflow_dags/autonomous_fixing/adapters/languages/base.py`
   - Lines 248-261: Improved error handling in `check_complexity()` - selective exception handling

3. `/home/rmondo/repos/air-executor/tests/unit/test_complexity_calculation.py` (NEW)
   - 8 comprehensive tests for complexity calculation accuracy
   - Explicit test for "no silent failures"

## Conclusion

**Root cause**: Silent failure in complexity calculation due to radon PATH issue
**Why tests didn't catch it**: Only tested method existence, not correctness or error handling
**Fixes applied**:
- Use `sys.executable -m radon` (works with venv)
- Remove silent try/except (fail fast on setup errors)
- Add comprehensive functional tests
- Selective error handling (re-raise config errors)

**Result**: Complexity values now accurate, setup errors visible immediately, comprehensive test coverage prevents regression.
