# Sample Python Project

Small test project for multi-language orchestrator testing.

## Intentional Issues

### P1: Static Analysis
- ❌ **Unused import**: `os` in calculator.py
- ❌ **Type hints missing**: `multiply()` function
- ❌ **High complexity**: `complex_calculator()` has complexity > 10
- ❌ **File size**: `large_module.py` exceeds 500 lines

### P2: Tests
- ✅ **Passing**: 6 tests pass
- ❌ **Failing**: 2 tests fail intentionally
  - `test_divide_basic()` - wrong assertion
  - `test_complex_calculator_power()` - wrong expected value

### P3: Coverage
- ❌ **No coverage**: `advanced_math()` - never tested
- ❌ **No coverage**: `handle_edge_cases()` - never tested
- ❌ **Partial coverage**: `complex_calculator()` - only 2/11 operations tested

## Running Tests

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Run with coverage
pytest --cov=src --cov-report=term --cov-report=json

# Run only fast tests (P2 minimal strategy)
pytest -m "not slow"
```

## Expected Results

### P1 Static Analysis
- Errors: 3-4 (unused import, type hints, etc.)
- Complexity violations: 1 (complex_calculator)
- File size violations: 1 (large_module.py)
- **Score: ~60-70%** (intentionally below 90% threshold)

### P2 Tests
- Total: 8 tests
- Passing: 6
- Failing: 2
- **Score: 75%** (intentionally below 85% threshold)

### P3 Coverage
- Overall: ~40-50%
- Gaps: 2-3 files with low coverage
- **Needs**: Tests for advanced_math(), handle_edge_cases()
