# Multi-Language Autonomous Fixing - Usage Guide

Complete guide for using the priority-based, multi-language autonomous fixing system.

## Quick Start

```bash
# 1. Configure your monorepo in config/multi_language_fix.yaml
target_project: "/path/to/your/monorepo"

# 2. Enable languages you use
languages:
  enabled:
    - flutter
    - python
    - javascript
    - go

# 3. Run the orchestrator
python airflow_dags/autonomous_fixing/multi_language_orchestrator.py \
    config/multi_language_fix.yaml
```

## How It Works

### Priority-Based Execution

The system uses a **4-priority execution strategy** with intelligent gates:

```
P1: Static Analysis (ALWAYS)
    ↓ (90% threshold)
P2: Unit Tests (ADAPTIVE)
    ↓ (85% threshold)
P3: Coverage (CONDITIONAL)
    ↓ (90% health)
P4: E2E Tests (FINAL)
```

### Execution Flow

```
1. Auto-detect projects → Find all Flutter, Python, JS, Go projects

2. P1: Static Analysis (parallel, ~2 min total)
   ├─ Flutter: flutter analyze + complexity
   ├─ Python: pylint + mypy
   ├─ JS/TS: eslint + tsc
   └─ Go: go vet + staticcheck

   Gate: P1 score ≥ 90%? → Continue, else fix P1 issues

3. P2: Strategic Tests (adaptive, 5-30 min)
   Strategy based on P1 health:
   ├─ < 30%: minimal tests (5 min)
   ├─ 30-60%: selective tests (15 min)
   └─ > 60%: comprehensive tests (30 min)

   Gate: P2 score ≥ 85%? → Continue, else fix P2 issues

4. P3: Coverage Analysis (conditional, ~60 min)
   Only if: P1 ≥ 90% AND P2 ≥ 85%
   ├─ Run coverage analysis
   ├─ Identify gaps (< 50% coverage)
   └─ Generate tests for uncovered code

5. P4: E2E Testing (conditional, ~120 min)
   Only if: Overall health ≥ 90%
   ├─ Start application
   ├─ Run E2E tests
   ├─ Capture runtime errors
   └─ Add regression tests
```

## Time-Aware Test Strategy

The system **adapts test execution time** based on project health:

### Minimal Strategy (Health < 30%)
```yaml
Duration: ~5 minutes
What runs:
  - Flutter: test/unit/ only
  - Python: pytest -m "not slow"
  - JavaScript: --testPathPattern=unit --bail
  - Go: go test -short

Why: Low health = many errors, focus on quick validation
```

### Selective Strategy (Health 30-60%)
```yaml
Duration: ~15 minutes
What runs:
  - Flutter: All except integration tests
  - Python: pytest -m "not integration"
  - JavaScript: unit + integration tests
  - Go: go test -tags=!integration

Why: Medium health = selective validation of changes
```

### Comprehensive Strategy (Health > 60%)
```yaml
Duration: ~30 minutes
What runs:
  - Flutter: Full test suite
  - Python: pytest (all tests)
  - JavaScript: npm test (all)
  - Go: go test ./...

Why: Good health = thorough validation before coverage/E2E
```

## Configuration

### Language-Specific Settings

#### Flutter
```yaml
flutter:
  analyzer_args: "--fatal-infos --fatal-warnings"
  test_timeout: 600
  complexity_threshold: 10
  max_file_lines: 500
```

#### Python
```yaml
python:
  linters:
    - "pylint"    # Code quality
    - "mypy"      # Type checking
  test_framework: "pytest"
  complexity_threshold: 10
  max_file_lines: 500
```

#### JavaScript/TypeScript
```yaml
javascript:
  linters:
    - "eslint"
  type_checker: "tsc"
  test_framework: "jest"  # or "vitest"
  complexity_threshold: 10
  max_file_lines: 500
```

#### Go
```yaml
go:
  linters:
    - "go vet"
    - "staticcheck"
  test_timeout: 300
  complexity_threshold: 10
  max_file_lines: 500
```

### Priority Gates

Control when each priority phase runs:

```yaml
priorities:
  p1_static:
    success_threshold: 0.90  # Must reach 90% to proceed

  p2_tests:
    success_threshold: 0.85  # Must reach 85% to proceed

  p3_coverage:
    gate_requirements:
      p1_score: 0.90  # P1 must be 90%+
      p2_score: 0.85  # P2 must be 85%+

  p4_e2e:
    gate_requirements:
      overall_health: 0.90  # Overall must be 90%+
```

## Monorepo Structure Support

The system auto-detects projects in various monorepo structures:

### Example: Multi-Language Monorepo
```
/monorepo
  /mobile_app/          # Flutter
    pubspec.yaml
    lib/
    test/

  /backend_api/         # Python
    setup.py
    src/
    tests/

  /web_frontend/        # TypeScript
    package.json
    src/
    __tests__/

  /microservices/       # Go
    go.mod
    cmd/
    pkg/
    *_test.go
```

### Detection Output
```
📦 Detected Projects:
   FLUTTER: 1 project(s)
      - /monorepo/mobile_app
   PYTHON: 1 project(s)
      - /monorepo/backend_api
   JAVASCRIPT: 1 project(s)
      - /monorepo/web_frontend
   GO: 1 project(s)
      - /monorepo/microservices
```

## Coverage Improvements

When P3 (Coverage) runs, the system:

1. **Analyzes coverage gaps**:
   - Files with < 50% coverage
   - Uncovered critical paths
   - Missing edge case tests

2. **Generates tests** for:
   - Critical business logic
   - Public APIs
   - Error handling paths

3. **Ensures quality**:
   - Meaningful assertions
   - Edge cases covered
   - Happy path + error scenarios

### Coverage Generation Prompt Example
```
Generate comprehensive tests for uncovered function: calculateTax()

Current coverage: 15%
Function location: lib/utils/tax_calculator.dart:45

Generate tests covering:
- Happy path: Valid inputs with expected tax amounts
- Edge cases: Zero amount, negative values, boundary conditions
- Error conditions: Null inputs, invalid tax rates

Requirements:
- Use meaningful test names
- Add clear assertions
- Cover all branches
```

## E2E Testing & Runtime Errors

When P4 (E2E) runs, the system:

1. **Starts the application**:
   - Flutter: Integration tests or `flutter drive`
   - Python: Start server, run E2E tests
   - JavaScript: Playwright/Cypress tests
   - Go: Integration tests with tags

2. **Captures runtime errors**:
   - Uncaught exceptions
   - API failures
   - UI rendering errors
   - Performance issues

3. **Adds regression tests**:
   ```python
   # Example: Captured runtime error
   def test_regression_user_profile_null_check():
       """Regression test for NullPointerException in user profile"""
       user = create_test_user(email=None)  # Previously crashed
       response = get_user_profile(user.id)
       assert response.status_code == 400  # Now handled gracefully
   ```

## Output Examples

### Successful P1 Execution
```
================================================================================
📍 PRIORITY 1: Fast Static Analysis
================================================================================

🔍 FLUTTER: Analyzing 1 project(s)...
   📁 /monorepo/mobile_app
      Issues: 12 (errors: 5, size: 3, complexity: 4)

🔍 PYTHON: Analyzing 1 project(s)...
   📁 /monorepo/backend_api
      Issues: 3 (errors: 2, size: 0, complexity: 1)

📊 Phase Result:
   Score: 92.5%
   Time: 45.3s
   ✅ Gate PASSED
```

### Adaptive P2 Execution
```
================================================================================
📍 PRIORITY 2: Strategic Unit Tests (Time-Aware)
================================================================================
📊 Test strategy: SELECTIVE (based on P1 health: 92.5%)

🧪 FLUTTER: Running selective tests...
   📁 /monorepo/mobile_app
      Running selective tests (changed files + smoke tests, ~15 min)
      Results: 145/150 passed

🧪 PYTHON: Running selective tests...
   📁 /monorepo/backend_api
      Running selective tests (changed files + smoke tests, ~15 min)
      Results: 89/92 passed

📊 Phase Result:
   Score: 96.3%
   Time: 18.7 min
   ✅ Gate PASSED
```

### Conditional P3 Execution
```
================================================================================
📍 PRIORITY 3: Coverage Analysis & Test Generation
================================================================================
✅ Gate passed: P1 = 92.5%, P2 = 96.3%

📈 FLUTTER: Analyzing coverage...
   📁 /monorepo/mobile_app
      Coverage: 73.5%
      Gaps: 8 files with low coverage

📈 PYTHON: Analyzing coverage...
   📁 /monorepo/backend_api
      Coverage: 81.2%
      Gaps: 3 files with low coverage

📊 Phase Result:
   Score: 77.4%
   Time: 42.1 min
```

### Skipped P4 (Low Health)
```
⏭️  Skipping P4 (E2E) - Overall health (76.8%) < 90%
```

## Troubleshooting

### No projects detected
```bash
# Check if project markers exist
ls -la **/pubspec.yaml   # Flutter
ls -la **/package.json   # JavaScript
ls -la **/go.mod         # Go
ls -la **/setup.py       # Python
```

### P1 gate not passing
```
Issue: P1 score (75%) < threshold (90%)
Action: Fix static analysis errors first
Command: Review P1 results and fix errors/complexity
```

### Tests timing out
```
Issue: Tests exceeding time budget
Actions:
1. Check test_timeout in config
2. Use 'minimal' strategy for initial runs
3. Parallelize test execution where possible
```

### Coverage analysis skipped
```
Issue: P3 skipped - gate not met
Reason: P1 = 85% (need 90%) OR P2 = 80% (need 85%)
Action: Fix P1/P2 issues first before coverage improvements
```

## Integration with Existing System

### Use with Current Orchestrator

```python
# In fix_orchestrator.py
from autonomous_fixing.multi_language_orchestrator import MultiLanguageOrchestrator

# Load multi-language config
with open('config/multi_language_fix.yaml') as f:
    ml_config = yaml.safe_load(f)

# Use multi-language orchestrator
ml_orchestrator = MultiLanguageOrchestrator(ml_config)
result = ml_orchestrator.execute(monorepo_path)

# Continue with existing fixing logic based on result
if result['success']:
    # Generate fix tasks from results
    tasks = generate_fix_tasks(result)
```

### Airflow DAG Integration

```python
def run_multi_language_fixing(**context):
    from autonomous_fixing.multi_language_orchestrator import MultiLanguageOrchestrator

    config = load_config('config/multi_language_fix.yaml')
    orchestrator = MultiLanguageOrchestrator(config)

    result = orchestrator.execute(config['target_project'])

    # Push results to XCom
    context['task_instance'].xcom_push(
        key='ml_fixing_result',
        value=result
    )
```

## Performance Benchmarks

### Single Language (Flutter only)
- P1: 30-60 seconds
- P2: 5-30 minutes (adaptive)
- P3: 20-40 minutes (if gate passed)
- P4: 30-60 minutes (if health ≥ 90%)

### Multi-Language (4 languages, parallel)
- P1: 60-90 seconds (all languages in parallel)
- P2: 15-30 minutes (adaptive per language)
- P3: 40-80 minutes (if gate passed)
- P4: 60-120 minutes (if health ≥ 90%)

## Best Practices

1. **Start with Single Language**: Test with one language first, then expand
2. **Use Adaptive Testing**: Let health scores drive test strategy
3. **Respect Priority Gates**: Don't skip to P3/P4 if P1/P2 aren't healthy
4. **Monitor Time Budgets**: Adjust timeouts based on project size
5. **Incremental Improvements**: Focus on P1 → P2 → P3 → P4 progression
6. **Coverage Targets**: Aim for 80% overall, 90%+ for critical paths
7. **E2E Sparingly**: Only run E2E when project is stable (90%+ health)

## See Also

- `MULTI_LANGUAGE_ARCHITECTURE.md` - Architecture and design details
- `config/multi_language_fix.yaml` - Configuration reference
- `language_adapters/` - Language-specific implementation details
