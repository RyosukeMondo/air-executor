# Silent Failures - Systematic Fix Plan

## Problem Summary

Found **28 CRITICAL** silent failures that hide configuration and setup errors.

### Anti-Pattern
```python
try:
    result = subprocess.run([tool, ...])
    # parse result...
except Exception as e:
    result.success = False
    result.error_message = str(e)  # HIDES the real problem!
```

**Why this is bad:**
- Tool not installed → Silent failure (success=False)
- User doesn't know what to fix
- Analysis results appear as "failed tests" instead of "missing tool"
- Debugging is impossible

## Fix Strategy

### Error Classification

1. **FAIL FAST** (Raise immediately):
   - Tool not installed (FileNotFoundError, "No module named")
   - Configuration errors
   - Setup problems

2. **EXPECTED** (Set result.success = False):
   - subprocess.TimeoutExpired
   - Tests actually failing (expected behavior)
   - Valid build failures

3. **RECOVERABLE** (Log and continue):
   - Single file parsing errors
   - Malformed data in optional files

### Implementation Pattern

**Before (WRONG):**
```python
try:
    result = subprocess.run(["tool", ...])
    # ...
except Exception as e:
    result.success = False
    result.error_message = str(e)
```

**After (CORRECT):**
```python
try:
    result = subprocess.run(["tool", ...])
    # ...
except subprocess.TimeoutExpired:
    # Expected - tests/analysis timed out
    result.success = False
    result.error_message = "Analysis timed out"
except (FileNotFoundError, RuntimeError) as e:
    # Configuration error - FAIL FAST
    if "not installed" in str(e) or "not found" in str(e):
        raise RuntimeError(
            f"Tool not installed: {e}\n"
            f"Install with: [installation command]"
        ) from e
    raise  # Re-raise other runtime errors
except Exception as e:
    # Unexpected error - log and raise
    logger.error(f"Unexpected error in analysis: {e}")
    raise
```

## Systematic Fixes

### Phase 1: Adapter Methods (CRITICAL - 28 occurrences)

**Files to fix:**
- `python_adapter.py` (lines 74, 135, 171, 204, 457, 495)
- `javascript_adapter.py` (lines 66, 135, 171, 222, 484, 537)
- `go_adapter.py` (lines 64, 96, 161, 199)
- `flutter_adapter.py` (lines 123, 207, 247)

**Methods affected:**
- `static_analysis()`
- `run_tests()`
- `analyze_coverage()`
- `run_e2e_tests()`
- `run_type_check()`
- `run_build()`

**Fix approach:**
1. Replace broad `except Exception` with specific exceptions
2. Check for tool availability errors → raise immediately
3. Keep timeout handling (expected)
4. Add clear error messages with fix suggestions

### Phase 2: Tool Validation (8 occurrences)

**Files:**
- `python_adapter.py` (_validate_python, _validate_tool)
- `javascript_adapter.py` (_validate_node, _validate_tool)
- `go_adapter.py` (_validate_go, _validate_tool)
- `flutter_adapter.py` (_validate_flutter, _validate_dart)

**Current:**
```python
except Exception as e:
    return ToolValidationResult(
        tool_name=tool,
        available=False,
        error_message=f"Tool failed: {e}"
    )
```

**Better:**
```python
except subprocess.TimeoutExpired:
    return ToolValidationResult(
        tool_name=tool,
        available=False,
        error_message="Tool validation timed out"
    )
except Exception as e:
    # Unexpected validation error - should investigate
    logger.warning(f"Tool validation failed unexpectedly: {e}")
    return ToolValidationResult(
        tool_name=tool,
        available=False,
        error_message=str(e)
    )
```

### Phase 3: Utility Functions (WARNING - 62 occurrences)

**Pattern:** Silent print + continue
```python
except Exception as e:
    print(f"Error: {e}")
    # continues silently
```

**Fix:**
- Add logging at appropriate level
- Consider if error should stop execution
- Add context about what failed and why

## Testing Strategy

For each fixed method, add test:

```python
def test_METHOD_fails_fast_when_tool_missing(monkeypatch):
    """Verify METHOD raises clear error when tool unavailable."""
    def mock_tool_missing(*args, **kwargs):
        raise FileNotFoundError("tool not found")

    monkeypatch.setattr(subprocess, "run", mock_tool_missing)

    with pytest.raises(RuntimeError, match="not installed"):
        adapter.METHOD(project_path)
```

## Implementation Order

1. ✅ **Fix calculate_complexity** (already done)
   - Added fail-fast for radon
   - Added comprehensive tests

2. **Fix remaining Python adapter methods** (6 methods)
   - static_analysis, run_tests, analyze_coverage
   - run_e2e_tests, run_type_check, run_build

3. **Apply same pattern to other adapters**
   - JavaScript, Go, Flutter
   - Copy the pattern from Python adapter

4. **Fix tool validation methods**
   - Add logging
   - Improve error messages

5. **Fix WARNING cases**
   - Add proper logging
   - Consider fail-fast where appropriate

## Success Criteria

- ✅ All adapter methods have specific exception handling
- ✅ Configuration errors raise immediately with helpful messages
- ✅ Timeout errors set result.success = False (expected)
- ✅ Every adapter method has test for tool-missing scenario
- ✅ No more silent failures hiding setup problems

## Impact

**Before:**
- Tool missing → Silent failure, appears as "test failed"
- User confused, debugging impossible
- Orchestrator keeps retrying wrong approach

**After:**
- Tool missing → Immediate clear error: "radon not installed: pip install radon"
- User knows exactly what to fix
- Fail fast = save time
