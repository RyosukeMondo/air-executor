# Air-Executor Python Usage Guide

## 📦 What is Air-Executor?

**Air-Executor** is a lightweight job orchestration system with ephemeral task runners. Think of it as a mini-Airflow/Prefect that runs locally with file-based state management.

### Key Features:
- ✅ **Ephemeral Runners**: Each task runs in its own subprocess
- ✅ **Dependency Management**: Tasks wait for dependencies before executing
- ✅ **File-based State**: No database needed, just JSON files
- ✅ **Parallel Execution**: Independent tasks run concurrently
- ✅ **Simple Integration**: Easy to use from Python code

## 🐍 Using from Python

### Basic Usage

```python
from pathlib import Path
import json
from datetime import datetime

class AirExecutorClient:
    def __init__(self, base_path: str = ".air-executor"):
        self.base_path = Path(base_path)
        self.jobs_path = self.base_path / "jobs"

    def create_job(self, job_name: str, tasks: list) -> str:
        """Create a new job with tasks"""
        job_id = f"{job_name}-{int(datetime.now().timestamp())}"
        job_dir = self.jobs_path / job_name
        job_dir.mkdir(parents=True, exist_ok=True)
        (job_dir / "logs").mkdir(exist_ok=True)

        # State file
        state = {
            "id": job_id,
            "name": job_name,
            "state": "waiting",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z"
        }
        with open(job_dir / "state.json", "w") as f:
            json.dump(state, f, indent=2)

        # Tasks file
        task_objects = []
        for i, task in enumerate(tasks, 1):
            task_objects.append({
                "id": task.get("id", f"task-{i}"),
                "job_name": job_name,
                "command": task["command"],
                "args": task.get("args", []),
                "dependencies": task.get("dependencies", []),
                "status": "pending",
                "created_at": datetime.utcnow().isoformat() + "Z",
                "started_at": None,
                "completed_at": None,
                "error": None
            })

        with open(job_dir / "tasks.json", "w") as f:
            json.dump(task_objects, f, indent=2)

        return job_id

# Usage
client = AirExecutorClient()
client.create_job("my-job", [
    {"command": "echo", "args": ["Hello"], "dependencies": []},
    {"command": "sleep", "args": ["2"], "dependencies": []},
])
```

## 💡 Common Use Cases

### 1. Data Pipeline

```python
client.create_job("etl-pipeline", [
    {
        "id": "extract",
        "command": "python",
        "args": ["scripts/extract.py"],
        "dependencies": []
    },
    {
        "id": "transform",
        "command": "python",
        "args": ["scripts/transform.py"],
        "dependencies": ["extract"]
    },
    {
        "id": "load",
        "command": "python",
        "args": ["scripts/load.py"],
        "dependencies": ["transform"]
    }
])
```

### 2. Parallel Processing

```python
client.create_job("parallel-processing", [
    {
        "id": "prepare",
        "command": "python",
        "args": ["prepare_data.py"],
        "dependencies": []
    },
    {
        "id": "process-1",
        "command": "python",
        "args": ["process.py", "--shard", "1"],
        "dependencies": ["prepare"]
    },
    {
        "id": "process-2",
        "command": "python",
        "args": ["process.py", "--shard", "2"],
        "dependencies": ["prepare"]
    },
    {
        "id": "process-3",
        "command": "python",
        "args": ["process.py", "--shard", "3"],
        "dependencies": ["prepare"]
    },
    {
        "id": "merge",
        "command": "python",
        "args": ["merge_results.py"],
        "dependencies": ["process-1", "process-2", "process-3"]
    }
])
```

### 3. Shell Commands

```python
client.create_job("deployment", [
    {
        "id": "build",
        "command": "docker",
        "args": ["build", "-t", "myapp", "."],
        "dependencies": []
    },
    {
        "id": "test",
        "command": "docker",
        "args": ["run", "myapp", "pytest"],
        "dependencies": ["build"]
    },
    {
        "id": "push",
        "command": "docker",
        "args": ["push", "myapp:latest"],
        "dependencies": ["test"]
    }
])
```

### 4. With Python Scripts (Inline)

```python
client.create_job("inline-python", [
    {
        "id": "analyze",
        "command": "python",
        "args": ["-c", """
import pandas as pd
import sys

df = pd.read_csv('data.csv')
summary = df.describe()
summary.to_csv('summary.csv')
print('Analysis complete!')
"""],
        "dependencies": []
    }
])
```

## 🔄 Integration with pexpect

For interactive commands that need input/output handling:

```python
# Create wrapper script that uses pexpect
wrapper = """#!/usr/bin/env python3
import pexpect

child = pexpect.spawn('your-interactive-command')
child.expect('Password:')
child.sendline('secret')
child.expect(pexpect.EOF)
"""

# Save wrapper script
Path("wrapper.py").write_text(wrapper)
Path("wrapper.py").chmod(0o755)

# Create job that runs it
client.create_job("interactive-job", [
    {
        "command": "python",
        "args": ["wrapper.py"],
        "dependencies": []
    }
])
```

## 📊 Monitoring Jobs

```python
def get_job_status(job_name: str) -> dict:
    """Get current status of a job"""
    state_file = Path(f".air-executor/jobs/{job_name}/state.json")
    tasks_file = Path(f".air-executor/jobs/{job_name}/tasks.json")

    with open(state_file) as f:
        state = json.load(f)

    with open(tasks_file) as f:
        tasks = json.load(f)

    return {
        "job_name": job_name,
        "state": state["state"],
        "total_tasks": len(tasks),
        "completed": sum(1 for t in tasks if t["status"] == "completed"),
        "failed": sum(1 for t in tasks if t["status"] == "failed"),
        "pending": sum(1 for t in tasks if t["status"] == "pending"),
    }

# Usage
status = get_job_status("my-job")
print(f"Job {status['job_name']}: {status['completed']}/{status['total_tasks']} completed")
```

## 🚀 Advanced Patterns

### Dynamic Task Generation

```python
# Generate tasks programmatically
shards = 10
tasks = [{"id": "prepare", "command": "echo", "args": ["Preparing"], "dependencies": []}]

# Add parallel processing tasks
for i in range(shards):
    tasks.append({
        "id": f"shard-{i}",
        "command": "python",
        "args": ["process.py", f"--shard={i}"],
        "dependencies": ["prepare"]
    })

# Add merge task that depends on all shards
tasks.append({
    "id": "merge",
    "command": "python",
    "args": ["merge.py"],
    "dependencies": [f"shard-{i}" for i in range(shards)]
})

client.create_job("dynamic-job", tasks)
```

### Error Handling

```python
# Check for failures
status = get_job_status("my-job")
if status["failed"] > 0:
    # Retry logic
    client.create_job("my-job-retry", failed_tasks)
```

## 🛠️ Helper Scripts Available

- `./create_job.sh <name>` - Create simple test job
- `./status.sh` - Check all jobs status
- `./start-dev.sh` - Start job manager
- `./stop-dev.sh` - Stop job manager gracefully
- `example_python_usage.py` - Python client examples

## 📝 Full Example Script

See `example_python_usage.py` for a complete working example that demonstrates:
- Sequential pipelines
- Parallel processing
- Python script execution
- Status monitoring

## 🔗 Comparison with Other Tools

| Feature | Air-Executor | Airflow | Prefect |
|---------|--------------|---------|---------|
| Setup | Drop files | Database + webserver | Database + webserver |
| State | File-based | Database | Database |
| UI | CLI/scripts | Web UI | Web UI |
| Scale | Single machine | Distributed | Distributed |
| Use case | Simple workflows | Production DAGs | Production flows |

**Use Air-Executor when:**
- You need simple local task orchestration
- You don't want database/webserver overhead
- You're prototyping workflows
- You need file-based state for version control

**Use Airflow/Prefect when:**
- You need production-scale orchestration
- You want web UI monitoring
- You need distributed execution
- You have complex scheduling requirements
