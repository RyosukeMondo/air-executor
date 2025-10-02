# ✅ Airflow is Running!

## 🎉 Access Information

**Web UI:** http://localhost:8080

**Login Credentials:**
- **Username:** `admin`
- **Password:** `rBUUEXuhQxwAvHpw`

(Password saved in: `~/airflow/simple_auth_manager_passwords.json.generated`)

---

## 📊 What You'll See

Once you log in, you'll get access to Airflow's beautiful dashboard:

### 1. **DAGs View** (Main Page)
- List of all DAGs (Directed Acyclic Graphs)
- Status indicators (running, success, failed)
- Quick actions (trigger, pause, delete)

### 2. **Graph View**
- Visual representation of task dependencies
- Click any DAG → "Graph" tab
- See task flow with color-coded status

### 3. **Calendar View**
- Historical run status
- See patterns over time

### 4. **Task Instance Details**
- Click any task to see logs
- View duration, retry attempts
- Access task configuration

---

## 🚀 Quick Start: Create Your First DAG

### Option 1: Using the Example DAGs

Airflow comes with 61+ example DAGs already loaded! Try these:

1. Go to http://localhost:8080
2. Log in with credentials above
3. You'll see DAGs like:
   - `example_bash_operator`
   - `example_python_operator`
   - `tutorial`
   - `latest_only`

4. Click the "Play" button (▶️) next to any DAG to trigger it
5. Click the DAG name → "Graph" to see execution flow
6. Watch tasks turn green as they complete!

### Option 2: Create Air-Executor Integration DAG

Create a DAG that uses Air-Executor:

```bash
# Create dags directory
mkdir -p ~/airflow/dags

# Copy our integration example
cp AIRFLOW_INTEGRATION.md ~/airflow/dags/
```

Then create: `~/airflow/dags/air_executor_dag.py`

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.sensors.python import PythonSensor
from datetime import datetime, timedelta
import sys
import json
from pathlib import Path

# Add Air-Executor to path
sys.path.insert(0, '/home/rmondo/repos/air-executor')

def create_air_executor_job(**context):
    """Create Air-Executor job"""
    from example_python_usage import AirExecutorClient

    client = AirExecutorClient(base_path='/home/rmondo/repos/air-executor/.air-executor')
    job_name = f"airflow-job-{context['dag_run'].run_id}"

    client.create_job(job_name, [
        {
            "id": "task1",
            "command": "echo",
            "args": ["Hello from Airflow + Air-Executor!"],
            "dependencies": []
        },
        {
            "id": "task2",
            "command": "sleep",
            "args": ["2"],
            "dependencies": ["task1"]
        },
        {
            "id": "task3",
            "command": "echo",
            "args": ["Job completed!"],
            "dependencies": ["task2"]
        }
    ])

    context['task_instance'].xcom_push(key='job_name', value=job_name)
    return job_name

def check_job_complete(**context):
    """Check if Air-Executor job completed"""
    job_name = context['task_instance'].xcom_pull(
        task_ids='create_job',
        key='job_name'
    )

    state_file = Path(f"/home/rmondo/repos/air-executor/.air-executor/jobs/{job_name}/state.json")

    if not state_file.exists():
        return False

    with open(state_file) as f:
        state = json.load(f)

    return state['state'] in ['completed', 'failed']

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2025, 10, 2),
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

with DAG(
    'air_executor_demo',
    default_args=default_args,
    description='Demo of Airflow + Air-Executor integration',
    schedule_interval=None,  # Manual trigger only
    catchup=False,
    tags=['air-executor', 'demo'],
) as dag:

    create_job = PythonOperator(
        task_id='create_job',
        python_callable=create_air_executor_job,
    )

    wait_for_job = PythonSensor(
        task_id='wait_for_completion',
        python_callable=check_job_complete,
        mode='poke',
        poke_interval=5,
        timeout=300,
    )

    create_job >> wait_for_job
```

Wait ~30 seconds, then refresh the Airflow UI - you'll see `air_executor_demo` DAG!

---

## 🎨 UI Features to Explore

### Graph View
- **Visual Task Flow**: See task dependencies as a graph
- **Real-time Status**: Watch tasks change color as they execute
- **Click Tasks**: View logs, duration, retry history

### Grid View
- **Historical Runs**: See past executions in a grid
- **Run Comparison**: Compare execution times across runs

### Calendar View
- **Monthly Overview**: See success/failure patterns
- **Date-based Navigation**: Jump to specific run dates

### Code View
- **View Source**: See the DAG source code directly in UI
- **Syntax Highlighting**: Python code with colors

### Task Logs
- **Streaming Logs**: See live task output
- **Download Logs**: Save logs for debugging
- **Log Level Filtering**: Filter by INFO, WARNING, ERROR

---

## 🛑 Stopping Airflow

When you're done:

```bash
# Find the airflow process
ps aux | grep airflow

# Kill it (or just Ctrl+C in the terminal where it's running)
pkill -f "airflow standalone"
```

Or just close the terminal where `airflow standalone` is running.

---

## 🔄 Starting Airflow Again

Next time, just run:

```bash
cd /home/rmondo/repos/air-executor
source venv/bin/activate
airflow standalone &
```

Then go to http://localhost:8080 with same credentials!

---

## 💡 Tips & Tricks

### 1. **Testing DAGs**
```bash
# Test a specific task without running the whole DAG
airflow tasks test air_executor_demo create_job 2025-10-02
```

### 2. **Viewing Logs**
```bash
# See scheduler logs
tail -f ~/airflow/logs/scheduler/latest/*.log
```

### 3. **Database Location**
```bash
# SQLite database at:
~/airflow/airflow.db

# View with:
sqlite3 ~/airflow/airflow.db
```

### 4. **Configuration**
```bash
# Edit config:
nano ~/airflow/airflow.cfg

# Common changes:
# - Change port: webserver.port
# - Increase workers: core.parallelism
# - Change timezone: core.default_timezone
```

### 5. **Clear Task History**
In the UI:
- Click DAG → Clear → Select runs → Confirm

---

## 🌟 Next Steps

1. **Explore Example DAGs**: Learn from the 61 built-in examples
2. **Create Custom DAG**: Build your own workflow
3. **Integrate Air-Executor**: Use the example above
4. **Add Scheduling**: Change `schedule_interval` to cron expression
5. **Set Up Alerts**: Configure email notifications in `airflow.cfg`

---

## 📚 Resources

- **Airflow Docs**: https://airflow.apache.org/docs/
- **Tutorial**: Go to DAG "tutorial" in the UI
- **Concepts**: https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/index.html

---

## 🆘 Troubleshooting

**UI Not Loading?**
```bash
# Check if running
curl localhost:8080

# Check logs
tail -f ~/airflow/logs/scheduler/latest/*.log
```

**Can't Log In?**
```bash
# Get password again
cat ~/airflow/simple_auth_manager_passwords.json.generated
```

**DAG Not Appearing?**
- Wait 30-60 seconds (DAG processor scans every 30s)
- Check file is in `~/airflow/dags/`
- Check for syntax errors in DAG file
- Look in Admin → Logs → DAG Processing

**Port 8080 Already Used?**
```bash
# Kill whatever is using it
lsof -ti:8080 | xargs kill -9

# Or change port in airflow.cfg
```

Enjoy your Airflow UI! 🎉
