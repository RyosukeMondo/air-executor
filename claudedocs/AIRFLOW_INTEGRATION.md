# Airflow Integration Guide for Air-Executor

## 🎯 Integration Strategy

Air-Executor can integrate with Apache Airflow in **two ways**:

### Option 1: Air-Executor as Airflow Backend (Recommended)
Use Airflow's rich UI while Air-Executor handles execution

### Option 2: Airflow DAG that Submits to Air-Executor
Keep both systems independent, use Airflow to orchestrate Air-Executor jobs

---

## 🚀 Option 1: Using Airflow UI with Air-Executor Backend

This approach gives you Airflow's beautiful dashboard while using Air-Executor's ephemeral runner architecture.

### Architecture

```
┌─────────────────────┐
│   Airflow Web UI    │  ← Users interact here
│   (Dashboard)       │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  Airflow Scheduler  │  ← Converts DAGs to tasks
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  Custom Executor    │  ← Air-Executor integration layer
│  (AirExecutor)      │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│   Air-Executor      │  ← Your existing job manager
│   Job Manager       │
└─────────────────────┘
```

### Implementation Steps

#### 1. Create Custom Airflow Executor

```python
# airflow_executor.py
"""
Custom Airflow Executor that uses Air-Executor as backend
"""

from typing import Any, Optional, Tuple
from airflow.executors.base_executor import BaseExecutor
from airflow.models.taskinstance import TaskInstanceKey
import json
from pathlib import Path
from datetime import datetime


class AirExecutorExecutor(BaseExecutor):
    """
    Airflow executor that delegates to Air-Executor
    """

    def __init__(self):
        super().__init__()
        self.air_executor_base = Path(".air-executor")
        self.jobs_path = self.air_executor_base / "jobs"

    def start(self):
        """Start the executor"""
        self.log.info("Starting AirExecutor executor")

    def execute_async(
        self,
        key: TaskInstanceKey,
        command: str,
        queue: Optional[str] = None,
        executor_config: Optional[Any] = None,
    ):
        """
        Execute task asynchronously by creating Air-Executor job

        Args:
            key: Airflow task instance key
            command: Command to execute (typically airflow task run ...)
            queue: Queue name (unused)
            executor_config: Executor-specific config
        """
        self.log.info(f"Executing task {key} via Air-Executor")

        # Create Air-Executor job for this task
        job_name = f"airflow-{key.dag_id}-{key.task_id}-{key.run_id}"
        job_id = self._create_air_executor_job(job_name, command)

        # Track this task
        self.running[key] = command

    def _create_air_executor_job(self, job_name: str, command: str) -> str:
        """Create Air-Executor job from Airflow task"""
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

        # Parse command into shell task
        tasks = [{
            "id": "airflow-task",
            "job_name": job_name,
            "command": "bash",
            "args": ["-c", command],
            "dependencies": [],
            "status": "pending",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "started_at": None,
            "completed_at": None,
            "error": None
        }]

        with open(job_dir / "tasks.json", "w") as f:
            json.dump(tasks, f, indent=2)

        self.log.info(f"Created Air-Executor job: {job_name}")
        return job_id

    def sync(self):
        """Sync task states between Air-Executor and Airflow"""
        self.log.debug("Syncing task states")

        # Check status of running tasks
        for key, command in list(self.running.items()):
            job_name = f"airflow-{key.dag_id}-{key.task_id}-{key.run_id}"
            state = self._get_air_executor_job_state(job_name)

            if state == "completed":
                self.success(key)
                del self.running[key]
            elif state == "failed":
                self.fail(key)
                del self.running[key]
            # If still "working" or "waiting", keep polling

    def _get_air_executor_job_state(self, job_name: str) -> str:
        """Get current state of Air-Executor job"""
        state_file = self.jobs_path / job_name / "state.json"

        if not state_file.exists():
            return "unknown"

        with open(state_file) as f:
            state = json.load(f)

        return state.get("state", "unknown")

    def end(self):
        """Shutdown executor"""
        self.log.info("Shutting down AirExecutor executor")

    def terminate(self):
        """Terminate executor"""
        self.end()
```

#### 2. Configure Airflow to Use Custom Executor

```python
# airflow.cfg or environment variables
[core]
executor = airflow_executor.AirExecutorExecutor

[air_executor]
base_path = /path/to/air-executor
```

#### 3. Create DAGs as Normal

```python
# dags/example_dag.py
from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'example_air_executor_dag',
    default_args=default_args,
    description='Example DAG using Air-Executor',
    schedule_interval=timedelta(days=1),
    catchup=False,
) as dag:

    t1 = BashOperator(
        task_id='print_date',
        bash_command='date',
    )

    t2 = BashOperator(
        task_id='sleep',
        bash_command='sleep 5',
    )

    t3 = BashOperator(
        task_id='print_hello',
        bash_command='echo "Hello from Air-Executor!"',
    )

    t1 >> [t2, t3]  # t2 and t3 run in parallel after t1
```

#### 4. Start Both Services

```bash
# Terminal 1: Start Air-Executor
./start-dev.sh

# Terminal 2: Start Airflow webserver
airflow webserver --port 8080

# Terminal 3: Start Airflow scheduler
airflow scheduler
```

Now you can:
- ✅ View DAGs in Airflow UI (http://localhost:8080)
- ✅ See task execution in Airflow dashboard
- ✅ Tasks actually run via Air-Executor ephemeral runners
- ✅ Monitor both in Airflow UI and `./status.sh`

---

## 🎨 Option 2: Airflow Orchestrating Air-Executor Jobs

Simpler approach: Use Airflow to submit jobs to Air-Executor as an external system.

### Implementation

```python
# dags/air_executor_jobs.py
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.sensors.python import PythonSensor
from datetime import datetime, timedelta
import json
from pathlib import Path


def create_air_executor_job(**context):
    """Create Air-Executor job"""
    from example_python_usage import AirExecutorClient

    client = AirExecutorClient()
    job_id = client.create_job(
        job_name=context['dag_run'].run_id,
        tasks=[
            {"command": "echo", "args": ["Task 1"], "dependencies": []},
            {"command": "sleep", "args": ["2"], "dependencies": []},
            {"command": "echo", "args": ["Task 2"], "dependencies": []},
        ]
    )

    # Store job_id for monitoring
    context['task_instance'].xcom_push(key='job_id', value=job_id)
    return job_id


def check_job_complete(**context):
    """Check if Air-Executor job completed"""
    job_name = context['dag_run'].run_id
    state_file = Path(f".air-executor/jobs/{job_name}/state.json")

    if not state_file.exists():
        return False

    with open(state_file) as f:
        state = json.load(f)

    return state['state'] in ['completed', 'failed']


def get_job_result(**context):
    """Get Air-Executor job result"""
    job_name = context['dag_run'].run_id
    state_file = Path(f".air-executor/jobs/{job_name}/state.json")

    with open(state_file) as f:
        state = json.load(f)

    if state['state'] == 'failed':
        raise Exception(f"Air-Executor job {job_name} failed")

    print(f"Job {job_name} completed successfully!")
    return state


default_args = {
    'owner': 'airflow',
    'start_date': datetime(2025, 1, 1),
}

with DAG(
    'air_executor_pipeline',
    default_args=default_args,
    description='Submit and monitor Air-Executor jobs',
    schedule_interval=timedelta(days=1),
    catchup=False,
) as dag:

    # Create job
    create_job = PythonOperator(
        task_id='create_air_executor_job',
        python_callable=create_air_executor_job,
    )

    # Wait for completion
    wait_for_job = PythonSensor(
        task_id='wait_for_completion',
        python_callable=check_job_complete,
        mode='poke',
        poke_interval=5,  # Check every 5 seconds
        timeout=600,  # 10 minute timeout
    )

    # Get result
    get_result = PythonOperator(
        task_id='get_job_result',
        python_callable=get_job_result,
    )

    create_job >> wait_for_job >> get_result
```

---

## 📊 What You Get with Airflow UI

Once integrated, Airflow provides:

### 1. **DAG Visualization**
- Graph view showing task dependencies
- Tree view showing historical runs
- Gantt chart for execution timeline

### 2. **Task Monitoring**
- Real-time task status (running, success, failed)
- Task logs accessible from UI
- Task duration and performance metrics

### 3. **Scheduling**
- Cron-based scheduling
- Backfilling for historical runs
- Pause/unpause DAGs

### 4. **Alerting**
- Email notifications on failure
- Slack/PagerDuty integrations
- Custom callbacks

### 5. **Variables & Connections**
- Centralized configuration management
- Secret storage
- Database connections

---

## 🏗️ Quick Start: Minimal Airflow + Air-Executor Setup

```bash
# 1. Install Airflow
pip install apache-airflow

# 2. Initialize Airflow DB
airflow db init

# 3. Create admin user
airflow users create \
    --username admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com \
    --password admin

# 4. Copy the custom executor
cp airflow_executor.py ~/airflow/plugins/

# 5. Start Air-Executor
./start-dev.sh

# 6. Start Airflow (separate terminals)
airflow webserver --port 8080
airflow scheduler

# 7. Open browser
# http://localhost:8080
# Login: admin / admin
```

---

## 🎯 Comparison: Which Approach?

| Feature | Option 1: Custom Executor | Option 2: Job Submission |
|---------|---------------------------|--------------------------|
| **Complexity** | High | Low |
| **Airflow Integration** | Deep | Shallow |
| **UI Features** | Full Airflow UI | Full Airflow UI |
| **Maintenance** | Custom code | Standard Airflow |
| **Best For** | Production deployment | Quick integration |

### Recommendation

**Start with Option 2** (Job Submission):
- ✅ Easier to implement
- ✅ Less coupling
- ✅ Faster to get working
- ✅ Still get full Airflow UI benefits

**Move to Option 1** (Custom Executor) when:
- You need deeper integration
- You want Airflow to fully control Air-Executor
- You're ready for production deployment

---

## 📝 Next Steps

1. **Try Option 2 first**: Create a simple DAG that submits jobs
2. **Install Airflow**: `pip install apache-airflow`
3. **Test Integration**: Run a test DAG
4. **Monitor Both**: Use Airflow UI + `./status.sh`
5. **Iterate**: Add more complex workflows

The beauty of this approach: **You keep Air-Executor's simplicity** while gaining **Airflow's rich UI and scheduling**! 🎉
