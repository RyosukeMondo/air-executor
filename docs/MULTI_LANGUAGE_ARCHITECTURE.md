# Multi-Language Autonomous Fixing Architecture

Priority-based, time-efficient autonomous fixing for monorepos with multiple languages.

## Priority-Based Execution Strategy

### Priority 1: Fast Static Analysis (ALWAYS RUN)
**Goal**: Fix errors, reduce complexity, improve structure
**Time**: ~30 seconds per language
**Threshold for next phase**: 90%+ accomplished

**Checks**:
- ✅ Static analysis errors
- ✅ File size violations (>500 lines)
- ✅ Cyclomatic complexity (>10)
- ✅ Code smells

**Actions**:
- Fix compilation/analysis errors
- Refactor large files for SRP (Single Responsibility Principle)
- Reduce complexity to make testing easier
- Quick wins for immediate health improvement

### Priority 2: Strategic Unit Tests (TIME-AWARE)
**Goal**: Verify fixes, ensure stability
**Time**: Adaptive based on health (5-30 minutes)
**Threshold for next phase**: Most tests passing (>85%)

**Smart Execution**:
```python
if health_score < 30%:
    run_tests = "minimal"  # Only critical path (5 min)
elif health_score < 60%:
    run_tests = "selective"  # Changed files + smoke tests (15 min)
else:
    run_tests = "comprehensive"  # Full suite (30 min)
```

**Actions**:
- Run tests for changed files first
- Parallel execution where possible
- Fast fail on critical errors
- Fix failing tests

### Priority 3: Coverage Improvements (CONDITIONAL)
**Goal**: Increase test coverage strategically
**Trigger**: P1 accomplished 90%+ AND P2 passing 85%+
**Time**: 20-60 minutes

**Smart Coverage**:
- Analyze coverage gaps
- Prioritize: Critical paths > Common flows > Edge cases
- Generate tests for uncovered code
- Focus on high-value, low-coverage areas

### Priority 4: E2E & Runtime Testing (FINAL PHASE)
**Goal**: Catch runtime errors, add regression tests
**Trigger**: P1-P3 healthy
**Time**: 30-120 minutes

**E2E Strategy**:
1. Start real server/application
2. Run E2E test suite
3. Capture runtime errors
4. Fix runtime issues
5. Add regression tests to prevent recurrence
6. Repeat until stable

## Language Support

### Supported Languages

| Language | Static Analysis | Unit Tests | Coverage | E2E |
|----------|----------------|------------|----------|-----|
| **Flutter** | `flutter analyze` | `flutter test` | `flutter test --coverage` | Integration tests |
| **Python** | `pylint`, `mypy` | `pytest` | `pytest --cov` | `playwright`, API tests |
| **JavaScript/TypeScript** | `eslint`, `tsc` | `jest`, `vitest` | `jest --coverage` | `playwright`, Cypress |
| **Go** | `go vet`, `staticcheck` | `go test` | `go test -cover` | API tests |

### Language Detection

**Automatic detection via project files**:
```python
language_markers = {
    'flutter': ['pubspec.yaml', 'lib/**/*.dart'],
    'python': ['requirements.txt', 'pyproject.toml', 'setup.py'],
    'javascript': ['package.json', 'tsconfig.json'],
    'go': ['go.mod', 'go.sum']
}
```

**Monorepo structure**:
```
/monorepo
  /flutter_app/         # Flutter project
  /python_backend/      # Python project
  /web_frontend/        # TypeScript project
  /api_service/         # Go project
```

## Time-Efficiency Strategy

### Execution Timeline

```
Phase 1 (0-2 min):    P1 Static Analysis (all languages in parallel)
                      ├─ Flutter: analyze + complexity
                      ├─ Python: pylint + mypy
                      ├─ JS/TS: eslint + tsc
                      └─ Go: go vet + staticcheck

Phase 2 (2-8 min):    P1 Fixes (parallel batches)
                      └─ Fix errors, refactor complexity

Phase 3 (8-10 min):   Health check → Decide P2 strategy

Phase 4 (10-40 min):  P2 Strategic Tests (time-aware)
                      ├─ If health < 30%: minimal tests only
                      ├─ If health 30-60%: selective tests
                      └─ If health > 60%: comprehensive tests

Phase 5 (40-60 min):  P2 Test Fixes
                      └─ Fix failing tests

Gate Check:           P1 ≥ 90% AND P2 ≥ 85%? → Continue, else repeat

Phase 6 (60-90 min):  P3 Coverage Analysis & Test Generation
                      └─ Only if gate passed

Phase 7 (90-180 min): P4 E2E Testing & Runtime Fixes
                      └─ Only if P1-P3 healthy
```

### Adaptive Time Allocation

```python
def calculate_test_budget(health_score: float, priority: int) -> int:
    """Calculate time budget for testing based on health"""

    if priority == 1:  # Static analysis
        return 120  # Always 2 minutes (fast)

    elif priority == 2:  # Unit tests
        if health_score < 0.3:
            return 300   # 5 min - minimal tests
        elif health_score < 0.6:
            return 900   # 15 min - selective tests
        else:
            return 1800  # 30 min - comprehensive tests

    elif priority == 3:  # Coverage
        if health_score < 0.85:
            return 0  # Skip coverage if not healthy enough
        return 3600  # 60 min - coverage improvements

    elif priority == 4:  # E2E
        if health_score < 0.9:
            return 0  # Skip E2E if not healthy enough
        return 7200  # 120 min - E2E testing
```

## Language Adapter Interface

### Base Adapter Class

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class AnalysisResult:
    language: str
    phase: str  # 'static', 'tests', 'coverage', 'e2e'
    errors: List[Dict]
    complexity_violations: List[Dict]
    file_size_violations: List[Dict]
    test_failures: List[Dict]
    coverage_gaps: List[Dict]
    runtime_errors: List[Dict]
    execution_time: float

class LanguageAdapter(ABC):
    """Base class for language-specific analysis and fixing"""

    @abstractmethod
    def detect_projects(self, root_path: str) -> List[str]:
        """Find all projects of this language in monorepo"""
        pass

    @abstractmethod
    def static_analysis(self, project_path: str) -> AnalysisResult:
        """Priority 1: Fast static analysis"""
        pass

    @abstractmethod
    def run_tests(self, project_path: str, strategy: str) -> AnalysisResult:
        """Priority 2: Run tests with strategy (minimal/selective/comprehensive)"""
        pass

    @abstractmethod
    def analyze_coverage(self, project_path: str) -> AnalysisResult:
        """Priority 3: Analyze test coverage gaps"""
        pass

    @abstractmethod
    def run_e2e_tests(self, project_path: str) -> AnalysisResult:
        """Priority 4: Run E2E tests and capture runtime errors"""
        pass

    @abstractmethod
    def parse_errors(self, output: str) -> List[Dict]:
        """Parse language-specific error format"""
        pass

    @abstractmethod
    def calculate_complexity(self, file_path: str) -> int:
        """Calculate cyclomatic complexity"""
        pass
```

### Flutter Adapter

```python
class FlutterAdapter(LanguageAdapter):
    def detect_projects(self, root_path: str) -> List[str]:
        # Find all pubspec.yaml files
        return glob.glob(f"{root_path}/**/pubspec.yaml")

    def static_analysis(self, project_path: str) -> AnalysisResult:
        # Run flutter analyze
        # Check file sizes
        # Calculate complexity with dart_code_metrics
        pass

    def run_tests(self, project_path: str, strategy: str) -> AnalysisResult:
        if strategy == "minimal":
            # Run only unit tests, no widget/integration
            cmd = "flutter test test/unit/"
        elif strategy == "selective":
            # Run unit + widget tests
            cmd = "flutter test --exclude-tags=integration"
        else:
            # Full test suite
            cmd = "flutter test"
        pass

    def analyze_coverage(self, project_path: str) -> AnalysisResult:
        # flutter test --coverage
        # Parse coverage/lcov.info
        # Identify uncovered functions
        pass

    def run_e2e_tests(self, project_path: str) -> AnalysisResult:
        # flutter test integration_test/
        # OR flutter drive --target=test_driver/app.dart
        pass
```

### Python Adapter

```python
class PythonAdapter(LanguageAdapter):
    def detect_projects(self, root_path: str) -> List[str]:
        # Find setup.py, pyproject.toml, requirements.txt
        pass

    def static_analysis(self, project_path: str) -> AnalysisResult:
        # Run pylint + mypy in parallel
        # Check file sizes
        # Calculate complexity with radon
        pass

    def run_tests(self, project_path: str, strategy: str) -> AnalysisResult:
        if strategy == "minimal":
            cmd = "pytest -m 'not slow' --tb=short"
        elif strategy == "selective":
            cmd = "pytest -m 'not slow and not integration'"
        else:
            cmd = "pytest"
        pass

    def analyze_coverage(self, project_path: str) -> AnalysisResult:
        # pytest --cov --cov-report=json
        # Parse coverage.json
        # Find uncovered functions
        pass

    def run_e2e_tests(self, project_path: str) -> AnalysisResult:
        # pytest -m e2e
        # OR start server + run playwright tests
        pass
```

### JavaScript/TypeScript Adapter

```python
class JavaScriptAdapter(LanguageAdapter):
    def detect_projects(self, root_path: str) -> List[str]:
        # Find package.json files
        pass

    def static_analysis(self, project_path: str) -> AnalysisResult:
        # Run eslint + tsc in parallel
        # Check file sizes
        # Calculate complexity with complexity-report
        pass

    def run_tests(self, project_path: str, strategy: str) -> AnalysisResult:
        if strategy == "minimal":
            cmd = "npm test -- --testPathPattern='unit' --bail"
        elif strategy == "selective":
            cmd = "npm test -- --testPathPattern='(unit|integration)'"
        else:
            cmd = "npm test"
        pass
```

### Go Adapter

```python
class GoAdapter(LanguageAdapter):
    def detect_projects(self, root_path: str) -> List[str]:
        # Find go.mod files
        pass

    def static_analysis(self, project_path: str) -> AnalysisResult:
        # Run go vet + staticcheck in parallel
        # Check file sizes
        # Calculate complexity with gocyclo
        pass

    def run_tests(self, project_path: str, strategy: str) -> AnalysisResult:
        if strategy == "minimal":
            cmd = "go test -short ./..."
        elif strategy == "selective":
            cmd = "go test -short -tags=!integration ./..."
        else:
            cmd = "go test ./..."
        pass
```

## Configuration

### New Config Structure

```yaml
# Multi-language configuration
languages:
  enabled:
    - flutter
    - python
    - javascript
    - go

  auto_detect: true  # Auto-detect languages in monorepo

  # Language-specific settings
  flutter:
    analyzer_args: "--fatal-infos --fatal-warnings"
    test_timeout: 600
    complexity_threshold: 10
    max_file_lines: 500

  python:
    linters: ["pylint", "mypy"]
    test_framework: "pytest"
    complexity_threshold: 10
    max_file_lines: 500

  javascript:
    linters: ["eslint"]
    type_checker: "tsc"
    test_framework: "jest"  # or "vitest"
    complexity_threshold: 10
    max_file_lines: 500

  go:
    linters: ["go vet", "staticcheck"]
    test_timeout: 300
    complexity_threshold: 10
    max_file_lines: 500

# Priority-based execution
priorities:
  p1_static:
    enabled: true
    max_duration_seconds: 120
    success_threshold: 0.90  # 90% to proceed to P3

  p2_tests:
    enabled: true
    adaptive_strategy: true
    time_budgets:
      minimal: 300      # 5 min when health < 30%
      selective: 900    # 15 min when health 30-60%
      comprehensive: 1800  # 30 min when health > 60%
    success_threshold: 0.85  # 85% passing to proceed

  p3_coverage:
    enabled: true
    gate_requirements:
      p1_score: 0.90  # P1 must be 90%+
      p2_score: 0.85  # P2 must be 85%+
    max_duration_seconds: 3600
    target_coverage: 0.80  # Aim for 80% coverage

  p4_e2e:
    enabled: true
    gate_requirements:
      overall_health: 0.90  # Overall health must be 90%+
    max_duration_seconds: 7200
    retry_on_flaky: true

# Execution strategy
execution:
  parallel_languages: true  # Run all language checks in parallel
  max_concurrent_projects: 4
  fail_fast: false  # Continue even if one language fails
  priority_gates: true  # Enforce priority gates
```

## Execution Flow

```python
class MultiLanguageOrchestrator:
    def __init__(self, config):
        self.adapters = {
            'flutter': FlutterAdapter(config.languages.flutter),
            'python': PythonAdapter(config.languages.python),
            'javascript': JavaScriptAdapter(config.languages.javascript),
            'go': GoAdapter(config.languages.go),
        }

    def execute(self, monorepo_path: str):
        # 1. Detect all projects by language
        projects_by_language = self.detect_all_projects(monorepo_path)

        # 2. PRIORITY 1: Static Analysis (parallel)
        p1_results = self.run_priority_1(projects_by_language)
        p1_score = self.calculate_score(p1_results)

        if p1_score < 0.90:
            # Fix P1 issues before proceeding
            self.fix_priority_1_issues(p1_results)
            return  # Re-check next iteration

        # 3. PRIORITY 2: Tests (adaptive, parallel)
        health = self.calculate_health(p1_results)
        test_strategy = self.determine_test_strategy(health)
        p2_results = self.run_priority_2(projects_by_language, test_strategy)
        p2_score = self.calculate_score(p2_results)

        if p2_score < 0.85:
            # Fix P2 issues
            self.fix_priority_2_issues(p2_results)
            return

        # 4. PRIORITY 3: Coverage (conditional)
        if self.should_run_coverage(p1_score, p2_score):
            p3_results = self.run_priority_3(projects_by_language)
            self.generate_missing_tests(p3_results)

        # 5. PRIORITY 4: E2E (final phase)
        overall_health = self.calculate_overall_health()
        if overall_health >= 0.90:
            p4_results = self.run_priority_4(projects_by_language)
            self.fix_runtime_issues(p4_results)
```

## Benefits

1. **Time Efficient**: Fast static checks always run, expensive tests only when health is good
2. **Multi-Language**: Single system handles entire monorepo
3. **Prioritized**: Focus on quick wins first, expensive operations last
4. **Adaptive**: Test strategy adjusts to current health
5. **Gated**: Don't waste time on coverage if basics aren't fixed
6. **Comprehensive**: From static analysis → tests → coverage → E2E
