# Autonomous Code Fixing - Complete Guide

Comprehensive guide for the multi-language, priority-based autonomous code fixing system.

## Table of Contents

- [Overview](#overview)
- [How It Works](#how-it-works)
- [Supported Languages](#supported-languages)
- [Priority-Based Execution](#priority-based-execution)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Running on Real Projects](#running-on-real-projects)
- [Monitoring & Debugging](#monitoring--debugging)
- [Advanced Usage](#advanced-usage)
- [Troubleshooting](#troubleshooting)

## Overview

The Autonomous Code Fixing system provides **automatic code quality improvement** across multiple languages with intelligent priority-based execution and adaptive testing strategies.

### Key Features

✅ **Multi-Language Support**: Python, JavaScript/TypeScript, Flutter/Dart, Go
✅ **Priority-Based Execution**: Focus on quick wins first (P1 → P2 → P3 → P4)
✅ **Adaptive Testing**: Time-aware test strategy based on project health
✅ **Health Monitoring**: Comprehensive metrics (build, tests, coverage, quality)
✅ **Auto-Discovery**: Find and queue fix tasks automatically
✅ **Git Integration**: All changes are commits for easy review
✅ **Safety Features**: Circuit breakers, time limits, validation gates

### Architecture

```
┌────────────────────────────────────────────────────────────┐
│              Orchestrator (Meta-Controller)                │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │ Health Check │→ │ Phase Router │→ │ Completion Gate │  │
│  └──────────────┘  └──────────────┘  └─────────────────┘  │
│                           │                                │
│                    State Store (Redis)                     │
└───────────────────────────┼────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
  ┌──────────┐        ┌──────────┐       ┌──────────┐
  │ P1 Static│        │ P2 Tests │       │ P3 Cover │
  │  Phase   │        │  Phase   │       │  Phase   │
  └──────────┘        └──────────┘       └──────────┘
```

## How It Works

### Execution Flow

```
1. Project Detection
   ├─ Auto-detect language (Python/JS/Flutter/Go)
   ├─ Validate required tools
   └─ Check git status

2. P1: Static Analysis (ALWAYS RUN, ~2 min)
   ├─ Run linters & type checkers in parallel
   ├─ Analyze file sizes & complexity
   ├─ Calculate health score
   └─ Gate: ≥ 90% → Continue, else fix P1 issues

3. P2: Strategic Tests (ADAPTIVE, 5-30 min)
   ├─ Determine strategy based on P1 health:
   │  ├─ < 30% health: Minimal tests (5 min)
   │  ├─ 30-60% health: Selective tests (15 min)
   │  └─ > 60% health: Comprehensive tests (30 min)
   ├─ Run tests with chosen strategy
   └─ Gate: ≥ 85% pass → Continue, else fix P2 issues

4. P3: Coverage Analysis (CONDITIONAL, 20-60 min)
   ├─ Gate check: P1 ≥ 90% AND P2 ≥ 85%?
   ├─ If yes: Analyze coverage gaps
   ├─ Generate tests for uncovered code
   └─ Focus on critical paths

5. P4: E2E Testing (FINAL PHASE, 30-120 min)
   ├─ Gate check: Overall health ≥ 90%?
   ├─ If yes: Run E2E/integration tests
   ├─ Capture runtime errors
   └─ Add regression tests

6. Completion Detection
   ├─ All gates passed?
   ├─ No queued tasks?
   ├─ Stable for 3 runs?
   └─ If all yes: COMPLETE
```

### Health Score Calculation

```python
# Overall Health Score (0-100%)
health_score = (
    build_status * 0.3 +      # 30% - Does it build?
    test_quality * 0.3 +      # 30% - Tests pass + coverage
    code_quality * 0.2 +      # 20% - File size, complexity
    analysis_clean * 0.2      # 20% - Lint errors
)

# Test Quality Score
test_quality = (
    pass_rate * 0.6 +         # 60% - How many tests pass?
    coverage * 0.3 +          # 30% - Code coverage
    diversity * 0.1           # 10% - Has unit + integration?
)

# Code Quality Score
code_quality = (
    size_score * 0.4 +        # 40% - File sizes reasonable?
    complexity_score * 0.4 +  # 40% - Low complexity?
    nesting_score * 0.2       # 20% - Reasonable nesting?
)
```

## Supported Languages

### Python

**Static Analysis (P1):**
- `pylint` - Code quality and errors
- `mypy` - Type checking
- `ruff` - Fast linting (optional)

**Testing (P2):**
- `pytest` - Unit, integration, E2E tests
- Strategies: minimal (`-m "not slow"`), selective (`-m "not integration"`), comprehensive (all)

**Coverage (P3):**
- `pytest --cov` - Coverage analysis
- `pytest --cov-report=json` - Structured output

**Example Configuration:**
```yaml
python:
  linters: ["pylint", "mypy"]
  test_framework: "pytest"
  complexity_threshold: 10
  max_file_lines: 500
  test_markers:
    unit: "not slow and not integration"
    integration: "integration"
    e2e: "e2e"
```

### JavaScript/TypeScript

**Static Analysis (P1):**
- `eslint` - Linting
- `tsc` - TypeScript type checking

**Testing (P2):**
- `jest` or `vitest` - Test runner
- Strategies: minimal (`--testPathPattern=unit`), selective, comprehensive

**Coverage (P3):**
- `jest --coverage` or `vitest --coverage`

**Example Configuration:**
```yaml
javascript:
  linters: ["eslint"]
  type_checker: "tsc"
  test_framework: "jest"  # or "vitest"
  complexity_threshold: 10
  max_file_lines: 500
```

### Flutter/Dart

**Static Analysis (P1):**
- `flutter analyze` - Dart analyzer
- `dart_code_metrics` - Complexity analysis (optional)

**Testing (P2):**
- `flutter test` - Unit and widget tests
- Strategies: minimal (`test/unit/`), selective (`--exclude-tags=integration`), comprehensive (all)

**Coverage (P3):**
- `flutter test --coverage`
- `lcov` format output

**E2E (P4):**
- `flutter test integration_test/`
- `flutter drive` for driver tests

**Example Configuration:**
```yaml
flutter:
  analyzer_args: "--fatal-infos --fatal-warnings"
  test_timeout: 600
  complexity_threshold: 10
  max_file_lines: 500
```

### Go

**Static Analysis (P1):**
- `go vet` - Official Go analysis
- `staticcheck` - Advanced static analysis

**Testing (P2):**
- `go test` - Standard testing
- Strategies: minimal (`-short`), selective (`-tags=!integration`), comprehensive (all)

**Coverage (P3):**
- `go test -cover`
- `go test -coverprofile=coverage.out`

**Example Configuration:**
```yaml
go:
  linters: ["go vet", "staticcheck"]
  test_timeout: 300
  complexity_threshold: 10
  max_file_lines: 500
```

## Priority-Based Execution

### P1: Static Analysis (Fast, ALWAYS RUN)

**Goal**: Fix errors, reduce complexity, improve structure
**Time**: ~30 seconds per language
**Threshold**: 90% success to proceed to P2

**What It Checks:**
- ✅ Compilation/analysis errors
- ✅ File size violations (> 500 lines)
- ✅ Cyclomatic complexity (> 10)
- ✅ Code smells and antipatterns

**Actions:**
- Fix compilation/linting errors
- Refactor large files (Single Responsibility Principle)
- Reduce complexity to make testing easier
- Quick wins for immediate health improvement

**Why First?**
- Fast feedback (seconds, not minutes)
- Foundational: can't test broken code
- Highest ROI: small fixes, big impact

### P2: Strategic Tests (Adaptive, TIME-AWARE)

**Goal**: Verify fixes, ensure stability
**Time**: Adaptive based on P1 health (5-30 minutes)
**Threshold**: 85% pass rate to proceed to P3

**Adaptive Strategy:**

| P1 Health | Strategy | Duration | What Runs |
|-----------|----------|----------|-----------|
| < 30% | **Minimal** | 5 min | Critical tests only |
| 30-60% | **Selective** | 15 min | Changed files + smoke tests |
| > 60% | **Comprehensive** | 30 min | Full test suite |

**Why Adaptive?**
- Unhealthy projects need fast feedback, not slow comprehensive tests
- Healthy projects can afford thorough validation
- 40-70% time savings on problematic projects

**Actions:**
- Run tests with appropriate strategy
- Fix failing tests
- Ensure test stability

### P3: Coverage Improvements (CONDITIONAL)

**Goal**: Increase test coverage strategically
**Trigger**: P1 ≥ 90% AND P2 ≥ 85%
**Time**: 20-60 minutes

**Smart Coverage:**
- Analyze coverage gaps
- Prioritize: Critical paths > Common flows > Edge cases
- Generate tests for uncovered code
- Focus on high-value, low-coverage areas

**Actions:**
- Identify files with < 50% coverage
- Generate meaningful tests (not just coverage games)
- Ensure edge cases are covered

**Why Conditional?**
- No point adding tests if basics are broken
- Saves 20-60 minutes when not ready

### P4: E2E & Runtime Testing (FINAL PHASE)

**Goal**: Catch runtime errors, add regression tests
**Trigger**: Overall health ≥ 90%
**Time**: 30-120 minutes

**E2E Strategy:**
1. Start real server/application
2. Run E2E test suite
3. Capture runtime errors
4. Fix runtime issues
5. Add regression tests to prevent recurrence

**Why Last?**
- Most expensive (time and resources)
- Only valuable when project is stable
- Saves 30-120 minutes on unstable projects

## Quick Start

### KISS Principle: Simple Commands That Work

**Prerequisites** (one-time setup):
```bash
# Install development tools
./scripts/setup_python.sh      # Python tools
./scripts/setup_javascript.sh  # JavaScript/TypeScript tools
./scripts/setup_go.sh           # Go tools (including SDK)
./scripts/setup_flutter.sh      # Flutter SDK

# Verify installation
./scripts/check_tools.sh
```

### Single Project Execution

```bash
# Run any project - handles Python environment automatically
./scripts/run_autonomous_fix.sh config/projects/my-project.yaml

# Or run in background
./scripts/run_autonomous_fix.sh config/projects/my-project.yaml --background

# Monitor progress
tail -f logs/orchestrator_run.log

# Check results
cd /path/to/project
git log --oneline -5
```

### All Projects with PM2

```bash
# Start all projects
pm2 start config/pm2.config.js

# Start specific project
pm2 start config/pm2.config.js --only fix-my-project

# Monitor logs
pm2 logs
pm2 logs fix-my-project

# Check status
pm2 status

# Stop all
pm2 stop all
```

### Available Project Configurations

| Project | Language | Config |
|---------|----------|--------|
| **air-executor** | Python | `config/projects/air-executor.yaml` |
| **cc-task-manager** | JavaScript | `config/projects/cc-task-manager.yaml` |
| **mind-training** | JavaScript | `config/projects/mind-training.yaml` |
| **money-making-app** | Flutter | `config/projects/money-making-app.yaml` |
| **warps** | TypeScript | `config/projects/warps.yaml` |

## Configuration

### Project Configuration Template

```yaml
# config/projects/my-project.yaml

# Project identification
project_name: "my-project"
project_path: "/path/to/my-project"
language: "python"  # python | javascript | flutter | go

# Tool validation
validate_tools: true
required_tools:
  - pylint    # Language-specific
  - mypy
  - pytest

# Priority thresholds
priorities:
  p1_static:
    enabled: true
    max_duration_seconds: 120
    success_threshold: 0.90  # 90% to proceed

  p2_tests:
    enabled: true
    adaptive_strategy: true  # Enable adaptive testing
    time_budgets:
      minimal: 300           # 5 min when health < 30%
      selective: 900         # 15 min when health 30-60%
      comprehensive: 1800    # 30 min when health > 60%
    success_threshold: 0.85  # 85% pass to proceed

  p3_coverage:
    enabled: true
    gate_requirements:
      p1_score: 0.90  # P1 must be 90%+
      p2_score: 0.85  # P2 must be 85%+
    max_duration_seconds: 3600
    target_coverage: 0.80  # Aim for 80% coverage

  p4_e2e:
    enabled: false  # Usually disabled initially
    gate_requirements:
      overall_health: 0.90  # Overall health must be 90%+
    max_duration_seconds: 7200
    retry_on_flaky: true

# Execution strategy
execution:
  max_iterations: 5              # Stop after 5 fix cycles
  max_duration_hours: 2          # Time limit
  auto_commit: true              # Auto-commit fixes
  fail_fast: false               # Continue even if one phase fails
  parallel_languages: true       # Run language checks in parallel

# Issue grouping (batch size control)
issue_grouping:
  mega_batch_mode: false         # false = smaller, reviewable commits
  max_cleanup_batch_size: 30     # Max cleanup issues per batch
  max_location_batch_size: 15    # Max location-based issues per batch

# Logging
logging:
  level: "INFO"                  # DEBUG | INFO | WARNING | ERROR
  file: "logs/my-project.log"    # Log file path
  structured_debug: true         # Enable structured JSON debug logs

# Language-specific settings
python:
  linters: ["pylint", "mypy"]
  test_framework: "pytest"
  complexity_threshold: 10
  max_file_lines: 500

# Project-specific overrides
project_overrides:
  thresholds:
    p1_static: 0.85  # Override if project has many issues
    p2_tests: 0.75
```

### PM2 Configuration

```javascript
// config/pm2.config.js
module.exports = {
  apps: [
    {
      name: 'fix-air-executor',
      script: './scripts/run_autonomous_fix.sh',
      args: 'config/projects/air-executor.yaml',
      interpreter: 'bash',
      autorestart: false,  // Run once
      max_restarts: 0,
      out_file: './logs/fix-air-executor-out.log',
      error_file: './logs/fix-air-executor-error.log',
    },
    {
      name: 'fix-money-making-app',
      script: './scripts/run_autonomous_fix.sh',
      args: 'config/projects/money-making-app.yaml',
      interpreter: 'bash',
      autorestart: false,
      max_restarts: 0,
      out_file: './logs/fix-money-making-app-out.log',
      error_file: './logs/fix-money-making-app-error.log',
    },
    // Add more projects...
  ]
};
```

## Running on Real Projects

### Recommended Workflow

**Phase 1: Test Run (Recommended First)**

```bash
# 1. Verify prerequisites
./scripts/check_tools.sh

# 2. Test on ONE project first
./scripts/run_autonomous_fix.sh config/projects/air-executor.yaml

# 3. Monitor execution
tail -f logs/orchestrator_run.log

# 4. Review commits
cd /path/to/project
git log --oneline -5
git show HEAD  # Review latest commit

# 5. If good, proceed to all projects
```

**Phase 2: Gradual Rollout**

```bash
# Start with minimal iterations
vim config/projects/my-project.yaml
# Set: max_iterations: 1

# Run single iteration
./scripts/run_autonomous_fix.sh config/projects/my-project.yaml

# Review changes
git diff HEAD~1 HEAD

# If good, increase iterations
# Set: max_iterations: 3
# Then: max_iterations: 5
```

**Phase 3: Full Automation**

```bash
# Configure all projects
ls config/projects/*.yaml

# Start PM2
pm2 start config/pm2.config.js

# Monitor
pm2 logs
pm2 monit

# Let it run...
```

### Safety Features

✅ **All changes are commits** - Easy to review and revert
✅ **No auto-push** - You control when changes go remote
✅ **Git status check** - Warns about uncommitted changes
✅ **Branch aware** - Works on current branch
✅ **Time limits** - Won't run forever (max_duration_hours)
✅ **Circuit breakers** - Stops on repeated failures
✅ **Validation gates** - Ensures quality before proceeding

### Rollback if Needed

```bash
# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes)
git reset --hard HEAD~1

# Undo multiple commits
git reset --hard HEAD~5

# Undo all autonomous changes
git reset --hard <commit-before-autonomous-run>
```

## Monitoring & Debugging

### Real-Time Monitoring

**Main Output:**
```bash
# Watch main orchestrator log
tail -f logs/orchestrator_run.log

# Expected output:
# ================================================================================
# 📍 PRIORITY 1: Fast Static Analysis
# ================================================================================
# 🔍 PYTHON: Analyzing 1 project(s)...
#    📁 /path/to/project
#       Issues: 12 (errors: 5, size: 3, complexity: 4)
# 📊 Phase Result:
#    Score: 92.5%
#    Time: 45.3s
#    ✅ Gate PASSED
```

**Structured Debug Logs:**
```bash
# Watch debug events (JSON)
tail -f logs/debug/multi-project_*.jsonl

# Filter specific events
cat logs/debug/*.jsonl | jq 'select(.event == "wrapper_call")'
cat logs/debug/*.jsonl | jq 'select(.event == "health_check")'

# View timeline
cat logs/debug/*.jsonl | jq -r '"\(.timestamp) \(.event) \(.message)"'
```

**PM2 Monitoring:**
```bash
# Live logs
pm2 logs

# Specific project
pm2 logs fix-my-project

# Interactive monitoring
pm2 monit

# Check status
pm2 status

# Detailed process info
pm2 show fix-my-project
```

### Git Monitoring

```bash
# Check commits in real-time
watch -n 5 'git log --oneline -5'

# View specific project
cd /path/to/project
git log --oneline --since="1 hour ago"

# See all changes from autonomous run
git log --oneline --grep="fix:"
git log --oneline --author="Claude"

# Review changes by file
git diff HEAD~5 HEAD --stat
```

### Health Metrics

```bash
# Quick health check (no tests, ~30s)
python airflow_dags/autonomous_fixing/enhanced_health_monitor.py \
  /path/to/project

# With tests (~2-5 min)
python airflow_dags/autonomous_fixing/enhanced_health_monitor.py \
  /path/to/project --tests

# Full analysis with coverage (~5-10 min)
python airflow_dags/autonomous_fixing/enhanced_health_monitor.py \
  /path/to/project --tests --coverage

# Code quality only (~10s)
python airflow_dags/autonomous_fixing/code_metrics.py \
  /path/to/project --threshold=300

# Test breakdown (~2-5 min)
python airflow_dags/autonomous_fixing/test_metrics.py \
  /path/to/project
```

### Debug Mode

```bash
# Enable debug logging
export DEBUG=1
./scripts/run_autonomous_fix.sh config/projects/my-project.yaml

# Or edit config
vim config/projects/my-project.yaml
# Set: logging.level: "DEBUG"
```

## Advanced Usage

### Custom Priority Thresholds

For projects with many issues, lower thresholds:

```yaml
priorities:
  p1_static:
    success_threshold: 0.75  # Instead of 0.90
  p2_tests:
    success_threshold: 0.60  # Instead of 0.85
```

### Enable Coverage Phase

Only after P1 and P2 are clean:

```yaml
priorities:
  p3_coverage:
    enabled: true
    gate_requirements:
      p1_score: 0.90
      p2_score: 0.85
```

### Adjust Batch Sizes

Control commit granularity:

```yaml
issue_grouping:
  mega_batch_mode: false       # Smaller commits
  max_cleanup_batch_size: 10   # Smaller batches
  max_location_batch_size: 5
```

### Run More Iterations

For projects needing deep work:

```yaml
execution:
  max_iterations: 10           # More fix cycles
  max_duration_hours: 4        # Longer time limit
```

### Focus on One Language

```yaml
languages:
  enabled:
    - python  # Only this one
  auto_detect: false
```

### Project-Specific Tool Configuration

```yaml
python:
  linters: ["pylint", "mypy", "ruff"]  # Add ruff
  test_framework: "pytest"
  pytest_args: "-v --tb=short"         # Custom pytest args
  complexity_threshold: 15             # Higher threshold
  max_file_lines: 800                  # Larger files OK
```

## Troubleshooting

### No Projects Detected

```bash
# Check if project markers exist
ls -la **/pubspec.yaml   # Flutter
ls -la **/package.json   # JavaScript
ls -la **/go.mod         # Go
ls -la **/setup.py       # Python

# Enable debug mode
python airflow_dags/autonomous_fixing/multi_language_orchestrator.py \
  config/projects/my-project.yaml --debug
```

### P1 Gate Not Passing

```
Issue: P1 score (75%) < threshold (90%)
```

**Solution 1: Fix issues manually first**
```bash
# Review P1 issues
cat logs/orchestrator_run.log | grep "P1.*Issues"

# Fix manually, then re-run
```

**Solution 2: Lower threshold temporarily**
```yaml
priorities:
  p1_static:
    success_threshold: 0.70  # Temporarily lower
```

### Tests Timing Out

```
Issue: Tests exceeding time budget
```

**Solution 1: Use minimal strategy**
```yaml
p2_tests:
  time_budgets:
    minimal: 180   # Reduce from 300 to 180 seconds
```

**Solution 2: Increase timeouts**
```yaml
python:
  test_timeout: 900  # 15 minutes instead of default
```

**Solution 3: Parallelize tests**
```bash
# For pytest
pytest -n auto  # Auto-detect CPU count

# For jest
jest --maxWorkers=50%
```

### Coverage Analysis Skipped

```
Issue: P3 skipped - gate not met
Reason: P1 = 85% (need 90%) OR P2 = 80% (need 85%)
```

**Solution**: Fix P1/P2 first before coverage:
```bash
# Focus on P1 and P2 only
vim config/projects/my-project.yaml
# Set: p3_coverage.enabled: false

# Run until P1 and P2 are healthy
./scripts/run_autonomous_fix.sh config/projects/my-project.yaml

# Then enable P3
# Set: p3_coverage.enabled: true
```

### No Commits Created

**Possible causes:**

1. **Projects already healthy**
   ```bash
   # Check health
   cat logs/orchestrator_run.log | grep "Overall Health"
   # If > 90%, project is already healthy
   ```

2. **Gates not passing**
   ```bash
   # Look for gate failures
   cat logs/orchestrator_run.log | grep "Gate"
   # Adjust thresholds if needed
   ```

3. **No issues discovered**
   ```bash
   # Check issue discovery
   cat logs/orchestrator_run.log | grep "Issues discovered"
   ```

4. **Claude wrapper failing**
   ```bash
   # Test wrapper manually
   echo '{"action":"prompt","prompt":"Hello","options":{"cwd":"."}}' | \
     python scripts/claude_wrapper.py
   ```

### Process Hangs

```bash
# Check if actually running (analysis takes time)
ps aux | grep multi_language_orchestrator

# Check debug logs for progress
tail -f logs/debug/multi-project_*.jsonl

# Typical phase durations:
# - Test discovery: 5-10s
# - Static analysis: 30-120s
# - Test execution: 60-300s
# - Fix iteration: 30-60s
```

### Permission Errors

```bash
# Make scripts executable
chmod +x scripts/*.sh

# Check file permissions
ls -l scripts/
```

### Redis Errors

```bash
# Check Redis is running
redis-cli ping  # Should return PONG

# Start Redis if not running
redis-server &

# Check Redis logs
redis-cli MONITOR
```

## Best Practices

### 1. Start Small
- Test on one project first
- Review first commits carefully
- Scale gradually

### 2. Monitor Actively
- Watch logs during first runs
- Check commits frequently
- Use PM2 for visibility

### 3. Adjust Thresholds
- Lower thresholds for problematic projects
- Raise thresholds as health improves
- Use project-specific overrides

### 4. Respect Priority Gates
- Don't skip to P3/P4 if P1/P2 aren't healthy
- Fix basics first
- Coverage and E2E are final polish

### 5. Incremental Improvements
- Focus on P1 → P2 → P3 → P4 progression
- Don't expect perfection immediately
- Celebrate small wins

### 6. Review Before Push
- Always review commits before pushing
- Test manually after autonomous run
- Ensure quality of generated fixes

### 7. Use Branches
- Create feature branch for autonomous fixes
- Review as pull request
- Merge after validation

## Performance Benchmarks

### Single Language (Python only)
- P1: 30-60 seconds
- P2: 5-30 minutes (adaptive)
- P3: 20-40 minutes (if gate passed)
- P4: 30-60 minutes (if health ≥ 90%)

### Multi-Language (4 languages, parallel)
- P1: 60-90 seconds (all languages in parallel)
- P2: 15-30 minutes (adaptive per language)
- P3: 40-80 minutes (if gate passed)
- P4: 60-120 minutes (if health ≥ 90%)

### Efficiency Gains

**Old System** (no prioritization):
- All checks every time: 30-60 min
- No health-based adaptation
- Wasted time on coverage when basics broken

**New System** (priority-based):
- Fast static first: 2 min
- Adaptive testing: 5-30 min (based on health)
- Coverage only when ready: Saves 20-60 min
- E2E only when stable: Saves 30-120 min

**Result**: 40-70% time savings on unhealthy projects

## Next Steps

- **For Configuration**: See [CONFIGURATION.md](./CONFIGURATION.md)
- **For Architecture**: See [ARCHITECTURE.md](./ARCHITECTURE.md)
- **For Getting Started**: See [GETTING_STARTED.md](./GETTING_STARTED.md)
- **For Troubleshooting**: See [reference/troubleshooting.md](./reference/troubleshooting.md)

---

**Ready to Start!**

```bash
# Verify prerequisites
./scripts/check_tools.sh

# Test on single project
./scripts/run_autonomous_fix.sh config/projects/my-project.yaml

# Monitor progress
tail -f logs/orchestrator_run.log
```

**Happy Autonomous Fixing! 🚀**
