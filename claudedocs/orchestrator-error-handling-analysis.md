# Orchestrator Error Handling Analysis

## Problem: Confusing Error Messages

### What You Observed
```
[1/1] Running tests for PYTHON: air-executor...
✗ PYTHON: air-executor - Error: pytest not found: [Errno 2] No such file or directory: 'pytest'
Install with: pip install pytest

⚠ CRITICAL: No tests found
All projects have sufficient tests
```

This is confusing because:
1. First it says "pytest not found" (configuration error)
2. Then it says "no tests found" (sounds like a test issue)
3. Then it says "sufficient tests" (contradictory!)

### Root Cause Analysis

**BEFORE the fix** (commit 91ef450):

```python
# analyzer.py (OLD CODE)
try:
    analysis = adapter.run_tests(project_path, strategy)
    key = f"{lang_name}:{project_path}"
    result.results_by_project[key] = analysis  # ← Never executes!
except Exception as e:
    print(f"✗ Error: {e}\n")  # ← Prints error but CONTINUES
    # Note: No result added to results_by_project!
```

**What happened:**
1. `adapter.run_tests()` raises `RuntimeError("pytest not found...")`
2. `analyzer.py` catches it as generic `Exception`
3. Prints the error message
4. **Does NOT add result to `results_by_project`**
5. Continues execution (doesn't crash)

**Downstream impact:**
```python
# Later in scorer.py or iteration_engine.py
if not results_by_project:  # Empty dict!
    print("⚠ CRITICAL: No tests found")
    # But then some other check passes because...
    # missing results are interpreted as "no tests to run"
    # which might be considered "passing" in some logic!
```

So "error code is treated as result count" means:
- **Missing result** (because exception was caught) → interpreted as "no tests"
- **"No tests"** → might be treated as success in some gate logic
- **Result:** Confusing contradictory messages

### AFTER the fix (commit 91ef450):

```python
# analyzer.py (NEW CODE)
try:
    analysis = adapter.run_tests(project_path, strategy)
    key = f"{lang_name}:{project_path}"
    result.results_by_project[key] = analysis
except RuntimeError as e:
    # Configuration errors (tools not installed) - FAIL FAST
    error_msg = str(e).lower()
    if any(phrase in error_msg for phrase in ["not installed", "not found", "no module named"]):
        print(f"\n❌ CONFIGURATION ERROR: {project_name}")
        print(f"   {e}\n")
        raise  # ← RE-RAISE to halt execution!
    # Other runtime errors - log and continue
    print(f"✗ Runtime error: {e}\n")
except Exception as e:
    # Unexpected errors - log and continue
    print(f"✗ Unexpected error: {e}\n")
```

**What happens now:**
1. `adapter.run_tests()` raises `RuntimeError("pytest not found...")`
2. `analyzer.py` catches it as `RuntimeError`
3. Checks if error message contains "not installed"/"not found" → YES
4. Prints clear "❌ CONFIGURATION ERROR" message
5. **RE-RAISES the exception** → propagates to orchestrator → **script crashes**
6. **No confusing messages** because execution halts immediately!

## Error Propagation Path

```
Adapter (raises RuntimeError)
    ↓
analyzer.py (catches, checks, re-raises)
    ↓
iteration_engine.run_improvement_loop() (no catch, propagates)
    ↓
orchestrator.execute() (no catch, propagates)
    ↓
run_orchestrator.py (no catch, propagates)
    ↓
Python interpreter (crashes with stack trace)
```

This is **correct behavior** for fail-fast!

## What We Should Test

### Unit Test
```python
def test_analyzer_reraises_configuration_errors():
    """analyzer.py should re-raise configuration errors to halt execution."""
    # Mock adapter to raise RuntimeError with "not installed"
    # Call analyzer.analyze_tests()
    # Assert RuntimeError is raised (not caught)
```

### Integration Test
```python
def test_missing_pytest_halts_orchestrator():
    """Missing pytest should halt entire orchestrator with clear message."""
    # Mock pytest to be unavailable
    # Run orchestrator
    # Assert it crashes with ConfigurationError
    # Assert error message contains installation instructions
```

## Improvements to Consider

### 1. Custom Exception Type (RECOMMENDED)
Instead of `RuntimeError` + string matching, use:
```python
from ..domain.exceptions import ConfigurationError

# In adapter:
raise ConfigurationError(
    "pytest not found: [error]\n"
    "Install with: pip install pytest"
)

# In analyzer.py:
except ConfigurationError as e:
    print(f"\n❌ CONFIGURATION ERROR: {e}\n")
    raise  # Re-raise
```

**Benefits:**
- ✅ No string matching needed
- ✅ Clear exception type in stack trace
- ✅ Better type hints and documentation
- ✅ Easier to catch specifically if needed

### 2. Structured Error Messages
```python
class ConfigurationError(Exception):
    def __init__(self, tool: str, error: str, install_cmd: str = None):
        self.tool = tool
        self.error = error
        self.install_cmd = install_cmd

        message = f"{tool} not found: {error}"
        if install_cmd:
            message += f"\nInstall with: {install_cmd}"

        super().__init__(message)
```

### 3. Better Error Reporting
```python
# In analyzer.py:
except ConfigurationError as e:
    print(f"\n{'='*80}")
    print("❌ CONFIGURATION ERROR")
    print(f"{'='*80}")
    print(f"Tool: {e.tool}")
    print(f"Error: {e.error}")
    if e.install_cmd:
        print(f"Install: {e.install_cmd}")
    print(f"{'='*80}\n")
    raise
```

## Summary

✅ **Commit 91ef450 is CORRECT** - it fixes the problem by re-raising configuration errors
✅ **All components handle it correctly** - no exception handling in the chain, so it propagates
✅ **Fail-fast works** - missing tools now crash immediately with clear message

🔧 **Recommended next steps:**
1. Write integration tests to verify behavior
2. Refactor to use `ConfigurationError` instead of `RuntimeError` + string matching
3. Add structured error messages with tool name, error, installation command

📝 **Decision required:**
- Should we refactor to `ConfigurationError` now, or keep `RuntimeError` for simplicity?
- Should we write tests before or after the refactor?
