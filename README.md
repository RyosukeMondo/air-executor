# Air Executor

A lightweight, flexible job execution system for Python that enables asynchronous task management with subprocess isolation.

## Features

- **Asynchronous Job Execution**: Run jobs as isolated subprocesses
- **Job Management**: Create, monitor, and control job lifecycle
- **Task Organization**: Group related tasks into jobs with dependencies
- **Storage Backend**: Persistent job state with file-based storage
- **CLI Interface**: Easy-to-use command-line interface
- **Airflow Integration**: Compatible with Apache Airflow workflows

## 📖 Documentation

**Complete documentation available in [docs/](./docs/)**

- **[Getting Started](./docs/getting-started/)** - Installation, quick start, configuration
- **[User Guides](./docs/guides/)** - Airflow integration, Claude SDK, DAG development
- **[Reference](./docs/reference/)** - Configuration, troubleshooting, patterns
- **[Architecture](./docs/architecture/)** - System design and architecture decisions

## Installation

### Quick Install

```bash
# Clone the repository
git clone https://github.com/RyosukeMondo/air-executor.git
cd air-executor

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
pip install -e .

# Install development dependencies
pip install -r requirements-dev.txt
```

## Quick Start

### Using Python API

```python
from air_executor import Job, Task, SubprocessRunner

# Create a job
job = Job(name="data_processing")

# Add tasks
job.add_task(Task(
    name="fetch_data",
    command=["python", "scripts/fetch_data.py"]
))

job.add_task(Task(
    name="process_data",
    command=["python", "scripts/process_data.py"],
    depends_on=["fetch_data"]
))

# Execute the job
runner = SubprocessRunner()
runner.run_job(job)
```

### Using CLI

```bash
# Start the job manager
python scripts/run_manager.py

# Create a job from JSON
air-executor create examples/simple_job.json

# Check job status
air-executor status <job_id>

# List all jobs
air-executor list
```

## Project Structure

```
air-executor/
├── src/air_executor/       # Main package source code
│   ├── core/              # Core job and task models
│   ├── manager/           # Job execution management
│   ├── runners/           # Execution backends
│   ├── storage/           # Persistence layer
│   └── cli/               # Command-line interface
├── tests/                 # Test suite
│   ├── unit/             # Unit tests
│   └── integration/      # Integration tests
├── scripts/              # Utility scripts and examples
├── examples/             # Example configurations
├── claudedocs/           # Documentation and analysis
├── docs/                 # Additional documentation
└── apps/                 # Application entry points

```

## Development

### Setup Development Environment

```bash
# Run setup script
bash scripts/setup-dev.sh

# Or manually:
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=air_executor --cov-report=html

# Run specific test file
pytest tests/unit/test_job.py
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint
flake8 src/ tests/

# Type checking
mypy src/
```

## Documentation

- [Why Air Executor](claudedocs/WHY_AIR_EXECUTOR.md)
- [Python Usage Guide](claudedocs/PYTHON_USAGE_GUIDE.md)
- [Airflow Integration](claudedocs/AIRFLOW_INTEGRATION.md)
- [Implementation Details](claudedocs/IMPLEMENTATION_COMPLETE.md)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details

## Author

RyosukeMondo
