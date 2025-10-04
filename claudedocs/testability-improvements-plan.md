# Testability Improvements Implementation Plan

**Goal**: Make air-executor E2E testable through dependency injection, configuration objects, and in-process testing.

**Status**: 🟡 In Progress
**Started**: 2025-10-04
**Target Completion**: TBD

---

## Progress Overview

- [ ] **Phase 1**: Configuration Objects (4/5 complete)
- [ ] **Phase 2**: Dependency Injection (0/6 complete)
- [ ] **Phase 3**: Interface Extraction (0/4 complete)
- [ ] **Phase 4**: In-Process CLI (0/3 complete)
- [ ] **Phase 5**: Test Builders (0/4 complete)
- [ ] **Phase 6**: E2E Test Refactoring (0/5 complete)

**Overall Progress**: 4/27 tasks complete (15%)

---

## Phase 1: Configuration Objects
**Priority**: 🔴 High | **Risk**: Low | **Impact**: High

### Goals
- Make all filesystem paths configurable
- Enable test isolation through tmp_path
- Remove hardcoded constants
- Backward compatible (defaults work as before)

### Tasks

#### 1.1 Create PreflightConfig ✅
- [x] Create `airflow_dags/autonomous_fixing/config/preflight_config.py`
- [x] Define dataclass with all configurable parameters
- [x] Add to PreflightValidator constructor with default parameter
- [x] Update all tests to use custom configs with tmp_path

**Acceptance Criteria**:
```python
@dataclass
class PreflightConfig:
    """Configuration for PreflightValidator."""
    cache_max_age_days: int = 30  # Changed from 7 to match new implementation
    state_dir_name: str = ".ai-state"

    # Future: Add more as needed
    # hook_cache_dir: Optional[Path] = None
    # test_cache_dir: Optional[Path] = None

# Usage in tests:
config = PreflightConfig(cache_max_age_days=1)  # Fast staleness for tests
validator = PreflightValidator(tracker, config=config)
```

**Files to modify**:
- `airflow_dags/autonomous_fixing/core/validators/preflight.py`
- `tests/unit/test_preflight_validator.py`
- `tests/integration/test_setup_optimization_flow.py`

---

#### 1.2 Create StateManagerConfig ✅
- [x] Create `airflow_dags/autonomous_fixing/config/state_config.py`
- [x] Make state_dir, cache_dirs configurable
- [x] Add to ProjectStateManager constructor
- [x] Update tests to use isolated state directories

**Acceptance Criteria**:
```python
@dataclass
class StateConfig:
    """Configuration for ProjectStateManager."""
    state_dir_name: str = ".ai-state"
    max_age_days: int = 30
    external_hook_cache_dir: Path = Path("config/precommit-cache")
    external_test_cache_dir: Path = Path("config/test-cache")

    def with_base_dir(self, base: Path) -> 'StateConfig':
        """Create config with custom base directory for caches."""
        return StateConfig(
            state_dir_name=self.state_dir_name,
            max_age_days=self.max_age_days,
            external_hook_cache_dir=base / "hook-cache",
            external_test_cache_dir=base / "test-cache"
        )

# Usage:
config = StateConfig().with_base_dir(tmp_path)
manager = ProjectStateManager(project_path, config=config)
```

**Files to modify**:
- `airflow_dags/autonomous_fixing/core/state_manager.py`
- All integration tests using ProjectStateManager

---

#### 1.3 Create OrchestratorConfig ✅
- [x] Create `airflow_dags/autonomous_fixing/config/orchestrator_config.py`
- [x] Consolidate all configuration parameters
- [x] Support loading from YAML (existing behavior)
- [x] Support programmatic configuration (new for tests)

**Acceptance Criteria**:
```python
@dataclass
class OrchestratorConfig:
    """Central configuration for entire orchestrator."""
    # Project settings
    projects: List[str] = field(default_factory=list)
    languages: List[str] = field(default_factory=lambda: ["python", "javascript"])

    # State management
    state_config: StateConfig = field(default_factory=StateConfig)

    # Validation settings
    preflight_config: PreflightConfig = field(default_factory=PreflightConfig)

    # Redis settings
    redis_host: Optional[str] = None
    redis_port: Optional[int] = None

    # AI settings
    anthropic_api_key: Optional[str] = None
    model: str = "claude-3-5-sonnet-20241022"

    @classmethod
    def from_yaml(cls, path: Path) -> 'OrchestratorConfig':
        """Load from existing YAML format."""
        ...

    @classmethod
    def for_testing(cls, tmp_path: Path, **overrides) -> 'OrchestratorConfig':
        """Create isolated test configuration."""
        return cls(
            state_config=StateConfig().with_base_dir(tmp_path),
            preflight_config=PreflightConfig(cache_max_age_days=1),
            redis_host=None,  # No Redis in tests
            **overrides
        )
```

**Files modified**:
- `airflow_dags/autonomous_fixing/config/orchestrator_config.py` (created)
- `airflow_dags/autonomous_fixing/config/__init__.py` (updated exports)
- `airflow_dags/autonomous_fixing/multi_language_orchestrator.py` (updated to accept OrchestratorConfig)
- `run_orchestrator.py` (updated to use OrchestratorConfig.from_yaml())

**Tests added**:
- `tests/unit/test_orchestrator_config.py` (7 tests)
- `tests/integration/test_orchestrator_config_compatibility.py` (4 tests)

**Implementation notes**:
- Backward compatible: accepts both `OrchestratorConfig` and `Dict`
- `from_yaml()` method for existing YAML configs
- `from_dict()` method for backward compatibility
- `for_testing()` method creates isolated test configs
- `to_dict()` method for component compatibility
- All tests pass (11/11) ✅

---

#### 1.4 Create SetupTrackerConfig
- [ ] Create config for SetupTracker state directory
- [ ] Make STATE_DIR configurable (currently class variable)
- [ ] Support test isolation

**Acceptance Criteria**:
```python
@dataclass
class SetupTrackerConfig:
    """Configuration for SetupTracker."""
    state_dir: Path = Path(".ai-setup-state")
    redis_config: Optional[Dict[str, Any]] = None

# Usage:
config = SetupTrackerConfig(state_dir=tmp_path / "setup-state")
tracker = SetupTracker(config=config)
```

**Files to modify**:
- `airflow_dags/autonomous_fixing/core/setup_tracker.py`

---

#### 1.5 Integration and Testing
- [ ] Update all existing tests to use new configs
- [ ] Ensure backward compatibility (default configs work as before)
- [ ] Add config validation tests
- [ ] Document configuration in README

**Acceptance Criteria**:
- All existing tests pass without changes
- New tests can use `OrchestratorConfig.for_testing(tmp_path)`
- No hardcoded paths remain in core code

---

## Phase 2: Dependency Injection
**Priority**: 🔴 High | **Risk**: Medium | **Impact**: High

### Goals
- Enable mocking of dependencies
- Remove internal object creation
- Factory pattern for flexibility
- Maintain backward compatibility

### Tasks

#### 2.1 Inject State Manager Factory into PreflightValidator
- [ ] Add `state_manager_factory` parameter to `__init__`
- [ ] Default to `ProjectStateManager` for backward compatibility
- [ ] Update all tests to inject mock factories

**Acceptance Criteria**:
```python
class PreflightValidator:
    def __init__(
        self,
        setup_tracker: SetupTracker,
        config: PreflightConfig = None,
        state_manager_factory: Callable[[Path], IStateRepository] = None
    ):
        self.setup_tracker = setup_tracker
        self.config = config or PreflightConfig()
        # Default to real implementation
        self.state_manager_factory = state_manager_factory or ProjectStateManager

    def can_skip_hook_config(self, project_path: Path) -> Tuple[bool, str]:
        # Use injected factory instead of creating directly
        state_manager = self.state_manager_factory(project_path)
        should_reconfig, reason = state_manager.should_reconfigure('hooks')
        ...

# Test usage:
mock_state_manager = Mock(spec=IStateRepository)
mock_state_manager.should_reconfigure.return_value = (False, "cached")
validator = PreflightValidator(
    tracker,
    state_manager_factory=lambda path: mock_state_manager
)
```

**Files to modify**:
- `airflow_dags/autonomous_fixing/core/validators/preflight.py`
- `tests/unit/test_preflight_validator.py` (replace @patch with injection)

---

#### 2.2 Inject Dependencies into IterationEngine
- [ ] Add analyzer, fixer, scorer as constructor parameters
- [ ] Default to creating them internally (backward compat)
- [ ] Support full dependency injection

**Acceptance Criteria**:
```python
class IterationEngine:
    def __init__(
        self,
        config: OrchestratorConfig,
        analyzer: Optional[ProjectAnalyzer] = None,
        fixer: Optional[IssueFixer] = None,
        scorer: Optional[HealthScorer] = None,
        hook_manager: Optional[HookLevelManager] = None
    ):
        self.config = config
        # Use injected or create defaults
        self.analyzer = analyzer or ProjectAnalyzer(config)
        self.fixer = fixer or IssueFixer(config)
        self.scorer = scorer or HealthScorer(config)
        self.hook_manager = hook_manager or HookLevelManager(config)
```

**Files to modify**:
- `airflow_dags/autonomous_fixing/core/iteration_engine.py`

---

#### 2.3 Inject AI Client into IssueFixer
- [ ] Add `ai_client` parameter
- [ ] Support mock AI clients for testing
- [ ] Default to Anthropic client

**Acceptance Criteria**:
```python
class IssueFixer:
    def __init__(
        self,
        config: OrchestratorConfig,
        ai_client: Optional[Any] = None  # Will be ILanguageModel once extracted
    ):
        self.config = config
        self.ai_client = ai_client or self._create_anthropic_client()

    def _create_anthropic_client(self):
        """Create default Anthropic client."""
        from anthropic import Anthropic
        return Anthropic(api_key=self.config.anthropic_api_key)

# Test usage:
mock_ai = Mock()
mock_ai.messages.create.return_value = Mock(content=[Mock(text="fixed code")])
fixer = IssueFixer(config, ai_client=mock_ai)
```

**Files to modify**:
- `airflow_dags/autonomous_fixing/core/fixer.py`
- E2E tests that need to mock AI

---

#### 2.4 Inject Redis Client into SetupTracker
- [ ] Already partially done, improve interface
- [ ] Ensure factory pattern for Redis creation
- [ ] Support mock Redis for tests

**Acceptance Criteria**:
```python
class SetupTracker:
    def __init__(
        self,
        config: SetupTrackerConfig,
        redis_factory: Optional[Callable[[], Redis]] = None
    ):
        self.config = config
        if redis_factory:
            self.redis_client = redis_factory()
        elif config.redis_config:
            self.redis_client = self._create_redis_client(config.redis_config)
        else:
            self.redis_client = None  # Filesystem fallback
```

**Files to modify**:
- `airflow_dags/autonomous_fixing/core/setup_tracker.py`

---

#### 2.5 Inject Adapters into ProjectAnalyzer
- [ ] Make language adapters injectable
- [ ] Support custom adapter factories for tests

**Acceptance Criteria**:
```python
class ProjectAnalyzer:
    def __init__(
        self,
        config: OrchestratorConfig,
        adapter_factory: Optional[Callable[[str], ILanguageAdapter]] = None
    ):
        self.config = config
        self.adapter_factory = adapter_factory or self._default_adapter_factory
        self.adapters = self._create_adapters()
```

**Files to modify**:
- `airflow_dags/autonomous_fixing/core/analyzer.py`

---

#### 2.6 Test All Dependency Injection
- [ ] Write tests for each injected dependency
- [ ] Verify backward compatibility (defaults work)
- [ ] Ensure mocking works cleanly

---

## Phase 3: Interface Extraction
**Priority**: 🟡 Medium | **Risk**: Medium | **Impact**: High

### Goals
- Define clear contracts
- Enable in-memory test implementations
- Support alternative implementations

### Tasks

#### 3.1 Extract IStateRepository Interface
- [ ] Create `domain/interfaces/state_repository.py`
- [ ] Define interface for state management
- [ ] Implement in ProjectStateManager (FilesystemStateRepository)
- [ ] Create MemoryStateRepository for tests

**Acceptance Criteria**:
```python
# domain/interfaces/state_repository.py
class IStateRepository(ABC):
    """Interface for project state management."""

    @abstractmethod
    def should_reconfigure(self, phase: str) -> Tuple[bool, str]:
        """Check if reconfiguration needed for phase."""
        pass

    @abstractmethod
    def save_state(self, phase: str, metadata: Dict[str, Any]) -> None:
        """Save state for phase."""
        pass

    @abstractmethod
    def get_state(self, phase: str) -> Optional[Dict[str, Any]]:
        """Get state for phase."""
        pass

# adapters/state/memory_state_repository.py
class MemoryStateRepository(IStateRepository):
    """In-memory state for fast tests."""

    def __init__(self):
        self.states: Dict[str, Dict[str, Any]] = {}

    def should_reconfigure(self, phase: str) -> Tuple[bool, str]:
        if phase not in self.states:
            return (True, f"no {phase} state in memory")
        return (False, f"{phase} cached in memory")

    def save_state(self, phase: str, metadata: Dict[str, Any]) -> None:
        self.states[phase] = metadata

    def get_state(self, phase: str) -> Optional[Dict[str, Any]]:
        return self.states.get(phase)

# Rename existing implementation
class FilesystemStateRepository(IStateRepository):
    """Filesystem-based state (formerly ProjectStateManager)."""
    # Existing ProjectStateManager code
```

**Files to create**:
- `airflow_dags/autonomous_fixing/domain/interfaces/state_repository.py`
- `airflow_dags/autonomous_fixing/adapters/state/memory_state_repository.py`
- `airflow_dags/autonomous_fixing/adapters/state/filesystem_state_repository.py`

**Files to modify**:
- `airflow_dags/autonomous_fixing/core/state_manager.py` (keep as alias for backward compat)

---

#### 3.2 Extract ISetupTracker Interface
- [ ] Create interface for setup tracking
- [ ] Implement for Redis and filesystem
- [ ] Create in-memory implementation for tests

**Acceptance Criteria**:
```python
class ISetupTracker(ABC):
    """Interface for tracking setup completion."""

    @abstractmethod
    def mark_setup_complete(self, project_path: str, phase: str) -> None:
        pass

    @abstractmethod
    def is_setup_complete(self, project_path: str, phase: str) -> bool:
        pass

    @abstractmethod
    def clear_setup_state(self, project_path: str, phase: str) -> None:
        pass

class MemorySetupTracker(ISetupTracker):
    """In-memory tracker for tests."""

    def __init__(self):
        self.completions: Set[Tuple[str, str]] = set()

    def mark_setup_complete(self, project_path: str, phase: str) -> None:
        self.completions.add((project_path, phase))

    def is_setup_complete(self, project_path: str, phase: str) -> bool:
        return (project_path, phase) in self.completions
```

**Files to create**:
- `airflow_dags/autonomous_fixing/domain/interfaces/setup_tracker.py`
- `airflow_dags/autonomous_fixing/adapters/tracking/memory_setup_tracker.py`

---

#### 3.3 Extract IAIClient Interface
- [ ] Create interface for AI interactions
- [ ] Implement for Anthropic
- [ ] Create mock AI client for tests

**Acceptance Criteria**:
```python
class IAIClient(ABC):
    """Interface for AI language model interactions."""

    @abstractmethod
    def generate_fix(
        self,
        issue: Dict[str, Any],
        context: str,
        system_prompt: str
    ) -> str:
        """Generate code fix for issue."""
        pass

class MockAIClient(IAIClient):
    """Deterministic AI client for tests."""

    def __init__(self, responses: Dict[str, str] = None):
        self.responses = responses or {}
        self.calls = []

    def generate_fix(self, issue, context, system_prompt):
        self.calls.append((issue, context, system_prompt))
        issue_key = issue.get('message', 'default')
        return self.responses.get(issue_key, "# Fixed code")

# Test usage:
mock_ai = MockAIClient(responses={
    "syntax error": "fixed_syntax = True",
    "type error": "x: int = 5"
})
fixer = IssueFixer(config, ai_client=mock_ai)
```

**Files to create**:
- `airflow_dags/autonomous_fixing/domain/interfaces/ai_client.py`
- `airflow_dags/autonomous_fixing/adapters/ai/anthropic_client.py`
- `airflow_dags/autonomous_fixing/adapters/ai/mock_ai_client.py`

---

#### 3.4 Update All Components to Use Interfaces
- [ ] Change type hints to use interfaces
- [ ] Update dependency injection to accept interfaces
- [ ] Ensure tests use in-memory implementations

---

## Phase 4: In-Process CLI
**Priority**: 🟡 Medium | **Risk**: Low | **Impact**: High

### Goals
- Enable running orchestrator without subprocess
- Fast E2E tests
- Better debugging (in-process, step through)

### Tasks

#### 4.1 Create OrchestratorCLI Wrapper
- [ ] Create programmatic entry point
- [ ] Support config from dict/object (not just YAML)
- [ ] Return structured results (not exit codes)

**Acceptance Criteria**:
```python
# airflow_dags/autonomous_fixing/cli/orchestrator_cli.py
class OrchestratorCLI:
    """Programmatic interface to orchestrator."""

    @staticmethod
    def run(
        config: Union[Path, OrchestratorConfig],
        **overrides
    ) -> OrchestratorResult:
        """
        Run orchestrator in-process.

        Args:
            config: Either path to YAML or OrchestratorConfig object
            **overrides: Override config parameters

        Returns:
            OrchestratorResult with success, errors, metrics
        """
        if isinstance(config, Path):
            config = OrchestratorConfig.from_yaml(config)

        # Apply overrides
        for key, value in overrides.items():
            setattr(config, key, value)

        orchestrator = MultiLanguageOrchestrator(config)
        return orchestrator.execute()

    @staticmethod
    def run_from_yaml(config_path: Path, **overrides) -> OrchestratorResult:
        """Convenience method for YAML configs."""
        return OrchestratorCLI.run(config_path, **overrides)

@dataclass
class OrchestratorResult:
    """Structured result from orchestrator execution."""
    success: bool
    exit_code: int
    iterations_completed: int
    final_health_score: float
    errors: List[str]
    warnings: List[str]
    metrics: Dict[str, Any]
    duration_seconds: float
```

**Files to create**:
- `airflow_dags/autonomous_fixing/cli/orchestrator_cli.py`
- `airflow_dags/autonomous_fixing/domain/models/orchestrator_result.py`

---

#### 4.2 Update run_orchestrator.py to Use CLI
- [ ] Keep as thin wrapper around OrchestratorCLI
- [ ] Preserve existing command-line behavior
- [ ] Add `--in-process` flag for debugging

**Acceptance Criteria**:
```python
# run_orchestrator.py
def main():
    args = parse_args()
    config_path = Path(args.config)

    result = OrchestratorCLI.run_from_yaml(
        config_path,
        redis_host=args.redis_host,  # Optional overrides from CLI
        verbose=args.verbose
    )

    # Print results
    print(f"Success: {result.success}")
    print(f"Final health score: {result.final_health_score}")

    if result.errors:
        print("\nErrors:")
        for error in result.errors:
            print(f"  - {error}")

    sys.exit(result.exit_code)
```

**Files to modify**:
- `run_orchestrator.py`

---

#### 4.3 Update E2E Tests to Use In-Process CLI
- [ ] Replace subprocess.run with OrchestratorCLI.run
- [ ] Use OrchestratorConfig.for_testing
- [ ] Much faster, debuggable tests

**Acceptance Criteria**:
```python
# tests/e2e/test_autonomous_fixing_cache.py
def test_autonomous_fix_cache_hit(tmp_path):
    """Test cache hit scenario - in-process."""
    config = OrchestratorConfig.for_testing(
        tmp_path,
        projects=[str(tmp_path / "test-project")],
        languages=["python"]
    )

    # First run - cache miss
    result1 = OrchestratorCLI.run(config)
    assert result1.success

    # Second run - should use cache
    result2 = OrchestratorCLI.run(config)
    assert result2.success
    assert "saved" in result2.metrics.get("cache_message", "")

    # Much faster than subprocess!
    assert result2.duration_seconds < 5.0
```

**Files to modify**:
- `tests/e2e/test_autonomous_fixing_cache.py`
- `tests/e2e/test_project_state_e2e.py`

---

## Phase 5: Test Builders
**Priority**: 🟢 Low | **Risk**: Low | **Impact**: Medium

### Goals
- Centralize test setup logic
- Readable, maintainable tests
- Reusable test utilities

### Tasks

#### 5.1 Create OrchestratorBuilder
- [ ] Fluent interface for building test orchestrators
- [ ] Sensible defaults
- [ ] Easy customization

**Acceptance Criteria**:
```python
# tests/fixtures/builders.py
class OrchestratorBuilder:
    """Builder for creating test orchestrators."""

    def __init__(self, tmp_path: Path):
        self.tmp_path = tmp_path
        self.config = OrchestratorConfig.for_testing(tmp_path)
        self._mock_ai = None
        self._mock_redis = None

    def with_projects(self, *projects: str) -> 'OrchestratorBuilder':
        self.config.projects = list(projects)
        return self

    def with_languages(self, *languages: str) -> 'OrchestratorBuilder':
        self.config.languages = list(languages)
        return self

    def with_mock_ai(self, responses: Dict[str, str] = None) -> 'OrchestratorBuilder':
        self._mock_ai = MockAIClient(responses)
        return self

    def with_no_redis(self) -> 'OrchestratorBuilder':
        self.config.redis_host = None
        return self

    def build(self) -> MultiLanguageOrchestrator:
        orchestrator = MultiLanguageOrchestrator(self.config)
        if self._mock_ai:
            orchestrator.iteration_engine.fixer.ai_client = self._mock_ai
        return orchestrator

# Usage:
def test_orchestrator(tmp_path):
    orchestrator = (OrchestratorBuilder(tmp_path)
        .with_projects(str(tmp_path / "project1"))
        .with_languages("python")
        .with_mock_ai({"error": "fixed"})
        .with_no_redis()
        .build())

    result = orchestrator.execute()
    assert result.success
```

**Files to create**:
- `tests/fixtures/builders.py`

---

#### 5.2 Create ValidatorBuilder
- [ ] Builder for PreflightValidator
- [ ] Easy mock injection

**Acceptance Criteria**:
```python
class ValidatorBuilder:
    def __init__(self, tmp_path: Path):
        self.tmp_path = tmp_path
        self.config = PreflightConfig()
        self._state_factory = None
        self._tracker = None

    def with_memory_state(self) -> 'ValidatorBuilder':
        self._state_factory = lambda path: MemoryStateRepository()
        return self

    def with_custom_tracker(self, tracker: ISetupTracker) -> 'ValidatorBuilder':
        self._tracker = tracker
        return self

    def build(self) -> PreflightValidator:
        tracker = self._tracker or MemorySetupTracker()
        return PreflightValidator(
            tracker,
            config=self.config,
            state_manager_factory=self._state_factory
        )

# Usage:
validator = (ValidatorBuilder(tmp_path)
    .with_memory_state()
    .build())
```

---

#### 5.3 Create ProjectFixture Helper
- [ ] Helper for creating test projects
- [ ] Pre-configured with common scenarios

**Acceptance Criteria**:
```python
class ProjectFixture:
    """Helper for creating test projects."""

    @staticmethod
    def create_python_project(
        tmp_path: Path,
        name: str = "test-project",
        with_hooks: bool = False,
        with_tests: bool = False,
        with_errors: bool = False
    ) -> Path:
        """Create a Python project with various configurations."""
        project = tmp_path / name
        project.mkdir()

        # Create basic structure
        (project / "src").mkdir()
        (project / "src" / "main.py").write_text("def main(): pass")

        if with_hooks:
            (project / ".pre-commit-config.yaml").write_text("repos: []")
            hooks = project / ".git" / "hooks"
            hooks.mkdir(parents=True)
            (hooks / "pre-commit").write_text("#!/bin/sh\npre-commit run")

        if with_tests:
            (project / "tests").mkdir()
            (project / "tests" / "test_main.py").write_text(
                "def test_main(): assert True"
            )

        if with_errors:
            (project / "src" / "errors.py").write_text(
                "def broken(:\n  return 'syntax error'"
            )

        return project

# Usage:
project = ProjectFixture.create_python_project(
    tmp_path,
    with_hooks=True,
    with_errors=True
)
```

---

#### 5.4 Create Common Test Fixtures
- [ ] pytest fixtures for common scenarios
- [ ] Centralize in `tests/conftest.py`

**Acceptance Criteria**:
```python
# tests/conftest.py
@pytest.fixture
def isolated_config(tmp_path):
    """Orchestrator config with isolated paths."""
    return OrchestratorConfig.for_testing(tmp_path)

@pytest.fixture
def mock_ai_client():
    """Mock AI client with default responses."""
    return MockAIClient(responses={
        "error": "fixed",
        "warning": "improved"
    })

@pytest.fixture
def memory_state_repo():
    """In-memory state repository."""
    return MemoryStateRepository()

@pytest.fixture
def python_test_project(tmp_path):
    """Python project ready for testing."""
    return ProjectFixture.create_python_project(
        tmp_path,
        with_hooks=True,
        with_tests=True
    )
```

---

## Phase 6: E2E Test Refactoring
**Priority**: 🟢 Low | **Risk**: Low | **Impact**: High

### Tasks

#### 6.1 Refactor test_autonomous_fixing_cache.py
- [ ] Use OrchestratorCLI.run instead of subprocess
- [ ] Use OrchestratorConfig.for_testing
- [ ] Use builders where appropriate
- [ ] Ensure tests pass

---

#### 6.2 Refactor test_project_state_e2e.py
- [ ] Use in-process execution
- [ ] Use memory state repos for speed
- [ ] Add more comprehensive scenarios

---

#### 6.3 Add New E2E Scenarios
- [ ] Multi-language project test
- [ ] Large project test (100+ files)
- [ ] Concurrent execution test
- [ ] Error recovery test

---

#### 6.4 Performance Benchmarks
- [ ] Measure before/after test suite performance
- [ ] Target: E2E tests < 30s (from current ~5min)
- [ ] Document performance improvements

---

#### 6.5 Update Testing Documentation
- [ ] Document new testing patterns
- [ ] Update README with testing guide
- [ ] Add examples of common test scenarios

---

## Success Metrics

### Test Performance
- [ ] Unit tests: < 5s (current: ~0.2s) ✅
- [ ] Integration tests: < 15s (current: ~12s) ✅
- [ ] E2E tests: < 30s (current: ~2min estimate)
- [ ] Total test suite: < 60s

### Code Quality
- [ ] 0 hardcoded paths in core code
- [ ] 100% dependency injection in core components
- [ ] All interfaces extracted and documented
- [ ] Test coverage > 85%

### Developer Experience
- [ ] Can run E2E tests without Redis/external services
- [ ] Can debug E2E tests in IDE (in-process)
- [ ] Test failures are immediately clear (no shell script parsing)
- [ ] New tests are easy to write (builders, fixtures)

---

## Implementation Notes

### Backward Compatibility Strategy
1. Add new parameters with default values
2. Keep old behavior when no config provided
3. Deprecate old patterns gradually
4. Remove after 2 releases

### Testing Strategy
1. Write tests for new code before refactoring
2. Ensure all existing tests pass after each phase
3. Add integration tests between phases
4. Final comprehensive E2E test

### Migration Path for Existing Code
1. Phase 1-2 can be done together (configs + DI)
2. Phase 3 independent (interfaces don't break existing code)
3. Phase 4-5 build on top (CLI + builders)
4. Phase 6 validates everything works

---

## Risk Mitigation

### High Risk Areas
1. **State management refactoring** - Core to system
   - Mitigation: Thorough integration tests, gradual rollout

2. **AI client interface** - Complex interactions
   - Mitigation: Start with read-only interface, expand gradually

3. **Breaking changes** - Existing deployments
   - Mitigation: Maintain backward compatibility, deprecation warnings

### Rollback Plan
- Each phase is independent
- Can rollback to previous phase if issues found
- All changes behind feature flags where appropriate

---

## Next Steps

1. ✅ Create this documentation
2. ✅ Phase 1.1: Create PreflightConfig
3. ✅ Phase 1.2: Create StateManagerConfig
4. ✅ Phase 1.3: Create OrchestratorConfig
5. ⏭️ Phase 1.4: Create SetupTrackerConfig
6. Review and approve plan with team

---

## Questions / Decisions Needed

- [ ] Should we support both YAML and programmatic config permanently?
- [ ] What's the deprecation timeline for old patterns?
- [ ] Do we need feature flags for gradual rollout?
- [ ] Should in-memory implementations live in `tests/` or `adapters/`?

---

**Last Updated**: 2025-10-04
**Owner**: Claude Code + Development Team
**Reviewers**: TBD
