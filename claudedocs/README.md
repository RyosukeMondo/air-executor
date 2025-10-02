# Air-Executor

> Autonomous job management system with ephemeral task runners

Air-Executor orchestrates complex workflows through ephemeral, single-task runners that spawn on-demand, execute work, and terminate cleanly. Perfect for dynamic task graphs where subtasks emerge at runtime.

## Features

- **Ephemeral Task Runners**: Spawn runners on-demand, execute single task, terminate automatically
- **Single-Runner-Per-Job**: Enforce sequential execution, prevent race conditions
- **Dynamic Task Queuing**: Tasks can queue additional subtasks during execution
- **Polling-Based Monitoring**: Simple, reliable job state polling (configurable interval)
- **File-Based State**: No external dependencies, easy debugging, simple deployment
- **CLI Management**: Start, stop, status, logs - all from command line

## Architecture

```
┌─────────────────────────────────────────┐
│          Job Manager (Poller)           │
│  • Polls job directories every 5s       │
│  • Detects pending tasks                │
│  • Spawns runners when needed           │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│       Runner Spawner (PID Tracking)     │
│  • Enforces single-runner-per-job       │
│  • Manages PID files                    │
│  • Parallel spawning (up to max limit)  │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│    Ephemeral Task Runners (Subprocess)  │
│  • Execute single task                  │
│  • Update task status                   │
│  • Terminate after completion           │
└─────────────────────────────────────────┘
```

## Installation

### From PyPI (when published)

```bash
pip install air-executor
```

### From Source

```bash
git clone https://github.com/yourusername/air-executor.git
cd air-executor
pip install -e .
```

### Development Installation

```bash
pip install -e ".[dev]"
```

## Quick Start

### 1. Create Job Directory

```bash
# Air-Executor will create this structure automatically when needed
# .air-executor/
# └── jobs/
#     └── my-job/
#         ├── state.json      # Job state
#         ├── tasks.json      # Task queue
#         └── logs/           # Task execution logs
```

### 2. Start Job Manager

```bash
air-executor start
# Job manager started (PID 12345)
```

### 3. Check Status

```bash
air-executor status
# ┏━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┓
# ┃ Job Name  ┃ State    ┃ Pending Tasks ┃ Active Runner ┃ Updated At         ┃
# ┡━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━┩
# │ my-job    │ working  │             3 │       ✓       │ 2025-10-02 10:30:15│
# └───────────┴──────────┴───────────────┴───────────────┴────────────────────┘
```

### 4. View Logs

```bash
air-executor logs --job my-job
# Logs for job my-job:
#
# --- task-001.log ---
# Running task task-001...
# Task task-001 completed successfully
```

### 5. Stop Manager

```bash
air-executor stop
# Stopping job manager (PID 12345)...
# Job manager stopped
```

## Configuration

Create `.air-executor/config.yaml` to customize settings:

```yaml
# Polling interval in seconds (1-60)
poll_interval: 5

# Task timeout in seconds (60-7200)
task_timeout: 1800

# Maximum concurrent runner spawns (1-50)
max_concurrent_runners: 10

# Base directory for storage
base_path: .air-executor

# Logging settings
log_level: INFO
log_format: json
```

## Usage Examples

### Example: Simple Job with Sequential Tasks

```python
from air_executor.core.job import Job, JobState
from air_executor.core.task import Task, TaskQueue
from air_executor.storage.file_store import FileStore
import uuid

# Initialize storage
store = FileStore()

# Create job
job = Job(
    id=str(uuid.uuid4()),
    name="data-processing",
    state=JobState.WAITING
)
store.create_job_dir("data-processing")
store.write_job_state(job)

# Add tasks
queue = TaskQueue("data-processing", store.jobs_path / "data-processing" / "tasks.json")

task1 = Task(
    id="fetch-data",
    job_name="data-processing",
    command="curl",
    args=["-o", "data.json", "https://api.example.com/data"]
)

task2 = Task(
    id="process-data",
    job_name="data-processing",
    command="python",
    args=["process.py", "data.json"],
    dependencies=["fetch-data"]
)

queue.add(task1)
queue.add(task2)

# Job manager will automatically execute tasks in order
```

### Example: Dynamic Task Generation

Tasks can queue additional subtasks during execution:

```python
# In your task script
from air_executor.core.task import Task, TaskQueue
from air_executor.storage.file_store import FileStore

# Your task logic discovers 10 files to process
files = ["file1.txt", "file2.txt", ..., "file10.txt"]

# Queue a subtask for each file
store = FileStore()
queue = TaskQueue("my-job", store.jobs_path / "my-job" / "tasks.json")

for i, file in enumerate(files):
    subtask = Task(
        id=f"process-{i}",
        job_name="my-job",
        command="python",
        args=["process_file.py", file]
    )
    queue.add(subtask)

# Job manager will automatically spawn runners for new subtasks
```

## CLI Commands

### `air-executor start`
Start job manager in background. Spawns daemon process that polls for jobs.

Options:
- `--config PATH`: Path to custom config file

### `air-executor stop`
Stop job manager gracefully. Sends SIGTERM and waits for clean shutdown.

### `air-executor status`
Display status table for all jobs.

Options:
- `--job NAME`: Filter by specific job name

### `air-executor logs`
Display task execution logs.

Options:
- `--job NAME` (required): Job name
- `--tail N`: Number of lines to display (default: 50)

### `air-executor reset`
Reset job to waiting state (clears failed status).

Options:
- `--job NAME` (required): Job name

## Development

### Run Tests

```bash
make test
```

### Lint and Format

```bash
make lint    # Check code quality
make format  # Auto-format code
```

### Build Package

```bash
pip install build
python -m build
```

## Troubleshooting

### Stale PID Files

If a runner crashes, a stale PID file may remain:

```bash
# Job manager automatically cleans up stale PIDs on next poll
# Or manually remove:
rm .air-executor/jobs/my-job/runner.pid
```

### Job Stuck in Working State

If a job is stuck "working" with no active runner:

```bash
# Check for active runner
air-executor status --job my-job

# If no runner but state is "working", reset:
air-executor reset --job my-job
```

### Configuration Errors

If config file is invalid:

```bash
# Check config syntax
cat .air-executor/config.yaml

# Validate with Python
python -c "import yaml; yaml.safe_load(open('.air-executor/config.yaml'))"

# Remove to use defaults
mv .air-executor/config.yaml .air-executor/config.yaml.bak
```

## Architecture Decisions

### Why File-Based Storage?

- **Simplicity**: No database setup, no external dependencies
- **Debugging**: Inspect state with `cat state.json`
- **Portability**: Works anywhere Python runs
- **Durability**: Atomic writes prevent corruption

### Why Polling vs Events?

- **Simplicity**: No message broker, no webhooks, no callbacks
- **Reliability**: Works with any task execution backend
- **Predictability**: Fixed interval, no thundering herd
- **Debuggability**: Easy to reason about timing

### Why Single-Runner-Per-Job?

- **Simplicity**: No coordination needed between runners
- **Correctness**: Sequential execution prevents race conditions
- **Resource Control**: Bounded parallelism at job level
- **Clear Semantics**: One task at a time, easy to reason about

## Roadmap

- [ ] Web dashboard for job monitoring
- [ ] Airflow DAG integration
- [ ] Prefect flow integration
- [ ] Retry policies and exponential backoff
- [ ] Task priority and scheduling
- [ ] Distributed job management (multi-instance)
- [ ] WebSocket real-time updates
- [ ] Task execution metrics and analytics

## Contributing

Contributions welcome! Please:

1. Fork repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## License

MIT License - see LICENSE file for details

## Acknowledgments

Built with:
- [Pydantic](https://docs.pydantic.dev/) - Data validation
- [Click](https://click.palletsprojects.com/) - CLI framework
- [Rich](https://rich.readthedocs.io/) - Terminal formatting
- [psutil](https://psutil.readthedocs.io/) - Process management
