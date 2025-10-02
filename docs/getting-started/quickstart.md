# Quick Start Guide

Get up and running with Air Executor in 5 minutes.

## 1. Installation

```bash
git clone https://github.com/RyosukeMondo/air-executor.git
cd air-executor
python -m venv .venv
source .venv/bin/activate
pip install -e .
npm install -g @anthropic-ai/claude-code
claude login
```

## 2. Basic Usage

### Execute a Simple Task

```bash
# Run a Python script
python scripts/claude_wrapper.py
```

### Create Your First Job

```python
from air_executor import JobManager

# Create job manager
manager = JobManager()

# Create and run a job
job = manager.create_job("my_first_job")
job.add_task("echo 'Hello Air Executor!'")
job.run()
```

## 3. Airflow Integration

```bash
# Start Airflow
airflow webserver -p 8080
airflow scheduler

# Sync DAGs
./scripts/sync_dags_to_airflow.sh

# Open Airflow UI
open http://localhost:8080
```

## 4. Claude AI Integration

```bash
# Run Claude query
python airflow_dags/claude_query_sdk.py

# Or via Airflow DAG
airflow dags trigger claude_query_sdk
```

## 5. Autonomous Code Fixing

```bash
# Activate environment
source ~/.venv/air-executor/bin/activate

# Run autonomous fixing
python airflow_dags/autonomous_fixing/fix_orchestrator.py \
  config/autonomous_fix.yaml \
  --max-iterations=5
```

## Next Steps

- **Airflow Integration**: See [Airflow Integration Guide](../guides/airflow-integration.md)
- **Claude SDK**: See [Claude SDK Usage Guide](../guides/claude-sdk-usage.md)
- **DAG Development**: See [DAG Development Guide](../guides/dag-development.md)
- **Configuration**: See [Configuration Guide](./configuration.md)

## Common Tasks

### View Airflow DAGs
```bash
airflow dags list
```

### Trigger a DAG
```bash
airflow dags trigger claude_query_sdk
```

### Monitor Jobs
```bash
airflow dags list-runs -d claude_query_sdk
```

### Check Logs
```bash
airflow tasks logs claude_query_sdk run_claude_query_sdk <execution_date>
```

## Troubleshooting

- **Claude not authenticated**: Run `claude login`
- **Airflow not found**: Ensure `pip install apache-airflow`
- **Permission denied**: Check file permissions and virtual environment

For more help, see [Troubleshooting Guide](../reference/troubleshooting.md).
