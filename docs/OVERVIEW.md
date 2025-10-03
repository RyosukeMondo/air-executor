# Air Executor - Complete Overview

**Air Executor** is a lightweight, flexible job execution system for Python that enables asynchronous task management with subprocess isolation, integrated with Claude AI and Apache Airflow for autonomous code quality improvement.

## What is Air Executor?

Air Executor provides three core capabilities:

1. **Job Execution Framework** - Run isolated subprocess tasks with lifecycle management
2. **Claude AI Integration** - Interface with Claude for AI-powered code assistance
3. **Autonomous Code Fixing** - Multi-language automated code quality improvement

## Core Features

### 1. Job Execution System
- ✅ **Asynchronous Execution**: Run jobs as isolated subprocesses
- ✅ **Task Management**: Create, monitor, and control job lifecycle
- ✅ **Dependency Handling**: Group related tasks with dependencies
- ✅ **Storage Backend**: Persistent job state with file-based storage
- ✅ **CLI Interface**: Easy-to-use command-line interface

### 2. Claude AI Integration
- ✅ **Wrapper Protocol**: JSON-based stdin/stdout communication with Claude CLI
- ✅ **Stream Handling**: Real-time event processing from Claude
- ✅ **Session Management**: Maintain context across interactions
- ✅ **Airflow Integration**: Execute Claude tasks through Airflow DAGs

### 3. Autonomous Code Fixing
- ✅ **Multi-Language Support**: Python, JavaScript/TypeScript, Flutter/Dart, Go
- ✅ **Priority-Based Execution**: P1 (Static) → P2 (Tests) → P3 (Coverage) → P4 (E2E)
- ✅ **Adaptive Testing**: Time-aware test strategy based on project health
- ✅ **Health Monitoring**: Comprehensive metrics (build, tests, coverage, quality)
- ✅ **Auto-Discovery**: Find and fix issues across monorepos

## Quick Start

### Prerequisites
- Python 3.10+
- Claude Code CLI (npm install -g @anthropic-ai/claude-code)
- Redis (optional, for autonomous fixing)
- Apache Airflow 2.0+ (optional)

### Installation

```bash
# Clone repository
git clone https://github.com/RyosukeMondo/air-executor.git
cd air-executor

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install
pip install -e .

# Install Claude CLI
npm install -g @anthropic-ai/claude-code
claude login
```

### Basic Usage

**Simple Job Execution:**
```python
from air_executor import Job, Task, SubprocessRunner

# Create job
job = Job(name="data_processing")
job.add_task(Task(name="fetch", command=["python", "fetch.py"]))
job.add_task(Task(name="process", command=["python", "process.py"], depends_on=["fetch"]))

# Execute
runner = SubprocessRunner()
runner.run_job(job)
```

**Autonomous Code Fixing:**
```bash
# Run on single project
./scripts/run_autonomous_fix.sh config/projects/my-project.yaml

# Run on all projects with PM2
pm2 start config/pm2.config.js
pm2 logs
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                   User Interface                    │
│  (CLI, Airflow UI, Direct Python API, Scripts)     │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│              Air Executor Core                      │
│  ┌────────────┐  ┌──────────┐  ┌────────────────┐  │
│  │ Job Manager│  │ Storage  │  │ Task Executor  │  │
│  └────────────┘  └──────────┘  └────────────────┘  │
└─────────────────┬───────────────────────────────────┘
                  │
        ┌─────────┴──────────┬──────────────┐
        │                    │              │
┌───────▼────────┐ ┌────────▼────────┐ ┌──▼──────────────┐
│ Claude Wrapper │ │ Airflow DAGs    │ │ Multi-Language  │
│ (SDK/CLI)      │ │                 │ │ Orchestrator    │
└────────────────┘ └─────────────────┘ └─────────────────┘
```

### Core Components

**Job Manager**: Creates and manages job lifecycle, tracks state and metadata

**Task Executor**: Executes tasks as isolated subprocesses, manages timeout and cancellation

**Storage Backend**: Persists job state with JSON serialization, extensible for other backends

**Claude Wrapper**: Interfaces with Claude AI via CLI with JSON protocol and streaming events

**Multi-Language Orchestrator**: Coordinates autonomous fixing across Python, JS/TS, Flutter, Go

## Multi-Language Autonomous Fixing

### Priority-Based Execution Strategy

```
P1: Static Analysis (ALWAYS RUN, ~2 min)
├─ Linting, type checking, code quality
├─ File size & complexity analysis
└─ Gate: 90% success threshold
    ↓
P2: Unit Tests (ADAPTIVE, 5-30 min based on health)
├─ Minimal (< 30% health): 5 min
├─ Selective (30-60% health): 15 min
└─ Comprehensive (> 60% health): 30 min
    └─ Gate: 85% pass threshold
        ↓
P3: Coverage Analysis (CONDITIONAL, if P1≥90% AND P2≥85%)
├─ Identify coverage gaps
├─ Generate tests for uncovered code
└─ Target: 80% coverage
    ↓
P4: E2E Testing (FINAL PHASE, if overall health ≥ 90%)
├─ Integration/E2E test execution
├─ Runtime error capture
└─ Regression test generation
```

### Supported Languages

| Language | Static Analysis | Tests | Coverage | E2E |
|----------|----------------|-------|----------|-----|
| **Python** | pylint, mypy | pytest | pytest-cov | playwright |
| **JavaScript/TypeScript** | eslint, tsc | jest/vitest | jest --coverage | playwright/cypress |
| **Flutter/Dart** | flutter analyze | flutter test | flutter test --coverage | integration tests |
| **Go** | go vet, staticcheck | go test | go test -cover | integration tests |

### Time Efficiency

**Adaptive Strategy**:
- Unhealthy projects (< 30% health): 5 min tests → fast feedback
- Medium health (30-60%): 15 min selective tests
- Healthy projects (> 60%): 30 min comprehensive tests

**Gated Execution**:
- Skip expensive operations (P3, P4) when basics broken
- 40-70% time savings on unhealthy projects

## Key Workflows

### 1. Autonomous Fixing Workflow

```bash
# Single project
./scripts/run_autonomous_fix.sh config/projects/air-executor.yaml

# Monitor progress
tail -f logs/orchestrator_run.log

# Check results
git log --oneline -5
```

### 2. Airflow Integration Workflow

```bash
# Start Airflow
airflow webserver -p 8080 &
airflow scheduler &

# Sync DAGs
./scripts/sync_dags_to_airflow.sh

# Trigger DAG
airflow dags trigger claude_query_sdk --conf '{"prompt": "Analyze code"}'
```

### 3. Real Projects Workflow

```bash
# Configure projects in config/projects/*.yaml

# Run with PM2
pm2 start config/pm2.config.js
pm2 logs
pm2 status

# Stop
pm2 stop all
```

## Configuration

### Project Configuration

```yaml
# config/projects/my-project.yaml
project_name: "my-project"
project_path: "/path/to/project"
language: "python"  # or javascript, flutter, go

# Priority thresholds
priorities:
  p1_static:
    success_threshold: 0.90
  p2_tests:
    success_threshold: 0.85
    adaptive_strategy: true

# Execution limits
execution:
  max_iterations: 5
  max_duration_hours: 2
  auto_commit: true
```

### Language-Specific Configuration

```yaml
# Python
python:
  linters: ["pylint", "mypy"]
  test_framework: "pytest"
  complexity_threshold: 10
  max_file_lines: 500

# JavaScript/TypeScript
javascript:
  linters: ["eslint"]
  type_checker: "tsc"
  test_framework: "jest"

# Flutter
flutter:
  analyzer_args: "--fatal-infos --fatal-warnings"
  test_timeout: 600

# Go
go:
  linters: ["go vet", "staticcheck"]
  test_timeout: 300
```

## Health Monitoring

### Comprehensive Health Score

```python
health_score = (
    build_status * 0.3 +      # 30% - Does it build?
    test_quality * 0.3 +      # 30% - Tests pass + coverage
    code_quality * 0.2 +      # 20% - File size, complexity
    analysis_clean * 0.2      # 20% - Lint errors
)
```

### Metrics Tracked

**Build Metrics**: Build status, error count, warnings, analysis issues

**Test Metrics**: Total tests, pass rate, unit/integration/E2E/widget breakdown

**Coverage Metrics**: Coverage %, low-coverage files, uncovered areas

**Code Quality**: File sizes, complexity, nesting depth, violations

## Safety Features

✅ **All changes are commits** - Easy to review and revert
✅ **No auto-push** - Manual push gives you control
✅ **Branch aware** - Works on current branch
✅ **Circuit breakers** - Stops on repeated failures
✅ **Time limits** - Won't run forever
✅ **Validation gates** - Ensures quality before proceeding

## Performance

### Execution Timeline

| Phase | Time | Description |
|-------|------|-------------|
| P1 Static | 0-2 min | Parallel analysis all languages |
| P1 Fixes | 2-10 min | Quick error fixes |
| P2 Tests | 10-40 min | Adaptive testing strategy |
| P2 Fixes | 40-60 min | Test failure fixes |
| P3 Coverage | 60-90 min | If gate passed |
| P4 E2E | 90-180 min | If healthy |

### Efficiency Gains

**Old System**: All checks always run (30-60 min regardless of health)

**New System**:
- Fast static first (2 min)
- Adaptive testing (5-30 min based on health)
- Skip expensive ops when not ready
- **Result**: 40-70% time savings

## Use Cases

### 1. Monorepo Code Quality
- Auto-detect all projects in monorepo
- Run language-specific checks in parallel
- Gradual quality improvement

### 2. CI/CD Integration
- Pre-commit hooks for quality gates
- Automated fixing in CI pipeline
- Coverage reporting

### 3. Technical Debt Reduction
- Systematic refactoring
- Test generation for legacy code
- Complexity reduction

### 4. Development Workflow
- Local development with PM2
- Real-time code quality feedback
- Auto-fixing during development

## Project Structure

```
air-executor/
├── src/air_executor/       # Core package
│   ├── core/              # Job and task models
│   ├── manager/           # Job execution management
│   ├── runners/           # Execution backends
│   ├── storage/           # Persistence layer
│   └── cli/               # Command-line interface
├── scripts/               # Utility scripts
│   ├── run_autonomous_fix.sh      # Main wrapper
│   ├── check_tools.sh             # Tool validation
│   ├── setup_*.sh                 # Setup scripts
│   └── claude_wrapper.py          # Claude interface
├── config/                # Configuration files
│   ├── projects/          # Per-project configs
│   └── pm2.config.js      # PM2 process management
├── airflow_dags/          # Airflow DAG definitions
├── tests/                 # Test suite
└── docs/                  # Documentation
```

## Next Steps

Choose your path:

**For New Users**: [Getting Started Guide](./GETTING_STARTED.md)

**For Autonomous Fixing**: [Autonomous Fixing Guide](./AUTONOMOUS_FIXING.md)

**For Configuration**: [Configuration Reference](./CONFIGURATION.md)

**For Architecture**: [Architecture Deep Dive](./ARCHITECTURE.md)

**For Troubleshooting**: [Troubleshooting Guide](./reference/troubleshooting.md)

## Resources

- **GitHub**: [RyosukeMondo/air-executor](https://github.com/RyosukeMondo/air-executor)
- **Quick Start**: See [QUICKSTART.md](../QUICKSTART.md) in project root
- **Issues**: [GitHub Issues](https://github.com/RyosukeMondo/air-executor/issues)
- **Apache Airflow**: [Official Docs](https://airflow.apache.org/docs/)
- **Claude AI**: [Anthropic Docs](https://docs.anthropic.com/)

## Key Design Principles

1. **Modularity**: Components are loosely coupled and independently testable
2. **Extensibility**: Easy to add new task types and language adapters
3. **Reliability**: Comprehensive error handling and recovery
4. **Observability**: Detailed logging and health monitoring
5. **Safety**: Circuit breakers, validation gates, and rollback support
6. **Efficiency**: Priority-based execution and adaptive strategies

---

**Version**: 1.0
**Last Updated**: 2025-01-10
**Maintained by**: RyosukeMondo
