# Test Coverage Quick Start Guide

Fast reference for checking test coverage across Unit, Integration, and E2E tests.

---

## 🚀 Quick Commands

```bash
# === RUN ALL TESTS WITH COVERAGE ===
.venv/bin/python3 -m pytest tests/ \
  --cov=airflow_dags/autonomous_fixing \
  --cov-report=html \
  --cov-report=term-missing

# Then open: htmlcov/index.html

# === INDIVIDUAL TEST TIERS ===
# Unit Tests
.venv/bin/python3 -m pytest tests/unit/ --cov=airflow_dags/autonomous_fixing --cov-report=term-missing

# Integration Tests
.venv/bin/python3 -m pytest tests/integration/ --cov=airflow_dags/autonomous_fixing --cov-report=term-missing

# E2E Tests
.venv/bin/python3 -m pytest tests/e2e/ --cov=airflow_dags/autonomous_fixing --cov-report=term-missing

# === AUTOMATED SCRIPT ===
./scripts/coverage-check.sh
```

---

## 📊 Current Coverage Status

**As of October 5, 2025**:

| Test Tier | Tests | Status | Coverage Contribution |
|-----------|-------|--------|----------------------|
| **Unit** | 246 | ✅ All Pass | ~28% (isolated) |
| **Integration** | 48 | ⚠️ 2 Fail | ~35% (with interactions) |
| **E2E** | 44 | ✅ All Pass | ~40% (full system) |
| **TOTAL** | 338 | ⚠️ 2 Fail | **40% overall** |

---

## 📈 Coverage by Module

| Module | Coverage | Priority | Status |
|--------|----------|----------|--------|
| **core/** | ~65% | 🔴 High | Good |
| **adapters/** | ~70% | 🟡 Medium | Good |
| **domain/models/** | ~85% | 🟡 Medium | Excellent |
| **config/** | ~60% | 🟢 Low | Acceptable |
| **validators/** | ~55% | 🟡 Medium | Needs improvement |

---

## 🎯 Coverage Report Types

### 1. Terminal Output (Fast)
```bash
.venv/bin/python3 -m pytest tests/ \
  --cov=airflow_dags/autonomous_fixing \
  --cov-report=term
```
**Shows**: Coverage percentage per file

### 2. Terminal with Missing Lines (Detailed)
```bash
.venv/bin/python3 -m pytest tests/ \
  --cov=airflow_dags/autonomous_fixing \
  --cov-report=term-missing
```
**Shows**: Coverage % + exact line numbers not covered

### 3. HTML Report (Interactive)
```bash
.venv/bin/python3 -m pytest tests/ \
  --cov=airflow_dags/autonomous_fixing \
  --cov-report=html

# Open in browser
open htmlcov/index.html
```
**Shows**: Visual highlighting of covered/uncovered lines

---

## 🔍 How to Use Coverage Reports

### Step 1: Run Coverage
```bash
.venv/bin/python3 -m pytest tests/ \
  --cov=airflow_dags/autonomous_fixing \
  --cov-report=html
```

### Step 2: Open HTML Report
```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Step 3: Find Coverage Gaps
1. Sort by **Coverage %** (ascending)
2. Look for files < 70% coverage
3. Click on file to see uncovered lines (highlighted in red)

### Step 4: Write Tests
Focus on:
- ❌ Red lines (not executed)
- ⚠️ Yellow lines (partial branch coverage)
- 🎯 Critical business logic paths

---

## 🛠️ Common Workflows

### Daily Development
```bash
# Quick check while coding
.venv/bin/python3 -m pytest tests/unit/test_my_module.py \
  --cov=airflow_dags/autonomous_fixing/core/my_module \
  --cov-report=term-missing
```

### Pre-Commit
```bash
# Full test suite with coverage threshold
.venv/bin/python3 -m pytest tests/ \
  --cov=airflow_dags/autonomous_fixing \
  --cov-fail-under=80 \
  --cov-report=term-missing
```

### Coverage Gap Analysis
```bash
# 1. Generate HTML report
.venv/bin/python3 -m pytest tests/ \
  --cov=airflow_dags/autonomous_fixing \
  --cov-report=html

# 2. Find low coverage files
# 3. Write tests for uncovered lines
# 4. Re-run to verify improvement
```

---

## 📋 Example Output

### Terminal Report
```
---------- coverage: platform linux, python 3.12.3 -----------
Name                                                Stmts   Miss  Cover   Missing
---------------------------------------------------------------------------------
airflow_dags/autonomous_fixing/core/analyzer.py       120     15    88%   45-48, 67
airflow_dags/autonomous_fixing/core/fixer.py          156     28    82%   123-145
airflow_dags/autonomous_fixing/adapters/python.py      89      8    91%   102-105
---------------------------------------------------------------------------------
TOTAL                                                 6893   4122    40%
```

### HTML Report Features
- 📊 Coverage percentage per file/directory
- 🔍 Line-by-line highlighting (green = covered, red = not covered)
- 🌳 Directory tree navigation
- 📈 Coverage trend graphs
- 🔀 Branch coverage visualization

---

## 🎓 Understanding Coverage Numbers

### Coverage Percentage
```
Stmts = 120  (total executable lines)
Miss  = 15   (lines not executed by tests)
Cover = 88%  (percentage covered)
```

### Missing Lines
```
Missing: 45-48, 67
```
Means lines 45, 46, 47, 48, and 67 were never executed during tests.

### Coverage Goals
- **>80%**: Excellent - Strong test coverage
- **60-80%**: Good - Adequate coverage
- **40-60%**: Fair - Needs improvement
- **<40%**: Poor - Critical gaps

---

## 🚨 Troubleshooting

### "No data to report"
**Solution**: Use correct source path
```bash
# ✅ Correct
--cov=airflow_dags/autonomous_fixing

# ❌ Wrong
--cov=air_executor
```

### Old coverage data persists
**Solution**: Clean .coverage file
```bash
rm -f .coverage .coverage.*
```

### htmlcov/ not created
**Solution**: Add `--cov-report=html` flag
```bash
.venv/bin/python3 -m pytest tests/ \
  --cov=airflow_dags/autonomous_fixing \
  --cov-report=html  # ← Add this
```

---

## 📚 Full Documentation

See **`claudedocs/test-coverage-guide.md`** for:
- Advanced coverage techniques
- Branch coverage
- Coverage by specific modules
- CI/CD integration
- Configuration files
- Best practices

---

## 🎯 Quick Wins for Coverage Improvement

### 1. Test Uncovered Core Logic
Priority files (currently < 70%):
- `core/validators/*.py` (~55%)
- `adapters/ai/*.py` (~65%)
- `core/setup_*.py` (~60%)

### 2. Add Edge Case Tests
Focus on:
- Error handling paths
- Boundary conditions
- Null/empty input cases

### 3. Integration Tests
Add tests for:
- Component interactions
- Data flow between modules
- Service integration points

---

## 📞 Need Help?

- **Coverage Tool Docs**: https://coverage.readthedocs.io/
- **Pytest Coverage**: https://pytest-cov.readthedocs.io/
- **Project Tests**: `.claude/CLAUDE.md`
- **E2E Coverage**: `claudedocs/e2e-test-coverage-analysis-2025-10-05.md`
