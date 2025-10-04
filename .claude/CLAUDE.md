# Air-Executor Project Configuration

## Python Environment

**IMPORTANT**: This project uses a virtual environment.

Always use: `.venv/bin/python3` for all Python commands.

### Examples:
```bash
# Running tests
.venv/bin/python3 -m pytest tests/unit/test_adapter_interface_compliance.py -v

# Running scripts
.venv/bin/python3 run_orchestrator.py

# Installing packages
.venv/bin/pip install package-name

# Python REPL
.venv/bin/python3
```

**DO NOT USE**:
- `python` (not in PATH)
- `python3` (system Python, wrong environment)
- `venv/bin/python3` (wrong path - missing the dot)

---

## Project Structure

```
air-executor/
├── .venv/                      # Virtual environment (USE THIS)
├── airflow_dags/
│   └── autonomous_fixing/      # Main codebase
│       ├── core/               # Core orchestration
│       ├── adapters/           # Language adapters
│       └── domain/             # Domain models & interfaces
├── tests/
│   ├── unit/                   # Fast unit tests
│   ├── integration/            # Component interaction tests
│   └── e2e/                    # End-to-end tests
├── claudedocs/                 # AI-generated documentation
└── .claude/                    # Project-specific Claude config
```

---

## Key Architectural Patterns

### 1. Adapter Pattern
- All language adapters implement `ILanguageAdapter` interface
- Adapters accessed via `self.analyzer.adapters` dict, NOT `_get_adapter()` method
- Every adapter MUST implement: `run_type_check()`, `run_build()`, etc.

### 2. Component Responsibilities (SRP)
- **IterationEngine**: Manages improvement loop iterations
- **ProjectAnalyzer**: Runs analysis across projects
- **IssueFixer**: Fixes issues using Claude
- **HealthScorer**: Calculates health scores
- **HookLevelManager**: Progressive hook enforcement

### 3. Data Models
- `AnalysisResult`: Unified result model for all analysis phases
- Must have: `.success`, `.errors`, `.error_message` (for builds)

---

## Common Commands

### Running Tests
```bash
# All interface compliance tests
.venv/bin/python3 -m pytest tests/unit/test_adapter_interface_compliance.py -v

# Integration tests
.venv/bin/python3 -m pytest tests/integration/ -v

# E2E tests
.venv/bin/python3 -m pytest tests/e2e/ -v

# Run specific test
.venv/bin/python3 -m pytest tests/unit/test_adapter_interface_compliance.py::TestAdapterInterfaceCompliance::test_required_methods_exist -v

# Run with coverage
.venv/bin/python3 -m pytest tests/ --cov=airflow_dags/autonomous_fixing --cov-report=term-missing
```

### Running Orchestrator
```bash
# Run autonomous fixing
.venv/bin/python3 run_orchestrator.py

# With specific config
.venv/bin/python3 run_orchestrator.py --config config/warps.yaml
```

### Linting & Type Checking
```bash
# Ruff linting
.venv/bin/python3 -m ruff check airflow_dags/

# Type checking
.venv/bin/python3 -m mypy airflow_dags/autonomous_fixing/
```

---

## Interface Compliance Rules

When adding new adapter methods:

1. ✅ **Add to interface first**: `domain/interfaces/language_adapter.py`
2. ✅ **Implement in all adapters**: JavaScript, Python (and future ones)
3. ✅ **Add unit test**: `tests/unit/test_adapter_interface_compliance.py`
4. ✅ **Run tests**: Ensure all adapters comply

**Common Mistakes to Avoid**:
- ❌ Calling `self.analyzer._get_adapter(lang)`
- ✅ Use `self.analyzer.adapters.get(lang)`

- ❌ Implementing method without adding to interface
- ✅ Add to `ILanguageAdapter` first

- ❌ Returning dict instead of AnalysisResult
- ✅ Always return `AnalysisResult` from adapter methods

---

## Test Organization Philosophy

- **Unit tests** (fast, ~0.1s): Interface compliance, method existence, signatures
- **Integration tests** (medium, ~1s): Component interactions, real method calls
- **E2E tests** (slow, ~30s): Full orchestrator flow, realistic scenarios

Run unit tests first, then integration, then E2E.

---

## Important Files

### Interfaces (Source of Truth)
- `airflow_dags/autonomous_fixing/domain/interfaces/language_adapter.py`
- `airflow_dags/autonomous_fixing/domain/models/analysis.py`

### Core Components
- `airflow_dags/autonomous_fixing/core/iteration_engine.py`
- `airflow_dags/autonomous_fixing/core/analyzer.py`
- `airflow_dags/autonomous_fixing/core/fixer.py`
- `airflow_dags/autonomous_fixing/core/scorer.py`
- `airflow_dags/autonomous_fixing/core/hook_level_manager.py`

### Adapters
- `airflow_dags/autonomous_fixing/adapters/languages/javascript_adapter.py`
- `airflow_dags/autonomous_fixing/adapters/languages/python_adapter.py`

### Test Coverage
- `tests/unit/test_adapter_interface_compliance.py` - Interface validation
- `tests/integration/test_adapter_hook_integration.py` - Component integration
- `tests/e2e/test_orchestrator_adapter_flow.py` - Full flow testing

---

## Documentation

- `claudedocs/interface-mismatch-fixes-and-tests.md` - Recent fixes and test coverage
- `tests/README_INTERFACE_TESTS.md` - Test running guide
- `.claude/PROJECT_MEMORY.md` - Project context and history

---

## Code Quality Standards

- **Line length**: 100 characters (black)
- **Complexity threshold**: 10 (configurable)
- **Max file lines**: 500
- **Test coverage**: >80% target

---

## Progressive Hook Enforcement

Hooks upgrade based on quality gates:
- **Level 0**: Basic pre-commit setup
- **Level 1**: Type checking + build (after P1 passes)
- **Level 2**: + Unit tests (after P2 passes)
- **Level 3**: + Coverage + linting (after P3 passes)
