# Interface Mismatch Detection Tests

Quick reference for running tests that detect interface mismatches and ensure component compatibility.

## Test Categories

### 🔬 Unit Tests: Interface Compliance
**What**: Validates that all adapters implement the required interface correctly
**Speed**: Fast (~5 seconds)
**When**: Run on every commit

```bash
# Run all interface compliance tests
pytest tests/unit/test_adapter_interface_compliance.py -v

# Run specific test class
pytest tests/unit/test_adapter_interface_compliance.py::TestAdapterInterfaceCompliance -v

# Check for missing methods
pytest tests/unit/test_adapter_interface_compliance.py::TestAdapterInterfaceCompliance::test_required_methods_exist -v
```

**Key Tests**:
- ✅ All adapters have required methods
- ✅ Method signatures match interface
- ✅ Return types are correct
- ✅ No incorrect usage patterns (e.g., `_get_adapter`)

---

### 🔗 Integration Tests: Component Interaction
**What**: Tests real interactions between adapters and other components
**Speed**: Medium (~15 seconds)
**When**: Run before PR merge

```bash
# Run all integration tests
pytest tests/integration/test_adapter_hook_integration.py -v

# Test adapter-hook manager integration
pytest tests/integration/test_adapter_hook_integration.py::TestAdapterHookIntegration -v

# Test iteration engine adapter access
pytest tests/integration/test_adapter_hook_integration.py::TestIterationEngineAdapterAccess -v
```

**Key Tests**:
- ✅ HookLevelManager can call adapter methods
- ✅ IterationEngine accesses adapters via dict
- ✅ AnalysisResult attributes work correctly
- ✅ Error detection flows work

---

### 🚀 E2E Tests: Full Orchestrator Flow
**What**: Tests complete flow from orchestrator through all components
**Speed**: Slower (~30 seconds)
**When**: Run before release

```bash
# Run all E2E tests
pytest tests/e2e/test_orchestrator_adapter_flow.py -v

# Test full orchestrator flow
pytest tests/e2e/test_orchestrator_adapter_flow.py::TestOrchestratorE2E -v

# Test adapter return values
pytest tests/e2e/test_orchestrator_adapter_flow.py::TestAdapterMethodReturnValues -v
```

**Key Tests**:
- ✅ Complete P1 gate flow works
- ✅ Hook upgrade flow works
- ✅ No AttributeError throughout pipeline
- ✅ All adapters behave consistently

---

## Quick Commands

```bash
# Run ALL interface-related tests
pytest tests/ -k "interface or adapter" -v

# Run with coverage report
pytest tests/unit/test_adapter_interface_compliance.py --cov=airflow_dags/autonomous_fixing/adapters --cov-report=term-missing

# Run only tests that check for AttributeError
pytest tests/ -k "attributeerror or get_adapter" -v

# Run in fail-fast mode (stop at first failure)
pytest tests/unit/test_adapter_interface_compliance.py -x

# Run with detailed output
pytest tests/unit/test_adapter_interface_compliance.py -vv -s
```

---

## CI/CD Integration

Add to your CI pipeline:

```yaml
# .github/workflows/test.yml
- name: Test Interface Compliance
  run: |
    pytest tests/unit/test_adapter_interface_compliance.py -v --junitxml=test-results/interface-unit.xml

- name: Test Component Integration
  run: |
    pytest tests/integration/test_adapter_hook_integration.py -v --junitxml=test-results/interface-integration.xml

- name: Test E2E Flow
  run: |
    pytest tests/e2e/test_orchestrator_adapter_flow.py -v --junitxml=test-results/interface-e2e.xml
```

---

## What Each Test Catches

| Test Type | Catches | Example |
|-----------|---------|---------|
| Unit: Required Methods | Missing adapter methods | `AttributeError: 'JavaScriptAdapter' object has no attribute 'run_type_check'` |
| Unit: Signature Match | Wrong parameters | `TypeError: run_build() takes 1 positional argument but 2 were given` |
| Unit: Source Inspection | Wrong usage patterns | `self.analyzer._get_adapter(lang)` instead of `self.analyzer.adapters.get(lang)` |
| Integration: Real Calls | Interface contract violations | Method exists but returns wrong type |
| Integration: Error Handling | Missing error attributes | `AttributeError: 'AnalysisResult' object has no attribute 'error_message'` |
| E2E: Full Flow | Integration issues | Components work separately but fail together |

---

## Test Fixtures

Common fixtures available:

```python
# Unit tests
@pytest.fixture
def adapters():  # List of adapter classes

# Integration tests
@pytest.fixture
def js_adapter():  # JavaScriptAdapter instance
@pytest.fixture
def py_adapter():  # PythonAdapter instance
@pytest.fixture
def temp_js_project():  # Temporary JS project
@pytest.fixture
def temp_py_project():  # Temporary Python project
@pytest.fixture
def hook_manager():  # HookLevelManager instance

# E2E tests
@pytest.fixture
def temp_workspace():  # Full workspace with multiple projects
@pytest.fixture
def iteration_engine():  # Fully configured IterationEngine
```

---

## Debugging Failed Tests

### If test fails with AttributeError:

1. Check which class is missing the method
2. Look at the interface definition: `domain/interfaces/language_adapter.py`
3. Implement the missing method in the adapter
4. Ensure return type is `AnalysisResult`

### If test fails with signature mismatch:

1. Compare adapter method signature with interface
2. Ensure parameter names and types match
3. Check return type annotation

### If integration test fails:

1. Check component interaction in source code
2. Verify method calls use correct object references
3. Use debugger: `pytest --pdb tests/integration/...`

---

## Examples of Issues These Tests Catch

### ❌ Issue 1: Wrong Adapter Access
```python
# WRONG - Test would fail
adapter = self.analyzer._get_adapter(lang_name)

# CORRECT
adapter = self.analyzer.adapters.get(lang_name)
```

**Caught by**: `test_iteration_engine_uses_analyzer_adapters`

---

### ❌ Issue 2: Missing Method
```python
# Adapter missing run_type_check method
# Test would fail at import time or first call
```

**Caught by**: `test_required_methods_exist`

---

### ❌ Issue 3: Wrong Return Type
```python
def run_build(self, project_path: str) -> dict:  # WRONG
    return {"success": True}
```

**Caught by**: `test_build_returns_analysis_result`

---

### ❌ Issue 4: Missing Attribute
```python
result = AnalysisResult(...)
# If result.error_message is accessed but not set
# Test would fail
```

**Caught by**: `test_adapter_error_message_attribute`

---

## Maintenance

### When Adding New Adapter Methods:

1. Add to `ILanguageAdapter` interface
2. Implement in all adapters
3. Add test to `test_required_methods_exist`
4. Add integration test if needed
5. Run all tests to verify

### When Adding New Language Adapter:

1. Implement `ILanguageAdapter` interface
2. Add to `adapters` fixture in unit tests
3. Run all tests - they'll automatically check new adapter
4. Add language-specific integration tests if needed

---

## Coverage Goals

- **Unit Tests**: 100% of interface methods covered
- **Integration Tests**: All critical component interactions
- **E2E Tests**: Main user flows (P1 → P2 → P3)

Current coverage:
- ✅ All interface methods tested
- ✅ Both JS and Python adapters tested
- ✅ IterationEngine adapter access tested
- ✅ HookLevelManager integration tested
- ✅ Full P1 gate flow tested
