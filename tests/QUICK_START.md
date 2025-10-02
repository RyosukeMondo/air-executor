# Quick Start - Multi-Language Test Suite

## TL;DR

```bash
cd /home/rmondo/repos/air-executor/tests
./run_multi_language_test.sh
```

## What You Get

✅ **3 sample projects** (Python, JavaScript/TypeScript, Go)
✅ **Tmp directory** with fresh copies + git repos
✅ **Auto-run** multi-language orchestrator
✅ **See commits** Claude makes to fix issues
✅ **Run multiple times** - each run is independent

## Expected Output

```
================================================================================================
🧪 Multi-Language Autonomous Fixing - Test Runner
================================================================================================

Test directory: /home/rmondo/repos/air-executor/tests/tmp_test_run_20251003_143052

📁 Step 1: Creating temporary test directory...
✓ Created: /home/rmondo/repos/air-executor/tests/tmp_test_run_20251003_143052

📦 Step 2: Copying sample projects...
   ✓ Python project copied
   ✓ JavaScript/TypeScript project copied
   ✓ Go project copied

📝 Step 3: Initializing git repositories...
   ✓ Git initialized for Python
     Commit: a1b2c3d - Initial commit
   ✓ Git initialized for JavaScript/TypeScript
     Commit: e4f5g6h - Initial commit
   ✓ Git initialized for Go
     Commit: i7j8k9l - Initial commit

⚙️  Step 4: Creating test configuration...
✓ Test config created

📊 Step 5: Project Status (Before Fixing)
...

🚀 Step 6: Running Multi-Language Orchestrator
...

📊 Step 7: Results Summary
=== Python ===
   Git History:
     a1b2c3d Initial commit: Python with intentional bugs
...

✅ Test Run Complete
```

## After the Test

### View Commits
```bash
cd tests/tmp_test_run_TIMESTAMP/sample_python_project
git log --oneline
```

### See Changes
```bash
git show HEAD
git diff HEAD~1 HEAD
```

### Run Tests Manually
```bash
# Python
pytest

# JavaScript (after npm install)
npm test

# Go
go test ./...
```

### Clean Up
```bash
rm -rf tests/tmp_test_run_TIMESTAMP
```

## Sample Projects Summary

| Project | P1 Issues | P2 Issues | P3 Issues | Test Time |
|---------|-----------|-----------|-----------|-----------|
| **Python** | Unused imports, complexity, file size | 2 failing tests (75%) | 0% coverage on 2 functions | ~5 sec |
| **JavaScript** | Unused imports, missing types, complexity | 2 failing tests (82%) | 0% coverage on 2 functions | ~10 sec |
| **Go** | Unused imports, complexity, file size | 2 failing tests (75%) | 0% coverage on 2 functions | ~3 sec |

**Total test time**: < 1 minute for all 3 projects!

## Troubleshooting

**Script won't run?**
```bash
chmod +x run_multi_language_test.sh
```

**No Python venv?**
```bash
python -m venv ~/.venv/air-executor
source ~/.venv/air-executor/bin/activate
pip install redis pyyaml
```

**Redis not running?**
```bash
redis-server &
redis-cli ping  # Should return PONG
```

## Next: Test with Real Project

Once you've verified the test suite works:

1. Update `config/multi_language_fix.yaml` with real monorepo path
2. Run on actual codebase
3. See multi-language orchestrator fix real issues!
