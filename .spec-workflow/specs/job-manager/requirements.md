# Requirements Document: Job Manager MVP

## Introduction

The Job Manager is the core orchestration component of Air-Executor that monitors job states and spawns ephemeral task runners on demand. This MVP implementation provides the foundational job management capabilities including polling-based status monitoring, single-runner-per-job enforcement, and dynamic task queuing support.

## Alignment with Product Vision

This feature directly implements the core product principles outlined in product.md:

- **Ephemeral Over Persistent**: Task runners are spawned on-demand and terminate after single-task completion
- **Single Responsibility**: One active runner per job prevents coordination complexity and race conditions
- **Progressive Disclosure**: Support for dynamic task queuing allows workflows to discover sub-tasks at runtime
- **Infrastructure Agnostic**: Abstract runner interface supports both Airflow and Prefect implementations

## Requirements

### Requirement 1: Job State Management

**User Story:** As a workflow operator, I want jobs to persist their state across restarts, so that I can resume interrupted workflows without data loss.

#### Acceptance Criteria

1. WHEN a job is created THEN the system SHALL create a job directory at `.air-executor/jobs/{job-name}/` with `state.json`, `tasks.json`, and `logs/` subdirectory
2. WHEN job state changes THEN the system SHALL atomically update `state.json` with new status (waiting, working, completed, failed)
3. WHEN tasks are queued THEN the system SHALL append task definitions to `tasks.json` with unique task IDs and pending status
4. WHEN job manager restarts THEN the system SHALL restore all job states from filesystem and resume monitoring
5. IF state file is corrupted THEN the system SHALL log error and mark job as failed without data loss to other jobs

### Requirement 2: Polling-Based Job Monitoring

**User Story:** As a workflow operator, I want the job manager to automatically check job status at regular intervals, so that task runners are spawned promptly when work is available.

#### Acceptance Criteria

1. WHEN job manager starts THEN the system SHALL begin polling loop with configurable interval (default 5 seconds, range 1-60 seconds)
2. WHEN polling cycle executes THEN the system SHALL check status of all jobs in `.air-executor/jobs/` directory within 100ms per job
3. WHEN job has pending tasks AND no active runner THEN the system SHALL add job to spawn queue
4. WHEN polling encounters error for a job THEN the system SHALL log error, skip that job, and continue with remaining jobs
5. WHEN job manager receives SIGTERM THEN the system SHALL complete current polling cycle and gracefully shutdown within 10 seconds

### Requirement 3: Single-Runner-Per-Job Enforcement

**User Story:** As a workflow operator, I want only one task runner active per job at any time, so that tasks execute sequentially without race conditions.

#### Acceptance Criteria

1. WHEN checking if runner should spawn THEN the system SHALL verify no runner PID file exists in `.air-executor/jobs/{job-name}/runner.pid`
2. WHEN spawning runner THEN the system SHALL create PID file with runner process ID and timestamp before starting execution
3. WHEN runner terminates THEN the system SHALL remove PID file to allow next runner to spawn
4. IF PID file exists but process is dead THEN the system SHALL clean up stale PID file and allow new runner spawn
5. WHEN multiple jobs need runners THEN the system SHALL spawn runners in parallel (one per job, max 10 concurrent)

### Requirement 4: Task Runner Lifecycle Management

**User Story:** As a workflow operator, I want task runners to spawn automatically, execute a single task, and terminate cleanly, so that resources are efficiently utilized.

#### Acceptance Criteria

1. WHEN spawning task runner THEN the system SHALL execute subprocess with command `air-executor run-task --job {job-name} --task {task-id}`
2. WHEN runner spawns THEN the system SHALL set job state to "working" and update state.json atomically
3. WHEN runner terminates with exit code 0 THEN the system SHALL mark task as completed in tasks.json and remove PID file
4. WHEN runner terminates with exit code >0 THEN the system SHALL mark task as failed, log error, and remove PID file
5. WHEN runner exceeds timeout (default 30 minutes) THEN the system SHALL send SIGTERM, wait 10 seconds, then SIGKILL if needed

### Requirement 5: Dynamic Task Queue Management

**User Story:** As a workflow developer, I want task runners to queue additional tasks during execution, so that workflows can adapt based on runtime conditions.

#### Acceptance Criteria

1. WHEN runner queues new task THEN the system SHALL append task to `tasks.json` with atomically incrementing task ID
2. WHEN task is queued THEN the system SHALL include task definition (command, args, dependencies) and set status to "pending"
3. WHEN next polling cycle runs THEN the system SHALL detect new pending tasks and spawn runner if none active
4. WHEN task has dependencies THEN the system SHALL only mark as pending after all dependency tasks are completed
5. IF tasks.json write fails THEN the system SHALL retry up to 3 times with exponential backoff before failing task

### Requirement 6: Job Completion Detection

**User Story:** As a workflow operator, I want jobs to automatically transition to completed state when all tasks finish, so that I can track workflow outcomes.

#### Acceptance Criteria

1. WHEN polling detects no pending tasks AND no active runner THEN the system SHALL set job state to "completed"
2. WHEN any task is marked as failed THEN the system SHALL set job state to "failed" and stop spawning new runners
3. WHEN job reaches completed state THEN the system SHALL log completion time and task statistics (total, succeeded, failed)
4. WHEN job is completed or failed THEN the system SHALL continue monitoring but skip spawning logic until job is reset
5. IF all tasks are completed but job state is not updated THEN the system SHALL auto-correct state on next poll cycle

### Requirement 7: CLI Interface for Job Management

**User Story:** As a workflow operator, I want CLI commands to start, stop, and monitor the job manager, so that I can control the system without writing code.

#### Acceptance Criteria

1. WHEN executing `air-executor start` THEN the system SHALL start job manager in background with daemon mode and output PID
2. WHEN executing `air-executor stop` THEN the system SHALL send SIGTERM to job manager process and wait for graceful shutdown
3. WHEN executing `air-executor status` THEN the system SHALL display table of all jobs with state, pending tasks, and active runner status
4. WHEN executing `air-executor logs --job {name}` THEN the system SHALL output task execution logs from `.air-executor/jobs/{name}/logs/`
5. WHEN executing `air-executor reset --job {name}` THEN the system SHALL reset job to waiting state and clear failed status (with confirmation prompt)

### Requirement 8: Configuration Management

**User Story:** As a workflow operator, I want to configure polling interval, timeouts, and resource limits via config file, so that I can tune system behavior for my environment.

#### Acceptance Criteria

1. WHEN job manager starts THEN the system SHALL read configuration from `.air-executor/config.yaml` if exists, else use defaults
2. WHEN config file is invalid THEN the system SHALL log validation errors with line numbers and exit with code 1
3. WHEN config changes THEN the system SHALL require restart to apply (no hot reload in MVP)
4. WHEN config is missing optional values THEN the system SHALL use documented defaults (poll_interval: 5, task_timeout: 1800, max_runners: 10)
5. WHEN config contains unknown keys THEN the system SHALL log warnings but continue with valid keys

## Non-Functional Requirements

### Code Architecture and Modularity
- **Single Responsibility**: Separate modules for polling (`poller.py`), spawning (`spawner.py`), state (`job.py`, `task.py`), and storage (`file_store.py`)
- **Modular Design**: Core domain models have no dependencies on CLI or orchestrator implementations
- **Dependency Management**: Storage and runner interfaces allow swapping implementations without changing manager logic
- **Clear Interfaces**: `Runner` protocol defines contract for task execution, enabling Airflow/Prefect implementations

### Performance
- Job status query: <100ms per job (target 50-100 jobs)
- Polling cycle: Complete within poll_interval (5 seconds default)
- Runner spawn time: <10 seconds from detection to process start
- Memory footprint: <100MB for job manager process
- Concurrent runner spawns: Support up to 10 simultaneous spawns

### Reliability
- Graceful degradation: Single job errors do not crash manager
- State consistency: Atomic file writes prevent partial state corruption
- Process resilience: Stale PID cleanup handles crashed runners
- Restart recovery: Full state restoration from filesystem on startup
- Error logging: All errors logged with structured context for debugging

### Security
- File permissions: Job directories use 0700 (owner-only access)
- PID validation: Process existence checked before trusting PID files
- Command injection: Task commands validated and sanitized before subprocess execution
- Path traversal: Job names validated against allowed characters (alphanumeric, dash, underscore)
- Resource limits: Task timeout enforced to prevent runaway processes

### Usability
- Clear error messages: Actionable error messages with suggested fixes
- CLI output formatting: Tabular output with color-coded status indicators
- Progress visibility: Real-time status updates via `status` command
- Log accessibility: Easy access to task logs via `logs` command
- Configuration validation: Config errors reported with line numbers
