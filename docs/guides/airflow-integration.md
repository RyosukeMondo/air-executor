# Airflow Integration Guide

Complete guide for integrating Air Executor with Apache Airflow.

## Overview

Air Executor provides seamless integration with Apache Airflow for orchestrating Claude AI tasks and autonomous code fixing workflows.

## Setup

### 1. Install Airflow

```bash
pip install apache-airflow==2.10.4
airflow db init
```

### 2. Configure Airflow

```bash
# Set Airflow home (optional)
export AIRFLOW_HOME=~/airflow

# Create admin user
airflow users create \
    --username admin \
    --password admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com
```

### 3. Sync DAGs

```bash
# Sync Air Executor DAGs to Airflow
./scripts/sync_dags_to_airflow.sh
```

## Available DAGs

### Claude Query DAG (`claude_query_sdk`)

Execute Claude AI queries via Airflow.

**Parameters:**
- `prompt`: Query to send to Claude (default: "hello, how old are you?")
- `working_directory`: Working directory for execution

**Trigger via CLI:**
```bash
airflow dags trigger claude_query_sdk \
  --conf '{"prompt": "Explain Python async/await"}'
```

**Trigger via UI:**
1. Navigate to DAGs page
2. Click "Trigger DAG" on `claude_query_sdk`
3. Add JSON configuration
4. Click "Trigger"

### Python Cleanup DAG (`python_cleanup_dag`)

Automated Python code cleanup and linting.

**Trigger:**
```bash
airflow dags trigger python_cleanup_dag \
  --conf '{"working_directory": "/path/to/project"}'
```

### Commit and Push DAG (`commit_and_push_dag`)

Automated git commit and push workflow.

**Trigger:**
```bash
airflow dags trigger commit_and_push_dag \
  --conf '{"message": "feat: add new feature"}'
```

## DAG Development

See [DAG Development Guide](./dag-development.md) for creating custom DAGs.

## Monitoring

### View DAG Runs
```bash
airflow dags list-runs -d claude_query_sdk
```

### Check Task Logs
```bash
airflow tasks logs claude_query_sdk run_claude_query_sdk <date>
```

### Web UI
```bash
# Start web server
airflow webserver -p 8080

# Access UI
open http://localhost:8080
```

## Troubleshooting

### DAGs Not Appearing
- Verify DAG directory: `airflow config get-value core dags_folder`
- Sync DAGs: `./scripts/sync_dags_to_airflow.sh`
- Restart Airflow: `airflow webserver` and `airflow scheduler`

### Permission Errors
- Check file permissions in DAG folder
- Verify Airflow user has read access

### Task Failures
- Check task logs in Airflow UI
- Verify Claude authentication: `claude --version`
- Check wrapper path in configuration

For more help, see [Troubleshooting Guide](../reference/troubleshooting.md).
