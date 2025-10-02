# Test Setup Phase - Design Document

## Problem Statement

**Current Implementation Issues:**
```python
# javascript_adapter.py - HARDCODED ASSUMPTIONS
cmd = ['npm', 'test', '--']  # ❌ What if project uses yarn/pnpm?
                             # ❌ What if no "test" script in package.json?
                             # ❌ What if tests in different location?
```

**Real-World Variability:**
- **JavaScript**: npm/yarn/pnpm, jest/vitest/mocha, tests/test/__tests__
- **Python**: pytest/unittest, tests/test, sync/async
- **Flutter**: flutter test, test/widget_test, integration_test/
- **Go**: go test ./..., *_test.go files

**Need:** Robust, per-project test configuration with automatic discovery.

## Solution: Test Setup Phase

### Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    ITERATION START                           │
└────────────────────────────┬─────────────────────────────────┘
                             ↓
┌──────────────────────────────────────────────────────────────┐
│  NEW: Test Setup Phase (runs once per project)              │
│                                                              │
│  1. Check if test config exists                             │
│     └─ config/projects/{project}-tests.yaml                 │
│                                                              │
│  2. If not exists: AUTO-DISCOVER                            │
│     ├─ Detect package manager (npm/yarn/pnpm)               │
│     ├─ Find test script in package.json                     │
│     ├─ Discover test directories                            │
│     ├─ Detect test framework                                │
│     └─ Save discovered config                               │
│                                                              │
│  3. Load test configuration                                 │
│     └─ Returns: TestConfig object                           │
└────────────────────────────┬─────────────────────────────────┘
                             ↓
┌──────────────────────────────────────────────────────────────┐
│        Run Tests (using discovered config)                   │
│  $ {runner} {command} {args}                                │
│  Example: pnpm run test:unit --bail                         │
└──────────────────────────────────────────────────────────────┘
```

## Test Configuration Schema

### Option 1: Per-Project Test Config Files

```yaml
# config/projects/cc-task-manager-tests.yaml
project: /home/rmondo/repos/cc-task-manager
language: javascript

test_setup:
  # Discovery results
  discovered_at: "2025-10-03T10:30:00"
  discovery_method: "auto"  # or "manual"

  # Test execution
  runner: "pnpm"           # npm, yarn, pnpm, or direct command
  command: "test"          # script name in package.json
  framework: "jest"        # jest, vitest, mocha, etc.

  # Test locations
  test_directories:
    - "tests/"
    - "__tests__/"

  # Test patterns
  test_file_patterns:
    - "**/*.test.js"
    - "**/*.spec.js"

  # Execution strategies
  strategies:
    minimal:
      args: ["--testPathPattern=unit", "--bail"]
      timeout: 300
    selective:
      args: ["--testPathPattern=(unit|integration)"]
      timeout: 900
    comprehensive:
      args: []
      timeout: 1800

  # Validation
  verified: true           # Has test execution been verified?
  last_successful_run: "2025-10-03T10:35:00"
```

### Option 2: Embedded in Main Project Config

```yaml
# config/projects/cc-task-manager.yaml
projects:
  - path: "/home/rmondo/repos/cc-task-manager"
    language: "javascript"

languages:
  enabled: ["javascript"]
  javascript:
    # ... existing config ...

# NEW: Test configuration section
test_config:
  runner: "pnpm"
  command: "test"
  framework: "jest"
  test_directories: ["tests/", "__tests__/"]
  test_patterns: ["**/*.test.js", "**/*.spec.js"]
  strategies:
    minimal: { args: ["--testPathPattern=unit", "--bail"], timeout: 300 }
    selective: { args: ["--testPathPattern=(unit|integration)"], timeout: 900 }
    comprehensive: { args: [], timeout: 1800 }
```

### Recommendation: **Option 2 (Embedded)**

**Why:**
- ✅ Single config file per project (simpler)
- ✅ Test config lives with project config
- ✅ No config file explosion
- ✅ Easy to version control
- ✅ Clear project-level ownership

## Discovery Logic

### JavaScript Discovery

```python
def discover_javascript_tests(project_path: str) -> TestConfig:
    config = TestConfig()

    # 1. Detect package manager
    if (project_path / "pnpm-lock.yaml").exists():
        config.runner = "pnpm"
    elif (project_path / "yarn.lock").exists():
        config.runner = "yarn"
    else:
        config.runner = "npm"

    # 2. Read package.json
    package_json = json.loads((project_path / "package.json").read_text())
    scripts = package_json.get("scripts", {})

    # 3. Find test script
    if "test" in scripts:
        config.command = "test"
    elif "test:unit" in scripts:
        config.command = "test:unit"
    else:
        config.command = None  # No test script!

    # 4. Detect framework
    deps = {**package_json.get("dependencies", {}),
            **package_json.get("devDependencies", {})}

    if "jest" in deps:
        config.framework = "jest"
    elif "vitest" in deps:
        config.framework = "vitest"
    elif "mocha" in deps:
        config.framework = "mocha"

    # 5. Find test directories
    test_dirs = []
    for candidate in ["tests", "__tests__", "test", "spec"]:
        if (project_path / candidate).exists():
            test_dirs.append(f"{candidate}/")
    config.test_directories = test_dirs

    # 6. Find test files
    test_files = list(project_path.glob("**/*.test.{js,ts,jsx,tsx}"))
    test_files += list(project_path.glob("**/*.spec.{js,ts,jsx,tsx}"))
    config.test_file_patterns = ["**/*.test.*", "**/*.spec.*"]

    return config
```

### Python Discovery

```python
def discover_python_tests(project_path: str) -> TestConfig:
    config = TestConfig()

    # 1. Direct command (pytest/python)
    config.runner = "pytest"  # or "python -m pytest"

    # 2. Check for pytest
    requirements = []
    if (project_path / "requirements.txt").exists():
        requirements = (project_path / "requirements.txt").read_text().split()
    if (project_path / "pyproject.toml").exists():
        # Parse pyproject.toml for pytest
        pass

    if "pytest" in requirements:
        config.framework = "pytest"
    else:
        config.framework = "unittest"

    # 3. Find test directories
    test_dirs = []
    for candidate in ["tests", "test"]:
        if (project_path / candidate).exists():
            test_dirs.append(f"{candidate}/")
    config.test_directories = test_dirs

    # 4. Test patterns
    if config.framework == "pytest":
        config.test_file_patterns = ["test_*.py", "*_test.py"]
    else:
        config.test_file_patterns = ["test*.py"]

    return config
```

### Flutter Discovery

```python
def discover_flutter_tests(project_path: str) -> TestConfig:
    config = TestConfig()

    config.runner = "flutter"
    config.command = "test"
    config.framework = "flutter_test"

    # Find test directories
    test_dirs = []
    for candidate in ["test", "test/widget_test", "integration_test"]:
        if (project_path / candidate).exists():
            test_dirs.append(f"{candidate}/")
    config.test_directories = test_dirs

    config.test_file_patterns = ["**/*_test.dart"]

    return config
```

## Implementation Plan

### 1. Create TestConfig Data Class

```python
# airflow_dags/autonomous_fixing/core/test_config.py
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from pathlib import Path
import json
import yaml

@dataclass
class TestStrategy:
    """Configuration for a test execution strategy."""
    args: List[str] = field(default_factory=list)
    timeout: int = 300

@dataclass
class TestConfig:
    """Test execution configuration for a project."""
    # Discovery metadata
    project_path: str = ""
    language: str = ""
    discovered_at: Optional[str] = None
    discovery_method: str = "auto"  # auto or manual

    # Execution config
    runner: str = ""  # npm, yarn, pnpm, pytest, flutter, go
    command: Optional[str] = None  # test, test:unit, etc.
    framework: Optional[str] = None  # jest, pytest, flutter_test, etc.

    # Test locations
    test_directories: List[str] = field(default_factory=list)
    test_file_patterns: List[str] = field(default_factory=list)

    # Strategies
    strategies: Dict[str, TestStrategy] = field(default_factory=dict)

    # Validation
    verified: bool = False
    last_successful_run: Optional[str] = None

    def save(self, config_path: Path):
        """Save test config to YAML."""
        with open(config_path, 'w') as f:
            yaml.dump(self.to_dict(), f)

    @classmethod
    def load(cls, config_path: Path) -> 'TestConfig':
        """Load test config from YAML."""
        with open(config_path) as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)

    def to_dict(self) -> dict:
        """Convert to dict for serialization."""
        return {
            'project_path': self.project_path,
            'language': self.language,
            'discovered_at': self.discovered_at,
            'discovery_method': self.discovery_method,
            'runner': self.runner,
            'command': self.command,
            'framework': self.framework,
            'test_directories': self.test_directories,
            'test_file_patterns': self.test_file_patterns,
            'strategies': {
                name: {'args': s.args, 'timeout': s.timeout}
                for name, s in self.strategies.items()
            },
            'verified': self.verified,
            'last_successful_run': self.last_successful_run
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'TestConfig':
        """Create from dict."""
        strategies = {
            name: TestStrategy(**cfg)
            for name, cfg in data.get('strategies', {}).items()
        }
        return cls(
            project_path=data.get('project_path', ''),
            language=data.get('language', ''),
            discovered_at=data.get('discovered_at'),
            discovery_method=data.get('discovery_method', 'auto'),
            runner=data.get('runner', ''),
            command=data.get('command'),
            framework=data.get('framework'),
            test_directories=data.get('test_directories', []),
            test_file_patterns=data.get('test_file_patterns', []),
            strategies=strategies,
            verified=data.get('verified', False),
            last_successful_run=data.get('last_successful_run')
        )
```

### 2. Create Test Discovery Module

```python
# airflow_dags/autonomous_fixing/core/test_discovery.py
from pathlib import Path
from datetime import datetime
from .test_config import TestConfig, TestStrategy

class TestDiscovery:
    """Discovers test configuration for projects."""

    def discover(self, project_path: str, language: str) -> TestConfig:
        """Auto-discover test configuration."""
        if language == "javascript":
            return self._discover_javascript(project_path)
        elif language == "python":
            return self._discover_python(project_path)
        elif language == "flutter":
            return self._discover_flutter(project_path)
        elif language == "go":
            return self._discover_go(project_path)
        else:
            return self._create_fallback(project_path, language)

    def _discover_javascript(self, project_path: str) -> TestConfig:
        """Discover JavaScript test configuration."""
        # ... implementation from above
        pass

    def _discover_python(self, project_path: str) -> TestConfig:
        """Discover Python test configuration."""
        # ... implementation from above
        pass

    # ... etc
```

### 3. Update Project Config Schema

```yaml
# config/projects/cc-task-manager.yaml
projects:
  - path: "/home/rmondo/repos/cc-task-manager"
    language: "javascript"

languages:
  enabled: ["javascript"]
  javascript:
    linters: ["eslint"]
    type_checker: "tsc"
    test_framework: "jest"  # Keep for compatibility
    complexity_threshold: 15
    max_file_lines: 800

# NEW: Test configuration (auto-discovered or manual)
test_config:
  discovery: "auto"  # auto or manual
  runner: "pnpm"
  command: "test"
  framework: "jest"
  test_directories:
    - "tests/"
    - "__tests__/"
  test_patterns:
    - "**/*.test.js"
    - "**/*.spec.js"
  strategies:
    minimal:
      args: ["--testPathPattern=unit", "--bail"]
      timeout: 300
    selective:
      args: ["--testPathPattern=(unit|integration)"]
      timeout: 900
    comprehensive:
      args: []
      timeout: 1800

# ... rest of config
```

### 4. Update Language Adapters

```python
# javascript_adapter.py
class JavaScriptAdapter(BaseLanguageAdapter):
    def __init__(self, config: Dict):
        super().__init__(config)
        # NEW: Load test config
        self.test_config = self._load_test_config()

    def _load_test_config(self) -> TestConfig:
        """Load or discover test configuration."""
        # Check if config exists
        if 'test_config' in self.config:
            return TestConfig.from_dict(self.config['test_config'])

        # Auto-discover
        print("🔍 Auto-discovering test configuration...")
        discovery = TestDiscovery()
        test_config = discovery.discover(
            self.config['projects'][0]['path'],
            'javascript'
        )

        # Save for next time
        self._save_test_config(test_config)

        return test_config

    def analyze_tests(self, project_path: str, strategy: str) -> AnalysisResult:
        """Run tests using discovered configuration."""
        result = AnalysisResult()
        start_time = time.time()

        try:
            # Build command from test config
            if self.test_config.runner == "npm":
                cmd = ['npm', 'run', self.test_config.command]
            elif self.test_config.runner == "yarn":
                cmd = ['yarn', self.test_config.command]
            elif self.test_config.runner == "pnpm":
                cmd = ['pnpm', 'run', self.test_config.command]

            # Add strategy args
            if strategy in self.test_config.strategies:
                strategy_config = self.test_config.strategies[strategy]
                cmd.extend(strategy_config.args)
                timeout = strategy_config.timeout
            else:
                timeout = 1800

            # Run tests
            test_result = subprocess.run(
                cmd,
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            # ... parse results
```

## Benefits

### 1. Robustness
- ✅ No hardcoded assumptions
- ✅ Works with npm, yarn, pnpm automatically
- ✅ Discovers actual test setup
- ✅ Handles missing test scripts gracefully

### 2. Maintainability
- ✅ Config-driven (YAML, not code)
- ✅ Easy to override discovered config
- ✅ Clear separation: discovery vs execution

### 3. Transparency
- ✅ Saved config shows exactly how tests run
- ✅ Can manually adjust if discovery wrong
- ✅ Verifies test execution works

### 4. Flexibility
- ✅ Per-project customization
- ✅ Multiple test strategies per project
- ✅ Language-specific discovery logic

## Migration Plan

### Phase 1: Add Test Config to Existing Projects
```bash
# Run discovery for all 5 projects
python scripts/discover_test_configs.py

# Review generated configs
cat config/projects/cc-task-manager.yaml  # Check test_config section

# Test execution
pm2 restart all
```

### Phase 2: Verify and Adjust
```bash
# If discovery wrong, manually edit:
vim config/projects/warps.yaml

test_config:
  runner: "npm"  # Change from yarn to npm
  command: "test:ci"  # Use CI script instead
```

### Phase 3: Deploy
```bash
git commit -m "feat: Add test discovery and configuration"
pm2 reload all
```

## Questions to Answer

1. **Where to store discovered configs?**
   - ✅ Embedded in main project YAML (recommended)
   - ❌ Separate files (too many files)

2. **When to run discovery?**
   - ✅ First time project analyzed
   - ✅ On demand (flag: `--rediscover-tests`)
   - ❌ Every iteration (too slow)

3. **What if discovery fails?**
   - ✅ Log warning
   - ✅ Try to run tests anyway with fallback
   - ✅ Mark `verified: false` in config
   - ✅ Continue to P1 fixes (tests not blocking)

4. **Manual override?**
   - ✅ Yes! User can edit YAML anytime
   - ✅ Set `discovery: "manual"` to prevent auto-discovery

## Summary

**Current Problem:**
- Hardcoded test commands in language adapters
- Fragile assumptions about package managers, test scripts, directories
- No per-project customization

**Solution:**
- Test setup phase with auto-discovery
- Config-driven test execution
- Per-project test configuration in YAML
- Graceful fallbacks

**Benefits:**
- Robust and flexible
- Clear and maintainable
- Project-specific customization
- KISS: Simple YAML config
