# Project Structure

## Directory Organization

```
air-executor/
├── src/                           # Source code
│   ├── air_executor/              # Main package
│   │   ├── __init__.py
│   │   ├── core/                  # Core abstractions
│   │   │   ├── job.py             # Job state management
│   │   │   ├── task.py            # Task representation
│   │   │   └── runner.py          # Runner interface
│   │   ├── manager/               # Job manager implementation
│   │   │   ├── poller.py          # Polling loop
│   │   │   ├── spawner.py         # Runner spawner
│   │   │   └── config.py          # Configuration management
│   │   ├── runners/               # Task runner implementations
│   │   │   ├── base.py            # Base runner class
│   │   │   ├── claude_wrapper.py  # Claude Code CLI wrapper
│   │   │   └── subprocess_utils.py # Process management utilities
│   │   ├── orchestrators/         # Orchestrator-specific implementations
│   │   │   ├── airflow/
│   │   │   │   ├── dags/          # Airflow DAG definitions
│   │   │   │   ├── operators/     # Custom Airflow operators
│   │   │   │   └── executors/     # Executor configurations
│   │   │   └── prefect/
│   │   │       ├── flows/         # Prefect flow definitions
│   │   │       ├── workers/       # Custom worker implementations
│   │   │       └── deployments/   # Deployment configurations
│   │   ├── storage/               # State persistence
│   │   │   ├── file_store.py      # File-based storage
│   │   │   └── db_store.py        # Database storage (future)
│   │   ├── cli/                   # CLI interface
│   │   │   ├── main.py            # CLI entry point
│   │   │   ├── commands/          # CLI commands
│   │   │   └── ui.py              # Terminal UI (rich-based)
│   │   └── utils/                 # Shared utilities
│   │       ├── logging.py         # Structured logging setup
│   │       ├── validation.py      # Input validation
│   │       └── exceptions.py      # Custom exceptions
├── tests/                         # Test files
│   ├── unit/                      # Unit tests
│   │   ├── test_job.py
│   │   ├── test_task.py
│   │   ├── test_poller.py
│   │   └── test_spawner.py
│   ├── integration/               # Integration tests
│   │   ├── test_airflow_flow.py
│   │   ├── test_prefect_flow.py
│   │   └── test_end_to_end.py
│   ├── fixtures/                  # Test fixtures
│   │   ├── jobs.py                # Sample job definitions
│   │   └── tasks.py               # Sample task data
│   └── mocks/                     # Mock objects
│       ├── mock_runner.py
│       └── mock_orchestrator.py
├── docs/                          # Documentation
│   ├── idea.md                    # Original concept document
│   ├── tech_research.md           # Technical research (Japanese)
│   ├── architecture/              # Architecture documentation
│   │   ├── overview.md
│   │   ├── airflow-design.md
│   │   └── prefect-design.md
│   └── guides/                    # User guides
│       ├── quickstart.md
│       ├── airflow-setup.md
│       └── prefect-setup.md
├── examples/                      # Usage examples
│   ├── simple_job.json            # Basic job definition
│   ├── dynamic_tasks.json         # Job with dynamic sub-tasks
│   └── claude_workflow.json       # Claude Code integration example
├── scripts/                       # Utility scripts
│   ├── setup_airflow.sh           # Airflow environment setup
│   ├── setup_prefect.sh           # Prefect environment setup
│   └── run_dev.sh                 # Development environment launcher
├── .air-executor/                 # Runtime directory (gitignored)
│   ├── jobs/                      # Job state files
│   │   └── {job-name}/
│   │       ├── state.json         # Job status
│   │       ├── tasks.json         # Task queue
│   │       └── logs/              # Task execution logs
│   └── config.yaml                # User configuration
├── .spec-workflow/                # Spec workflow (development)
│   ├── steering/                  # Steering documents
│   └── specs/                     # Feature specifications
├── requirements.txt               # Python dependencies (all)
├── requirements-airflow.txt       # Airflow-specific dependencies
├── requirements-prefect.txt       # Prefect-specific dependencies
├── requirements-dev.txt           # Development dependencies
├── Makefile                       # Build automation
├── pyproject.toml                 # Python project configuration
├── setup.py                       # Package setup
└── README.md                      # Project overview
```

## Naming Conventions

### Files
- **Modules**: `snake_case` (e.g., `job_manager.py`, `task_runner.py`)
- **Classes**: `PascalCase` in `snake_case` files (e.g., `JobManager` in `job_manager.py`)
- **Services/Handlers**: `snake_case` with descriptive suffix (e.g., `claude_wrapper.py`, `file_store.py`)
- **Utilities/Helpers**: `snake_case` with `_utils` suffix (e.g., `subprocess_utils.py`, `validation.py`)
- **Tests**: `test_[module_name].py` (e.g., `test_job.py`, `test_poller.py`)

### Code
- **Classes/Types**: `PascalCase` (e.g., `JobManager`, `TaskRunner`, `JobState`)
- **Functions/Methods**: `snake_case` (e.g., `spawn_runner()`, `poll_job_status()`, `queue_task()`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_POLL_INTERVAL`, `MAX_RETRY_COUNT`)
- **Variables**: `snake_case` (e.g., `job_id`, `task_queue`, `runner_status`)
- **Private Members**: `_leading_underscore` (e.g., `_internal_state`, `_validate_config()`)

### Orchestrator-Specific
- **Airflow DAGs**: `kebab-case` (e.g., `job-manager-dag`, `dynamic-task-runner`)
- **Prefect Flows**: `snake_case` (e.g., `job_orchestrator_flow`, `task_runner_flow`)
- **Kubernetes Resources**: `kebab-case` (e.g., `task-runner-pod`, `job-namespace`)

## Import Patterns

### Import Order
1. Standard library imports
2. Third-party library imports (alphabetical)
3. Orchestrator-specific imports (airflow, prefect)
4. Local package imports (air_executor modules)
5. Relative imports (same package)

### Example Import Structure
```python
# Standard library
import os
import json
from pathlib import Path
from typing import Optional, List, Dict

# Third-party
import structlog
from pydantic import BaseModel, Field

# Orchestrator-specific
from airflow import DAG
from airflow.operators.python import PythonOperator

# Local package
from air_executor.core.job import Job, JobState
from air_executor.core.task import Task
from air_executor.storage.file_store import FileStore

# Relative imports (within same package)
from .base import BaseRunner
from .subprocess_utils import run_command
```

### Module/Package Organization
- **Absolute imports preferred**: Always import from package root (`from air_executor.core.job import Job`)
- **Relative imports limited**: Only within same subpackage (within `orchestrators/airflow/` or `runners/`)
- **No circular dependencies**: Core modules should not import from orchestrators or runners
- **Dependency direction**: `cli` → `manager` → `core` ← `storage`, `orchestrators` → `core`

## Code Structure Patterns

### Module/Class Organization
```python
# 1. Module docstring
"""
Job state management and persistence.

This module provides classes for representing job state,
managing job lifecycle, and persisting job data.
"""

# 2. Imports (as per import patterns above)

# 3. Constants and configuration
DEFAULT_POLL_INTERVAL = 5
MAX_TASKS_PER_JOB = 1000

# 4. Type definitions and dataclasses
class JobState(str, Enum):
    WAITING = "waiting"
    WORKING = "working"
    COMPLETED = "completed"
    FAILED = "failed"

# 5. Main implementation classes
class Job(BaseModel):
    """Represents a job with tasks and state."""
    id: str
    name: str
    state: JobState
    tasks: List[Task] = Field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task to the job queue."""
        pass

# 6. Helper/utility functions (module-level)
def validate_job_name(name: str) -> bool:
    """Validate job name against naming rules."""
    pass

# 7. Module exports (if needed)
__all__ = ["Job", "JobState", "validate_job_name"]
```

### Function/Method Organization
```python
def process_task(
    task: Task,
    config: Config,
    logger: structlog.BoundLogger
) -> TaskResult:
    """
    Process a single task through the runner.

    Args:
        task: Task to execute
        config: Configuration settings
        logger: Structured logger instance

    Returns:
        TaskResult with execution outcome

    Raises:
        TaskExecutionError: If task execution fails
    """
    # 1. Input validation
    if not task.is_valid():
        raise ValueError(f"Invalid task: {task.id}")

    # 2. Setup and preparation
    runner = get_runner(config)
    logger.info("starting_task", task_id=task.id)

    # 3. Core logic
    try:
        result = runner.execute(task)

    # 4. Error handling
    except Exception as e:
        logger.error("task_failed", task_id=task.id, error=str(e))
        raise TaskExecutionError(task.id, e)

    # 5. Cleanup and return
    finally:
        runner.cleanup()

    logger.info("task_completed", task_id=task.id)
    return result
```

## Code Organization Principles

1. **Single Responsibility**: Each file handles one domain concept
   - `job.py` = Job entity and lifecycle
   - `poller.py` = Polling loop logic
   - `spawner.py` = Runner spawning logic

2. **Modularity**: Clear boundaries between subsystems
   - `core/` = Domain models (no orchestrator dependencies)
   - `orchestrators/` = Orchestrator-specific implementations
   - `manager/` = Orchestrator-agnostic job management

3. **Testability**: Easy to mock and test in isolation
   - Dependency injection for storage, runners, config
   - Interface-based design (base classes, protocols)
   - Pure functions where possible

4. **Consistency**: Follow established patterns throughout codebase
   - All errors inherit from `AirExecutorError`
   - All config uses pydantic models
   - All logging uses structlog

## Module Boundaries

### Dependency Direction
```
       ┌──────────┐
       │   cli    │
       └────┬─────┘
            │
       ┌────▼─────┐
       │ manager  │
       └────┬─────┘
            │
    ┌───────┼───────┐
    │       │       │
┌───▼──┐ ┌─▼────┐ ┌▼──────┐
│ core │ │ stor │ │ orch  │
└──────┘ └──────┘ └───────┘
```

- **Core**: No dependencies on other packages (pure domain models)
- **Storage**: Depends only on core
- **Orchestrators**: Depends only on core (implements core interfaces)
- **Manager**: Depends on core, storage, orchestrators (orchestration logic)
- **CLI**: Depends on all (user interface layer)

### Module Interaction Rules
- **Core → Nothing**: Core is dependency-free
- **Storage → Core**: Storage persists core entities
- **Orchestrators → Core**: Orchestrators implement core runner interface
- **Manager → Core, Storage, Orchestrators**: Manager coordinates all
- **CLI → Manager**: CLI is thin wrapper around manager

### Boundary Enforcement
- Use `__all__` to explicitly define public APIs
- Mark internal functions with leading underscore
- Type hints enforce interface contracts
- Import rules prevent circular dependencies

## Code Size Guidelines

- **File size**: Maximum 500 lines per file (excluding tests)
- **Function/Method size**: Maximum 50 lines per function (prefer 20-30)
- **Class complexity**: Maximum 10 public methods per class
- **Nesting depth**: Maximum 4 levels (prefer 2-3)
- **Function parameters**: Maximum 5 parameters (use config objects for more)

**Refactoring triggers:**
- File exceeds 400 lines → split into submodules
- Function exceeds 40 lines → extract helper functions
- Class exceeds 8 methods → split responsibilities
- Nesting exceeds 3 levels → extract early returns or functions

## Dashboard/Monitoring Structure (Future)

```
src/
└── dashboard/              # Self-contained dashboard subsystem
    ├── server/             # Backend server (FastAPI)
    │   ├── api.py          # REST API endpoints
    │   ├── websocket.py    # Real-time updates
    │   └── auth.py         # Authentication (basic)
    ├── client/             # Frontend (TBD: React/Vue)
    │   ├── components/     # UI components
    │   ├── services/       # API client
    │   └── stores/         # State management
    ├── shared/             # Shared types/utilities
    │   └── models.py       # Shared data models
    └── public/             # Static assets
```

### Separation of Concerns
- Dashboard is optional, isolated subsystem
- Own CLI entry point: `air-executor dashboard`
- Minimal dependencies on core (read-only access to storage)
- Can be disabled without affecting job execution

## Documentation Standards

- **All public APIs**: Docstrings in Google style format
- **Complex logic**: Inline comments explaining "why", not "what"
- **README files**: For each major subpackage (core, orchestrators, manager)
- **Type hints**: All function signatures and class attributes
- **Examples**: Usage examples in docstrings for non-trivial functions

### Docstring Template
```python
def spawn_runner(job: Job, config: Config) -> Runner:
    """
    Spawn a new task runner for the given job.

    Creates an ephemeral runner instance configured for the job's
    orchestrator backend (Airflow or Prefect).

    Args:
        job: Job instance requiring a task runner
        config: Configuration with orchestrator settings

    Returns:
        Runner instance ready to execute tasks

    Raises:
        RunnerSpawnError: If runner creation fails
        ConfigError: If orchestrator not configured

    Example:
        >>> job = Job(id="job-1", name="data-processing")
        >>> runner = spawn_runner(job, config)
        >>> runner.execute(job.tasks[0])
    """
    pass
```
