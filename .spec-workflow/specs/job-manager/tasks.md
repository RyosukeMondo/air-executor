# Tasks Document: Job Manager MVP

## Task 1: Create Core Domain Models

- [x] 1. Create core domain models in src/air_executor/core/
  - Files: `src/air_executor/core/job.py`, `src/air_executor/core/task.py`
  - Define Job, JobState, Task, TaskStatus, TaskQueue classes with pydantic
  - Implement state transition methods and validation logic
  - Add serialization methods (from_file, to_file for Job)
  - Purpose: Establish type-safe domain models for job/task management
  - _Leverage: pydantic BaseModel, pathlib, datetime, Enum_
  - _Requirements: 1.1, 1.2, 1.3, 5.1, 5.2_
  - _Prompt: Implement the task for spec job-manager. First run spec-workflow-guide to get the workflow guide, then implement the task:

    Role: Python Domain Modeling Specialist with expertise in pydantic and type systems

    Task: Create comprehensive domain models for Job and Task entities following requirements 1.1-1.3, 5.1-5.2 from requirements.md. Implement Job class with state management (JobState enum: waiting, working, completed, failed), Task class with status tracking (TaskStatus enum: pending, running, completed, failed), and TaskQueue class for managing task collections. Include validation, state transition logic, dependency checking, and file serialization methods.

    Restrictions:
    - Must use pydantic BaseModel for all models
    - No external dependencies beyond pydantic, datetime, pathlib, typing
    - No orchestrator-specific logic (keep domain models pure)
    - Validate all state transitions (e.g., can't go from completed to waiting)
    - Validate job names (alphanumeric, dash, underscore only)

    _Leverage:
    - pydantic for validation and serialization
    - Enum for type-safe state/status values
    - pathlib for file operations
    - datetime for timestamps

    _Requirements Addressed:
    - 1.1: Job directory structure with state.json, tasks.json
    - 1.2: Atomic state updates in state.json
    - 1.3: Task queueing with unique IDs and pending status
    - 5.1: Task definition with command, args, dependencies
    - 5.2: Atomic task append with incrementing IDs

    Success Criteria:
    - All classes have complete type hints and validation
    - Job state transitions enforce valid state machine (waiting → working → completed/failed)
    - Task status transitions are validated and timestamped
    - TaskQueue supports dependency checking (is_ready method)
    - Serialization methods produce valid JSON matching data models spec
    - All validation errors produce clear, actionable messages

    Instructions:
    1. Edit tasks.md and change this task from [ ] to [-] (in progress)
    2. Create src/air_executor/core/ directory if not exists
    3. Create __init__.py with exports
    4. Implement job.py with Job, JobState classes
    5. Implement task.py with Task, TaskStatus, TaskQueue classes
    6. Write unit tests in tests/unit/test_job.py and tests/unit/test_task.py
    7. Run tests with pytest and ensure >90% coverage
    8. Edit tasks.md and change this task from [-] to [x] (completed)_

- [x] 2. Create File Storage Implementation

  - Files: `src/air_executor/storage/file_store.py`
  - Implement FileStore class with atomic JSON read/write operations
  - Add methods for job/task persistence (read_job_state, write_job_state, etc.)
  - Implement directory creation, job listing, and error handling
  - Purpose: Provide reliable file-based persistence with atomic writes
  - _Leverage: pathlib, json, tempfile for atomic writes_
  - _Requirements: 1.1, 1.2, 1.3, 1.4_
  - _Prompt: Implement the task for spec job-manager. First run spec-workflow-guide to get the workflow guide, then implement the task:

    Role: Backend Storage Engineer with expertise in file systems and atomic operations

    Task: Implement FileStore class following requirements 1.1-1.4 from requirements.md. Provide atomic JSON persistence for job state and task queues. Support read/write operations for .air-executor/jobs/{name}/state.json and tasks.json files with atomic write guarantees (write to temp file, then rename). Include directory creation, job listing, and robust error handling for corrupted files.

    Restrictions:
    - All writes must be atomic (write temp file, then os.rename)
    - Must handle partial writes and corrupted JSON gracefully
    - No database dependencies (pure file-based storage)
    - File permissions must be 0700 for job directories
    - Path traversal prevention (validate job names)

    _Leverage:
    - pathlib.Path for filesystem operations
    - json for serialization
    - tempfile.NamedTemporaryFile for atomic writes
    - os.rename() for atomic file replacement

    _Requirements Addressed:
    - 1.1: Create job directory with state.json, tasks.json, logs/
    - 1.2: Atomically update state.json on state changes
    - 1.3: Append tasks to tasks.json atomically
    - 1.4: Restore all job states from filesystem on restart

    Success Criteria:
    - All write operations are atomic (no partial writes possible)
    - Corrupted JSON files detected and logged without crashing
    - Directory creation is idempotent and creates full structure
    - Job listing handles missing/invalid directories gracefully
    - Unit tests verify atomic writes under concurrent access (mock scenarios)
    - File permissions enforced (0700 for job directories)

    Instructions:
    1. Edit tasks.md and change this task from [ ] to [-]
    2. Create src/air_executor/storage/ directory
    3. Create __init__.py with exports
    4. Implement file_store.py with FileStore class
    5. Write unit tests in tests/unit/test_file_store.py
    6. Test atomic writes, error handling, directory creation
    7. Run tests with pytest and ensure >85% coverage
    8. Edit tasks.md and change this task from [-] to [x]_

- [x] 3. Create Runner Interface and Subprocess Implementation

  - Files: `src/air_executor/core/runner.py`, `src/air_executor/runners/subprocess_runner.py`
  - Define Runner protocol with spawn, is_alive, terminate methods
  - Implement SubprocessRunner with process lifecycle management
  - Add timeout handling (SIGTERM → SIGKILL escalation)
  - Purpose: Provide abstraction for task execution with concrete subprocess implementation
  - _Leverage: typing.Protocol, subprocess, psutil, signal_
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
  - _Prompt: Implement the task for spec job-manager. First run spec-workflow-guide to get the workflow guide, then implement the task:

    Role: Systems Programmer with expertise in process management and Unix signals

    Task: Implement Runner protocol and SubprocessRunner class following requirements 4.1-4.5 from requirements.md. Define abstract Runner protocol for task execution abstraction. Implement concrete SubprocessRunner that spawns subprocess with command `air-executor run-task --job {job} --task {task}`, tracks PID, checks process liveness, and handles graceful/forceful termination with timeout escalation (SIGTERM → wait → SIGKILL).

    Restrictions:
    - Runner protocol must be implementation-agnostic (no subprocess details)
    - SubprocessRunner must handle zombie processes (wait/reap)
    - Must verify PID belongs to our spawned process (avoid killing wrong process)
    - Timeout enforcement required (SIGTERM after timeout, SIGKILL after grace period)
    - No shell=True in subprocess (security: prevent command injection)

    _Leverage:
    - typing.Protocol for interface definition
    - subprocess.Popen for process spawning
    - psutil for process existence and management
    - signal for SIGTERM/SIGKILL
    - time.sleep for timeout waiting

    _Requirements Addressed:
    - 4.1: Execute subprocess with air-executor run-task command
    - 4.2: Update job state to "working" on spawn
    - 4.3: Mark task completed on exit code 0
    - 4.4: Mark task failed on exit code >0
    - 4.5: Enforce timeout with SIGTERM → SIGKILL escalation

    Success Criteria:
    - Runner protocol defined with spawn, is_alive, terminate methods
    - SubprocessRunner spawns process and returns valid PID
    - is_alive correctly detects running vs exited processes
    - terminate sends SIGTERM, waits 10s, then SIGKILL if needed
    - Unit tests verify timeout handling with mock subprocess
    - Integration tests verify real subprocess lifecycle

    Instructions:
    1. Edit tasks.md and change this task from [ ] to [-]
    2. Create src/air_executor/core/runner.py with Runner protocol
    3. Create src/air_executor/runners/ directory
    4. Implement subprocess_runner.py with SubprocessRunner class
    5. Write unit tests in tests/unit/test_subprocess_runner.py
    6. Write integration tests in tests/integration/test_runner_lifecycle.py
    7. Run tests with pytest and ensure >80% coverage
    8. Edit tasks.md and change this task from [-] to [x]_

- [x] 4. Create Configuration Management

  - Files: `src/air_executor/manager/config.py`
  - Define Config class with pydantic validation
  - Implement from_file classmethod for YAML loading
  - Add default values and validation rules
  - Purpose: Provide validated, type-safe configuration management
  - _Leverage: pydantic BaseModel, pyyaml, pathlib_
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_
  - _Prompt: Implement the task for spec job-manager. First run spec-workflow-guide to get the workflow guide, then implement the task:

    Role: Configuration Management Specialist with expertise in validation and YAML parsing

    Task: Implement Config class following requirements 8.1-8.5 from requirements.md. Create pydantic model with fields: poll_interval (1-60s, default 5), task_timeout (60-7200s, default 1800), max_concurrent_runners (1-50, default 10), base_path (default .air-executor), log_level (default INFO), log_format (default json). Support loading from .air-executor/config.yaml with validation, defaults for missing values, and clear error messages for invalid config.

    Restrictions:
    - Must validate all numeric ranges (use pydantic Field with ge/le)
    - Must provide actionable error messages with line numbers for YAML errors
    - Must handle missing file gracefully (return defaults)
    - Must log warnings for unknown keys but not fail
    - No hot reload (restart required for config changes)

    _Leverage:
    - pydantic BaseModel with Field validators
    - pyyaml for YAML parsing (safe_load)
    - pathlib for file handling
    - pydantic ValidationError for detailed error messages

    _Requirements Addressed:
    - 8.1: Read from .air-executor/config.yaml, use defaults if missing
    - 8.2: Validate config and exit with error messages if invalid
    - 8.3: Restart required for config changes (no hot reload)
    - 8.4: Use documented defaults for missing optional values
    - 8.5: Log warnings for unknown keys, continue with valid ones

    Success Criteria:
    - Config loads from YAML file with all fields validated
    - Invalid values produce clear error messages (e.g., "poll_interval must be 1-60")
    - Missing file returns default Config without error
    - Unknown keys logged as warnings but don't prevent loading
    - Unit tests verify all validation rules and error messages

    Instructions:
    1. Edit tasks.md and change this task from [ ] to [-]
    2. Create src/air_executor/manager/ directory
    3. Create __init__.py with exports
    4. Implement config.py with Config class
    5. Write unit tests in tests/unit/test_config.py
    6. Test validation, defaults, error messages, unknown keys
    7. Run tests with pytest and ensure >90% coverage
    8. Edit tasks.md and change this task from [-] to [x]_

- [x] 5. Create Runner Spawner Component

  - Files: `src/air_executor/manager/spawner.py`
  - Implement RunnerSpawner class with PID tracking
  - Add spawn_if_needed method with parallel spawning (up to max_concurrent_runners)
  - Implement stale PID cleanup and active runner checking
  - Purpose: Manage runner lifecycle with concurrency control and PID tracking
  - _Leverage: Runner protocol, FileStore, concurrent.futures_
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2_
  - _Prompt: Implement the task for spec job-manager. First run spec-workflow-guide to get the workflow guide, then implement the task:

    Role: Concurrency Engineer with expertise in process orchestration and resource management

    Task: Implement RunnerSpawner class following requirements 3.1-3.5, 4.1-4.2 from requirements.md. Provide runner lifecycle management with PID tracking via .air-executor/jobs/{name}/runner.pid files. Implement spawn_if_needed method that spawns runners for multiple jobs in parallel (up to max_concurrent_runners limit). Enforce single-runner-per-job constraint by checking PID file existence and process liveness. Clean up stale PID files for dead processes.

    Restrictions:
    - Must enforce single runner per job (check PID file + process liveness)
    - Must clean up stale PIDs before allowing new spawn
    - Parallel spawning must respect max_concurrent_runners limit
    - PID file must be created BEFORE runner starts (prevent race condition)
    - Must handle runner spawn failures gracefully (log, clean up PID, continue)

    _Leverage:
    - Runner protocol for process operations
    - FileStore for PID file read/write
    - concurrent.futures.ThreadPoolExecutor for parallel spawning
    - psutil for process existence checking

    _Requirements Addressed:
    - 3.1: Check PID file existence before spawning
    - 3.2: Create PID file with process ID and timestamp before execution
    - 3.3: Remove PID file when runner terminates
    - 3.4: Clean up stale PID if process is dead
    - 3.5: Spawn runners in parallel (one per job, max 10 concurrent)
    - 4.1: Execute subprocess with air-executor run-task command
    - 4.2: Set job state to "working" when runner spawns

    Success Criteria:
    - spawn_if_needed correctly identifies jobs needing runners
    - PID files created atomically before runner starts
    - Stale PID cleanup handles crashed runners gracefully
    - Parallel spawning respects max_concurrent_runners limit
    - Runner spawn failures isolated (don't affect other jobs)
    - Unit tests with mocked Runner and FileStore verify logic
    - Integration tests verify real PID tracking and cleanup

    Instructions:
    1. Edit tasks.md and change this task from [ ] to [-]
    2. Create spawner.py in src/air_executor/manager/
    3. Implement RunnerSpawner class with all methods
    4. Write unit tests in tests/unit/test_spawner.py
    5. Write integration tests in tests/integration/test_spawner_lifecycle.py
    6. Run tests with pytest and ensure >80% coverage
    7. Edit tasks.md and change this task from [-] to [x]_

- [x] 6. Create Job Poller Component

  - Files: `src/air_executor/manager/poller.py`
  - Implement JobPoller class with polling loop
  - Add signal handling for graceful shutdown (SIGTERM)
  - Implement per-job error isolation and state management
  - Purpose: Provide main orchestration loop that discovers jobs and triggers spawning
  - _Leverage: FileStore, RunnerSpawner, signal, time, TaskQueue_
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 6.1, 6.2, 6.3_
  - _Prompt: Implement the task for spec job-manager. First run spec-workflow-guide to get the workflow guide, then implement the task:

    Role: Event Loop Architect with expertise in polling systems and signal handling

    Task: Implement JobPoller class following requirements 2.1-2.5, 6.1-6.3 from requirements.md. Create polling loop that runs every poll_interval seconds, scans .air-executor/jobs/ directory, loads job states, checks for pending tasks and active runners, and invokes RunnerSpawner for jobs that need work. Handle SIGTERM for graceful shutdown (complete current cycle, then exit within 10s). Isolate errors per job (log error, continue with other jobs).

    Restrictions:
    - Polling loop must not block longer than poll_interval
    - Must complete current poll cycle before shutdown (no interruption mid-cycle)
    - Job errors must not crash poller (isolation via try/except)
    - Must query all jobs within 100ms per job (performance requirement)
    - Must detect job completion (no pending tasks, no active runner → completed state)

    _Leverage:
    - FileStore for job discovery and state loading
    - RunnerSpawner for runner lifecycle
    - signal.signal for SIGTERM handling
    - time.sleep for poll interval
    - TaskQueue for pending task detection
    - structlog for structured logging

    _Requirements Addressed:
    - 2.1: Start polling loop with configurable interval (default 5s)
    - 2.2: Check status of all jobs within 100ms per job
    - 2.3: Add jobs with pending tasks and no active runner to spawn queue
    - 2.4: Log error for failed job, continue with remaining jobs
    - 2.5: Handle SIGTERM, complete current cycle, shutdown within 10s
    - 6.1: Detect no pending tasks and no active runner → set completed
    - 6.2: Detect failed task → set job to failed, stop spawning
    - 6.3: Log completion time and task statistics

    Success Criteria:
    - Polling loop runs continuously with correct interval
    - SIGTERM triggers graceful shutdown (completes cycle, exits <10s)
    - Job errors isolated and logged without crashing poller
    - Job completion detected and state updated correctly
    - Jobs with pending tasks and no runner added to spawn queue
    - Unit tests with mocked dependencies verify logic
    - Integration tests verify full poll cycle with real files

    Instructions:
    1. Edit tasks.md and change this task from [ ] to [-]
    2. Create poller.py in src/air_executor/manager/
    3. Implement JobPoller class with start, poll_once, stop methods
    4. Write unit tests in tests/unit/test_poller.py
    5. Write integration tests in tests/integration/test_poller_lifecycle.py
    6. Run tests with pytest and ensure >85% coverage
    7. Edit tasks.md and change this task from [-] to [x]_

- [x] 7. Create CLI Commands

  - Files: `src/air_executor/cli/main.py`, `src/air_executor/cli/commands.py`
  - Implement CLI using click framework
  - Add commands: start, stop, status, logs, reset
  - Use rich library for formatted table output
  - Purpose: Provide user-friendly command-line interface for job manager control
  - _Leverage: click, rich, FileStore, Job, Config_
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_
  - _Prompt: Implement the task for spec job-manager. First run spec-workflow-guide to get the workflow guide, then implement the task:

    Role: CLI Developer with expertise in click framework and terminal UI design

    Task: Implement CLI commands following requirements 7.1-7.5 from requirements.md. Create main.py as entry point with click group. Implement commands: start (spawn job manager daemon, output PID), stop (send SIGTERM to manager, wait for shutdown), status (display table of jobs with state/tasks/runner), logs (display task logs from jobs/{name}/logs/), reset (reset job to waiting state with confirmation). Use rich library for formatted, color-coded output.

    Restrictions:
    - start command must daemonize process (background execution)
    - stop command must handle missing PID gracefully
    - status command must work even if manager is stopped
    - logs command must support --tail option (default 50 lines)
    - reset command must require confirmation prompt

    _Leverage:
    - click for command parsing and options
    - rich.console and rich.table for formatted output
    - rich.syntax for log syntax highlighting
    - FileStore for job data access
    - subprocess for daemon spawning
    - os.kill for sending signals

    _Requirements Addressed:
    - 7.1: air-executor start → start manager daemon, output PID
    - 7.2: air-executor stop → send SIGTERM, wait for shutdown
    - 7.3: air-executor status → display job table (state, pending tasks, runner status)
    - 7.4: air-executor logs --job X → output task logs from jobs/X/logs/
    - 7.5: air-executor reset --job X → reset to waiting with confirmation

    Success Criteria:
    - All commands execute with correct exit codes (0 success, 1 error)
    - start command spawns background process and outputs PID
    - stop command gracefully terminates manager
    - status command displays formatted table with color-coded states
    - logs command displays task logs with syntax highlighting
    - reset command requires confirmation and updates job state
    - Unit tests verify command logic with mocked dependencies
    - E2E tests verify full CLI workflow

    Instructions:
    1. Edit tasks.md and change this task from [ ] to [-]
    2. Create src/air_executor/cli/ directory
    3. Create __init__.py with exports
    4. Implement main.py with click group and command entry point
    5. Implement commands.py with all command implementations
    6. Write unit tests in tests/unit/test_cli.py
    7. Write E2E tests in tests/e2e/test_cli_workflow.py
    8. Run tests with pytest and ensure >75% coverage
    9. Edit tasks.md and change this task from [-] to [x]_

- [x] 8. Create Package Structure and Entry Points

  - Files: `setup.py`, `pyproject.toml`, `requirements.txt`, `Makefile`
  - Set up Python package with entry points for CLI
  - Define dependencies (pydantic, click, rich, pyyaml, psutil, structlog)
  - Create Makefile for common tasks (install, test, run)
  - Purpose: Enable package installation and distribution
  - _Leverage: setuptools, pip-tools_
  - _Requirements: All (packaging and distribution)_
  - _Prompt: Implement the task for spec job-manager. First run spec-workflow-guide to get the workflow guide, then implement the task:

    Role: Python Packaging Engineer with expertise in setuptools and dependency management

    Task: Create Python package structure for air-executor. Implement setup.py with package metadata, dependencies, and console_scripts entry point for air-executor CLI. Create pyproject.toml with project configuration (black, isort, mypy settings). Generate requirements.txt with pinned dependencies. Create Makefile with targets: install, test, lint, format, run. Ensure package is pip-installable.

    Restrictions:
    - Must use src/ layout (importable as air_executor package)
    - Entry point must be air-executor = air_executor.cli.main:cli
    - requirements.txt must pin exact versions for reproducibility
    - Makefile must work on Linux/macOS (use POSIX commands)
    - Must include dev dependencies (pytest, black, mypy, ruff)

    _Leverage:
    - setuptools for package definition
    - pip-tools for requirements management
    - make for task automation
    - pyproject.toml for tool configuration

    _Requirements Addressed:
    - All requirements (enables entire system to be installed and run)
    - Dependency management for all required libraries
    - CLI entry point for user-friendly execution

    Success Criteria:
    - Package is pip-installable with pip install -e .
    - air-executor command is available after installation
    - make install sets up virtual environment and installs package
    - make test runs pytest with coverage
    - make lint runs ruff and mypy
    - make format runs black and isort
    - All dependencies are pinned in requirements.txt

    Instructions:
    1. Edit tasks.md and change this task from [ ] to [-]
    2. Create setup.py with package metadata and dependencies
    3. Create pyproject.toml with tool configurations
    4. Create requirements.txt with pinned dependencies
    5. Create requirements-dev.txt with dev dependencies
    6. Create Makefile with all targets
    7. Test installation with pip install -e .
    8. Verify air-executor command works
    9. Edit tasks.md and change this task from [-] to [x]_

- [x] 9. Write Integration Tests

  - Files: `tests/integration/test_manager_e2e.py`, `tests/integration/test_state_persistence.py`
  - Write end-to-end test for full manager lifecycle
  - Test state persistence and recovery after restart
  - Test multi-job concurrent execution
  - Purpose: Verify system works correctly as integrated whole
  - _Leverage: pytest, tmpdir fixture, real subprocess execution_
  - _Requirements: All (integration validation)_
  - _Prompt: Implement the task for spec job-manager. First run spec-workflow-guide to get the workflow guide, then implement the task:

    Role: QA Engineer with expertise in integration testing and system verification

    Task: Write comprehensive integration tests covering full job manager lifecycle. Test scenarios: 1) Full cycle (start manager → spawn runner → execute task → complete job → stop manager), 2) State persistence (create job → stop manager → restart → verify state restored), 3) Multi-job execution (multiple jobs with tasks → verify parallel runner spawning), 4) Error recovery (corrupted state file → verify graceful handling). Use real filesystem (tmpdir) and real subprocess execution.

    Restrictions:
    - Must use temporary directories (pytest tmpdir fixture)
    - Must verify file contents directly (state.json, tasks.json, PID files)
    - Must verify process lifecycle (PID exists, process terminates)
    - Must test both success and failure scenarios
    - Tests must be isolated (no shared state between tests)

    _Leverage:
    - pytest fixtures for setup/teardown
    - tmpdir fixture for temporary filesystem
    - subprocess for process execution
    - psutil for process verification
    - time.sleep for polling simulation

    _Requirements Addressed:
    - All requirements (integration testing validates entire system)
    - Verify state persistence across restarts
    - Verify concurrent runner spawning
    - Verify error handling and recovery

    Success Criteria:
    - E2E test verifies full manager lifecycle from start to completion
    - State persistence test verifies restart recovery
    - Multi-job test verifies parallel spawning (up to max_concurrent_runners)
    - Error recovery test verifies graceful handling of corrupted files
    - All tests pass consistently (no flaky tests)
    - Test coverage includes all critical paths

    Instructions:
    1. Edit tasks.md and change this task from [ ] to [-]
    2. Create tests/integration/ directory
    3. Create __init__.py
    4. Implement test_manager_e2e.py with full lifecycle test
    5. Implement test_state_persistence.py with restart recovery test
    6. Implement test_multi_job.py with concurrent execution test
    7. Run tests with pytest -v tests/integration/
    8. Verify all tests pass
    9. Edit tasks.md and change this task from [-] to [x]_

- [x] 10. Write Documentation and Examples

  - Files: `README.md`, `docs/quickstart.md`, `examples/simple_job.json`
  - Write README with project overview, installation, and quick start
  - Create quickstart guide with step-by-step tutorial
  - Add example job definitions for common use cases
  - Purpose: Enable users to understand and use the system
  - _Leverage: markdown, example configs_
  - _Requirements: All (documentation)_
  - _Prompt: Implement the task for spec job-manager. First run spec-workflow-guide to get the workflow guide, then implement the task:

    Role: Technical Writer with expertise in developer documentation and tutorials

    Task: Create comprehensive user documentation. Write README.md with project overview, features, installation instructions (pip install), quick start example, and links to detailed docs. Create docs/quickstart.md with step-by-step tutorial: 1) Install, 2) Create job definition, 3) Start manager, 4) Check status, 5) View logs, 6) Stop manager. Add examples/simple_job.json with annotated job definition. Ensure documentation matches actual implementation and CLI commands.

    Restrictions:
    - README must be concise (<500 lines), not exhaustive
    - Quick start must be copy-paste executable
    - Examples must be valid and tested
    - Documentation must match actual CLI command syntax
    - Must include troubleshooting section for common issues

    _Leverage:
    - Markdown for formatting
    - Code blocks with syntax highlighting
    - Mermaid diagrams for architecture visualization
    - Example job definitions in JSON

    _Requirements Addressed:
    - All requirements (documentation enables usage)
    - User understanding of system architecture
    - Clear instructions for common operations

    Success Criteria:
    - README includes project overview, features, installation, quick start
    - Quick start guide is executable and produces expected results
    - Example job definitions are valid and well-commented
    - Troubleshooting section covers common issues (stale PIDs, config errors)
    - Documentation is clear and actionable for new users
    - All CLI commands are accurately documented

    Instructions:
    1. Edit tasks.md and change this task from [ ] to [-]
    2. Create README.md in project root
    3. Create docs/quickstart.md
    4. Create examples/simple_job.json with comments
    5. Create examples/dynamic_tasks.json showing sub-task queueing
    6. Review documentation for accuracy against implementation
    7. Test quick start guide by following steps
    8. Edit tasks.md and change this task from [-] to [x]_
