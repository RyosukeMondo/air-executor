# Test Coverage Analysis Guide

Complete guide for checking test coverage across Unit, Integration, and E2E tests.

---

## Quick Reference

```bash
# All tests with coverage
.venv/bin/python3 -m pytest tests/ --cov=airflow_dags/autonomous_fixing --cov-report=html

# Unit tests only
.venv/bin/python3 -m pytest tests/unit/ --cov=airflow_dags/autonomous_fixing --cov-report=term-missing

# Integration tests only
.venv/bin/python3 -m pytest tests/integration/ --cov=airflow_dags/autonomous_fixing --cov-report=term-missing

# E2E tests only
.venv/bin/python3 -m pytest tests/e2e/ --cov=airflow_dags/autonomous_fixing --cov-report=term-missing

# View HTML report (after running with --cov-report=html)
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

---

## Coverage Report Types

### 1. Terminal Output (Default)

**Command**:
```bash
.venv/bin/python3 -m pytest tests/ --cov=airflow_dags/autonomous_fixing --cov-report=term
```

**Output**:
```
---------- coverage: platform linux, python 3.12.3-final-0 -----------
Name                                                          Stmts   Miss  Cover
---------------------------------------------------------------------------------
airflow_dags/autonomous_fixing/__init__.py                        0      0   100%
airflow_dags/autonomous_fixing/core/analyzer.py                 120     15    88%
airflow_dags/autonomous_fixing/core/fixer.py                    156     28    82%
...
TOTAL                                                          3245    456    86%
```

### 2. Terminal with Missing Lines

**Command**:
```bash
.venv/bin/python3 -m pytest tests/ --cov=airflow_dags/autonomous_fixing --cov-report=term-missing
```

**Output**:
```
Name                                                Stmts   Miss  Cover   Missing
----------------------------------------------------------------------------------
airflow_dags/autonomous_fixing/core/analyzer.py       120     15    88%   45-48, 67, 89-92
airflow_dags/autonomous_fixing/core/fixer.py          156     28    82%   123-145, 201-205
...
```

**Use When**: You want to see exactly which lines aren't covered

### 3. HTML Report (Most Detailed)

**Command**:
```bash
.venv/bin/python3 -m pytest tests/ --cov=airflow_dags/autonomous_fixing --cov-report=html
```

**Output**: Creates `htmlcov/` directory with interactive HTML reports

**Features**:
- Visual line-by-line coverage highlighting
- Click through to see exact uncovered lines
- Sort by coverage percentage
- Filter by file/directory
- Branch coverage visualization

**View Report**:
```bash
# Open in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
firefox htmlcov/index.html  # Explicit browser
```

### 4. XML Report (CI/CD Integration)

**Command**:
```bash
.venv/bin/python3 -m pytest tests/ --cov=airflow_dags/autonomous_fixing --cov-report=xml
```

**Output**: Creates `coverage.xml` for tools like Codecov, Coveralls, SonarQube

---

## Coverage by Test Tier

### Unit Tests Coverage

**What It Measures**: Coverage from fast, isolated unit tests

**Command**:
```bash
.venv/bin/python3 -m pytest tests/unit/ \
  --cov=airflow_dags/autonomous_fixing \
  --cov-report=html:htmlcov-unit \
  --cov-report=term-missing
```

**Expected Coverage**: 70-85% (focused on core logic)

**Good For**:
- Individual function/method testing
- Edge case coverage
- Algorithm correctness
- Pure logic paths

### Integration Tests Coverage

**What It Measures**: Coverage from component interaction tests

**Command**:
```bash
.venv/bin/python3 -m pytest tests/integration/ \
  --cov=airflow_dags/autonomous_fixing \
  --cov-report=html:htmlcov-integration \
  --cov-report=term-missing
```

**Expected Coverage**: 60-75% (focused on integration points)

**Good For**:
- Component interactions
- Data flow between modules
- Interface compliance
- Service integration

### E2E Tests Coverage

**What It Measures**: Coverage from end-to-end scenario tests

**Command**:
```bash
.venv/bin/python3 -m pytest tests/e2e/ \
  --cov=airflow_dags/autonomous_fixing \
  --cov-report=html:htmlcov-e2e \
  --cov-report=term-missing
```

**Expected Coverage**: 40-60% (focused on critical paths)

**Good For**:
- Full workflow validation
- Real-world scenarios
- System-level behavior
- Critical user journeys

---

## Combined Coverage Analysis

### All Tests Together

**Command**:
```bash
.venv/bin/python3 -m pytest tests/ \
  --cov=airflow_dags/autonomous_fixing \
  --cov-report=html \
  --cov-report=term-missing
```

**Target**: >80% overall coverage

### Incremental Coverage (Add to Existing)

**Use Case**: See coverage gain from specific test tier

**Commands**:
```bash
# Step 1: Run unit tests, save coverage data
.venv/bin/python3 -m pytest tests/unit/ \
  --cov=airflow_dags/autonomous_fixing \
  --cov-report=

# Step 2: Run integration tests, append to coverage
.venv/bin/python3 -m pytest tests/integration/ \
  --cov=airflow_dags/autonomous_fixing \
  --cov-append \
  --cov-report=

# Step 3: Run e2e tests, append and generate report
.venv/bin/python3 -m pytest tests/e2e/ \
  --cov=airflow_dags/autonomous_fixing \
  --cov-append \
  --cov-report=html \
  --cov-report=term-missing
```

**Result**: Shows cumulative coverage across all tiers

---

## Advanced Coverage Analysis

### 1. Branch Coverage

**What It Measures**: Ensures both `if` and `else` branches are tested

**Command**:
```bash
.venv/bin/python3 -m pytest tests/ \
  --cov=airflow_dags/autonomous_fixing \
  --cov-branch \
  --cov-report=term-missing
```

**Output**:
```
Name                                  Stmts   Miss Branch BrPart  Cover   Missing
---------------------------------------------------------------------------------
airflow_dags/.../analyzer.py           120     15     48      5    85%   45-48, 67->exit
```

**Use When**: You want to ensure all conditional paths are tested

### 2. Coverage for Specific Module

**Command**:
```bash
# Only cover core/ modules
.venv/bin/python3 -m pytest tests/ \
  --cov=airflow_dags/autonomous_fixing/core \
  --cov-report=html

# Only cover adapters/ modules
.venv/bin/python3 -m pytest tests/ \
  --cov=airflow_dags/autonomous_fixing/adapters \
  --cov-report=html
```

### 3. Coverage with Minimum Threshold

**Command**:
```bash
.venv/bin/python3 -m pytest tests/ \
  --cov=airflow_dags/autonomous_fixing \
  --cov-report=term-missing \
  --cov-fail-under=80
```

**Use When**: Enforce minimum coverage in CI/CD (fails if below 80%)

### 4. Coverage Context (Show Which Tests Cover Which Lines)

**Command**:
```bash
.venv/bin/python3 -m pytest tests/ \
  --cov=airflow_dags/autonomous_fixing \
  --cov-context=test \
  --cov-report=html
```

**Feature**: HTML report shows which specific test covered each line

---

## Practical Workflows

### Daily Development Workflow

```bash
# Quick check while developing
.venv/bin/python3 -m pytest tests/unit/test_my_module.py \
  --cov=airflow_dags/autonomous_fixing/core/my_module \
  --cov-report=term-missing
```

### Pre-Commit Check

```bash
# Ensure new code has coverage
.venv/bin/python3 -m pytest tests/ \
  --cov=airflow_dags/autonomous_fixing \
  --cov-report=term-missing \
  --cov-fail-under=80
```

### Coverage Gap Analysis

```bash
# 1. Generate HTML report
.venv/bin/python3 -m pytest tests/ \
  --cov=airflow_dags/autonomous_fixing \
  --cov-report=html

# 2. Open report
open htmlcov/index.html

# 3. Sort by coverage percentage (ascending)
# 4. Identify files < 70% coverage
# 5. Write tests for uncovered lines
```

### CI/CD Integration

```bash
# Generate XML for external tools
.venv/bin/python3 -m pytest tests/ \
  --cov=airflow_dags/autonomous_fixing \
  --cov-report=xml \
  --cov-report=term \
  --cov-fail-under=80
```

---

## Coverage Report Interpretation

### Good Coverage Metrics

| Metric | Target | Interpretation |
|--------|--------|----------------|
| **Overall Coverage** | >80% | Strong test coverage |
| **Core Modules** | >85% | Critical logic well-tested |
| **Adapters** | >75% | Integration points tested |
| **Utils** | >90% | Helper functions covered |
| **Models** | >70% | Data structures validated |

### Coverage by File Type

| File Type | Target | Priority |
|-----------|--------|----------|
| `core/*.py` | >85% | 🔴 High - Core business logic |
| `adapters/*.py` | >75% | 🟡 Medium - Integration points |
| `domain/*.py` | >70% | 🟡 Medium - Data models |
| `config/*.py` | >60% | 🟢 Low - Configuration |
| `scripts/*.py` | >40% | 🟢 Low - Utilities |

### Warning Signs

⚠️ **Coverage < 60%**: Likely missing critical test cases
⚠️ **Many missing branches**: Incomplete conditional testing
⚠️ **0% coverage in core files**: Serious testing gap
⚠️ **Decreasing coverage trend**: Test debt accumulating

---

## Coverage Best Practices

### 1. Focus on Meaningful Coverage

❌ **Bad**: Aiming for 100% coverage by testing trivial code
✅ **Good**: 80% coverage of critical business logic

### 2. Use Coverage to Find Gaps

**Workflow**:
1. Run coverage report
2. Identify uncovered critical paths
3. Write tests for those paths
4. Re-run coverage to verify

### 3. Combine with Other Metrics

**Coverage alone isn't enough**:
- ✅ Coverage + Passing tests
- ✅ Coverage + Code complexity metrics
- ✅ Coverage + Mutation testing (advanced)

### 4. Track Trends Over Time

```bash
# Save coverage percentage over time
echo "$(date +%Y-%m-%d),$(pytest --cov=airflow_dags --cov-report=term | grep TOTAL | awk '{print $4}')" >> coverage-history.csv
```

---

## Troubleshooting

### Issue: "No data to report"

**Cause**: Coverage module configuration mismatch

**Solution**:
```bash
# Ensure correct source path
.venv/bin/python3 -m pytest tests/ --cov=airflow_dags/autonomous_fixing

# NOT this (wrong path):
.venv/bin/python3 -m pytest tests/ --cov=air_executor
```

### Issue: Coverage data from previous runs

**Cause**: Old `.coverage` file persists

**Solution**:
```bash
# Clean coverage data
rm -f .coverage .coverage.*

# Or use --cov-reset
.venv/bin/python3 -m pytest tests/ --cov-reset --cov=airflow_dags/autonomous_fixing
```

### Issue: htmlcov/ directory missing

**Cause**: No `--cov-report=html` specified

**Solution**:
```bash
# Must include html report flag
.venv/bin/python3 -m pytest tests/ \
  --cov=airflow_dags/autonomous_fixing \
  --cov-report=html
```

---

## Configuration Files

### pyproject.toml Coverage Settings

Current configuration in `pyproject.toml:79`:
```toml
[tool.pytest.ini_options]
addopts = "-v --cov=air_executor --cov-report=term-missing"
```

**Note**: This has a bug - should be `--cov=airflow_dags/autonomous_fixing`

**Recommended Update**:
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = """
  -v
  --cov=airflow_dags/autonomous_fixing
  --cov-report=term-missing
  --cov-report=html
"""
```

### .coveragerc (Optional Advanced Config)

Create `.coveragerc` for fine-grained control:

```ini
[run]
source = airflow_dags/autonomous_fixing
omit =
    */tests/*
    */__pycache__/*
    */venv/*
    */node_modules/*

[report]
precision = 2
exclude_lines =
    pragma: no cover
    def __repr__
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
    @abstractmethod

[html]
directory = htmlcov
```

---

## Quick Commands Summary

```bash
# === UNIT TESTS ===
.venv/bin/python3 -m pytest tests/unit/ --cov=airflow_dags/autonomous_fixing --cov-report=html:htmlcov-unit

# === INTEGRATION TESTS ===
.venv/bin/python3 -m pytest tests/integration/ --cov=airflow_dags/autonomous_fixing --cov-report=html:htmlcov-integration

# === E2E TESTS ===
.venv/bin/python3 -m pytest tests/e2e/ --cov=airflow_dags/autonomous_fixing --cov-report=html:htmlcov-e2e

# === ALL TESTS ===
.venv/bin/python3 -m pytest tests/ --cov=airflow_dags/autonomous_fixing --cov-report=html --cov-report=term-missing

# === VIEW HTML REPORT ===
open htmlcov/index.html

# === COVERAGE WITH CI THRESHOLD ===
.venv/bin/python3 -m pytest tests/ --cov=airflow_dags/autonomous_fixing --cov-fail-under=80

# === BRANCH COVERAGE ===
.venv/bin/python3 -m pytest tests/ --cov=airflow_dags/autonomous_fixing --cov-branch --cov-report=term-missing
```

---

## Example Coverage Workflow

```bash
#!/bin/bash
# coverage-check.sh - Complete coverage analysis workflow

echo "🧪 Running Unit Tests with Coverage..."
.venv/bin/python3 -m pytest tests/unit/ \
  --cov=airflow_dags/autonomous_fixing \
  --cov-report=html:htmlcov-unit \
  --cov-report=term-missing

echo ""
echo "🔗 Running Integration Tests with Coverage..."
.venv/bin/python3 -m pytest tests/integration/ \
  --cov=airflow_dags/autonomous_fixing \
  --cov-report=html:htmlcov-integration \
  --cov-report=term-missing

echo ""
echo "🚀 Running E2E Tests with Coverage..."
.venv/bin/python3 -m pytest tests/e2e/ \
  --cov=airflow_dags/autonomous_fixing \
  --cov-report=html:htmlcov-e2e \
  --cov-report=term-missing

echo ""
echo "📊 Running ALL Tests with Combined Coverage..."
.venv/bin/python3 -m pytest tests/ \
  --cov=airflow_dags/autonomous_fixing \
  --cov-report=html \
  --cov-report=term-missing \
  --cov-fail-under=80

echo ""
echo "✅ Coverage reports generated:"
echo "   Unit:        htmlcov-unit/index.html"
echo "   Integration: htmlcov-integration/index.html"
echo "   E2E:         htmlcov-e2e/index.html"
echo "   Combined:    htmlcov/index.html"
echo ""
echo "Open with: open htmlcov/index.html"
```

---

## Related Documentation

- **Test Organization**: `.claude/CLAUDE.md`
- **Interface Tests**: `tests/README_INTERFACE_TESTS.md`
- **E2E Coverage Analysis**: `claudedocs/e2e-test-coverage-analysis-2025-10-05.md`
- **Pytest Documentation**: https://docs.pytest.org/en/stable/how-to/coverage.html
