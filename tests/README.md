# Multi-Language Test Projects

Sample projects for testing the multi-language autonomous fixing orchestrator.

## Overview

This directory contains **3 small sample projects** with intentional bugs for testing:

- **`sample_python_project/`** - Python project with pylint/mypy errors, failing tests, low coverage
- **`sample_javascript_project/`** - TypeScript project with eslint/tsc errors, failing tests, low coverage
- **`sample_go_project/`** - Go project with vet errors, failing tests, low coverage

Each project is designed to:
- ✅ Run **fast** (< 1 minute for all tests combined)
- ✅ Have **intentional issues** for each priority phase (P1/P2/P3)
- ✅ Test the **multi-language orchestrator** thoroughly

## Quick Start

```bash
# Run the test runner (creates tmp dir, copies projects, runs orchestrator)
./run_multi_language_test.sh
```

This will:
1. Create a tmp directory with timestamp
2. Copy all sample projects
3. Initialize git repositories for each
4. Run the multi-language orchestrator
5. Show commits made by Claude
6. Provide commands to inspect results

**Each run is independent** - you get a fresh tmp directory every time!

## What the Test Runner Does

### 1. Creates Clean Environment
```
tests/tmp_test_run_20251003_143052/
├── sample_python_project/        # Fresh copy with git
├── sample_javascript_project/    # Fresh copy with git
├── sample_go_project/            # Fresh copy with git
└── test_config.yaml              # Auto-generated config
```

### 2. Initializes Git Repos
Each project gets:
- `git init`
- Initial commit with all the buggy code
- Configured user (Test User <test@example.com>)
- `.gitignore` for dependencies

### 3. Runs Orchestrator
Executes multi-language orchestrator with test config pointing to tmp directory.

### 4. Shows Results
- Git commit history for each project
- Changes made by Claude
- Commits with fix messages

## Sample Projects Structure

### Python Project
```
sample_python_project/
├── setup.py
├── requirements.txt
├── pytest.ini
├── src/
│   ├── __init__.py
│   ├── calculator.py         # Unused import, missing types, high complexity
│   └── large_module.py        # 530+ lines (exceeds 500 threshold)
└── tests/
    ├── __init__.py
    └── test_calculator.py     # 2 failing tests, missing coverage
```

**Intentional Issues**:
- P1: Unused import (os), missing type hints, complexity > 10, file > 500 lines
- P2: 2/8 tests fail (75% pass rate < 85% threshold)
- P3: 2 functions with 0% coverage (advanced_math, handle_edge_cases)

### JavaScript/TypeScript Project
```
sample_javascript_project/
├── package.json
├── tsconfig.json
├── jest.config.js
├── .eslintrc.js
└── src/
    ├── calculator.ts          # Unused import, missing return type, high complexity
    ├── largeModule.ts         # 550+ lines (exceeds 500 threshold)
    └── calculator.test.ts     # 2 failing tests, missing coverage
```

**Intentional Issues**:
- P1: Unused import (path), missing return type, complexity > 10, file > 500 lines
- P2: 2/11 tests fail (82% pass rate < 85% threshold)
- P3: 2 functions with 0% coverage (advancedMath, handleEdgeCases)

### Go Project
```
sample_go_project/
├── go.mod
├── calculator.go              # Unused import, high complexity
├── large_module.go            # 550+ lines (exceeds 500 threshold)
├── calculator_test.go         # 2 failing tests, missing coverage
└── main.go
```

**Intentional Issues**:
- P1: Unused import (fmt), complexity > 10, file > 500 lines
- P2: 2/8 tests fail (75% pass rate < 85% threshold)
- P3: 2 functions with 0% coverage (AdvancedMath, HandleEdgeCases)

## Expected Orchestrator Behavior

### Priority 1: Static Analysis
- **Python**: Detect unused imports, missing types, high complexity, large file
- **JavaScript**: Detect unused imports, missing return types, high complexity, large file
- **Go**: Detect unused imports, high complexity, large file
- **Score**: ~60-70% (below 90% threshold)
- **Result**: ❌ Gate NOT passed → Fix P1 issues first

### Priority 2: Strategic Tests
- **Strategy**: Likely "minimal" (health < 30%) or "selective" (health 30-60%)
- **Python**: 6 pass, 2 fail = 75%
- **JavaScript**: 9 pass, 2 fail = 82%
- **Go**: 6 pass, 2 fail = 75%
- **Score**: ~77% (below 85% threshold)
- **Result**: ❌ Gate NOT passed → Fix P2 test failures

### Priority 3: Coverage
- **Gate**: Requires P1 ≥ 90% AND P2 ≥ 85%
- **Result**: ⏭️ Skipped (gates not met)

### Priority 4: E2E
- **Gate**: Requires overall health ≥ 90%
- **Result**: ⏭️ Skipped (gates not met)

## Inspecting Results

After running the test:

```bash
# Go to a project
cd tests/tmp_test_run_TIMESTAMP/sample_python_project

# View commit history
git log --oneline

# See what changed in latest commit
git show HEAD

# View diff from initial commit
git diff HEAD~1 HEAD

# See changes by file
git diff HEAD~1 HEAD --stat

# View specific file changes
git diff HEAD~1 HEAD src/calculator.py
```

## Running Tests Manually

### Python
```bash
cd tests/tmp_test_run_TIMESTAMP/sample_python_project

# Run tests
pytest

# Run with coverage
pytest --cov=src --cov-report=term

# Run static analysis
pylint src/
mypy src/
```

### JavaScript/TypeScript
```bash
cd tests/tmp_test_run_TIMESTAMP/sample_javascript_project

# Install dependencies first
npm install

# Run tests
npm test

# Run with coverage
npm run test:coverage

# Run linter
npm run lint

# Type check
npm run typecheck
```

### Go
```bash
cd tests/tmp_test_run_TIMESTAMP/sample_go_project

# Run tests
go test -v ./...

# Run with coverage
go test -cover ./...

# Run static analysis
go vet ./...
staticcheck ./...  # if installed
```

## Cleaning Up

```bash
# Remove a specific test run
rm -rf tests/tmp_test_run_20251003_143052

# Remove all test runs
rm -rf tests/tmp_test_run_*

# Keep only the 3 most recent test runs
ls -t tests/tmp_test_run_* | tail -n +4 | xargs rm -rf
```

## Customizing Test Runs

Edit `run_multi_language_test.sh` to:

### Enable/Disable Languages
```bash
# Comment out projects you don't want to test
# Copy Python project
if [ -d "${SCRIPT_DIR}/sample_python_project" ]; then
    # ... copy logic
fi
```

### Change Priority Gates
Modify the generated `test_config.yaml`:
```yaml
priorities:
  p1_static:
    success_threshold: 0.80  # Lower to 80% to pass gate

  p2_tests:
    success_threshold: 0.70  # Lower to 70% to pass gate
```

### Enable P4 E2E Testing
```yaml
priorities:
  p4_e2e:
    enabled: true  # Change to true
```

## Troubleshooting

### Test runner fails immediately
```bash
# Check prerequisites
ls ~/.venv/air-executor/bin/python  # Should exist
redis-cli ping  # Should return PONG

# Install dependencies
pip install -r tests/sample_python_project/requirements.txt
cd tests/sample_javascript_project && npm install
cd tests/sample_go_project && go mod download
```

### Orchestrator shows no commits
- This is **expected** if health scores don't improve enough
- Check tmp directory - projects are still there
- Manually inspect what would need fixing:
  ```bash
  cd tests/tmp_test_run_TIMESTAMP/sample_python_project
  pytest  # See test failures
  pylint src/  # See static errors
  ```

### Want to test fixing manually
```bash
# Use Claude wrapper directly in a tmp project
cd tests/tmp_test_run_TIMESTAMP/sample_python_project

echo '{"action":"prompt","prompt":"Fix all pylint errors in src/calculator.py","options":{"cwd":"."}}' | \
  ~/.venv/air-executor/bin/python \
  ../../scripts/claude_wrapper.py
```

## Performance Benchmarks

Expected execution times (for all 3 projects):

- **Project Setup**: 1-2 seconds
- **P1 Static Analysis**: 5-10 seconds (all languages parallel)
- **P2 Tests** (minimal): 10-20 seconds
- **P2 Tests** (selective): 30-60 seconds
- **Total**: < 2 minutes for complete test run

Much faster than real projects (which take 10-30 minutes)!

## Next Steps

1. **Run the test**: `./run_multi_language_test.sh`
2. **Inspect results**: Look at commits in tmp directory
3. **Iterate**: Run again to see if fixes accumulate
4. **Integrate**: Use learnings to improve orchestrator
5. **Add more tests**: Create additional sample projects for edge cases

## See Also

- `../docs/MULTI_LANGUAGE_ARCHITECTURE.md` - Architecture design
- `../docs/MULTI_LANGUAGE_USAGE.md` - Usage guide
- `../config/multi_language_fix.yaml` - Production config
