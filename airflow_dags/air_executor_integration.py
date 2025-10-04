"""
Airflow DAG that creates and monitors Air-Executor jobs.

This DAG demonstrates how Air-Executor jobs appear in Airflow UI:
- Create job via PythonOperator
- Monitor progress via PythonSensor
- Display results in Airflow UI
"""

import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add Air-Executor to Python path
sys.path.insert(0, "/home/rmondo/repos/air-executor")

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.standard.sensors.python import PythonSensor

from airflow_dags.autonomous_fixing.domain.exceptions import JobFailedError
from scripts.example_python_usage import AirExecutorClient


def create_air_executor_job(**context):
    """
    Create Air-Executor job and push job_name to XCom.
    This appears in Airflow logs.
    """
    client = AirExecutorClient(base_path="/home/rmondo/repos/air-executor/.air-executor")

    # Create unique job name based on DAG run (sanitize for valid characters)
    # Replace colons, plus signs, and dots with dashes or underscores
    run_id = context["dag_run"].run_id
    sanitized_run_id = re.sub(r"[^a-zA-Z0-9_-]", "_", run_id)
    job_name = f"airflow-{sanitized_run_id}"

    print(f"✅ Creating Air-Executor job: {job_name}")
    print(f"   Original DAG run ID: {run_id}")

    # Define tasks for Air-Executor
    tasks = [
        {
            "id": "greet",
            "command": "echo",
            "args": [f"Hello from Airflow DAG run: {context['dag_run'].run_id}"],
            "dependencies": [],
        },
        {"id": "process", "command": "sleep", "args": ["3"], "dependencies": ["greet"]},
        {
            "id": "complete",
            "command": "echo",
            "args": ["Air-Executor job completed successfully!"],
            "dependencies": ["process"],
        },
    ]

    job_id = client.create_job(job_name, tasks)

    print(f"✅ Job created with ID: {job_id}")
    print("📊 Monitor with: ./status.sh")
    print(f"📁 Job directory: .air-executor/jobs/{job_name}/")

    # Push to XCom for next task
    context["task_instance"].xcom_push(key="job_name", value=job_name)
    context["task_instance"].xcom_push(key="job_id", value=job_id)

    return job_name


def check_job_status(**context):
    """
    Check Air-Executor job status.
    Sensor will keep polling until this returns True.
    """
    job_name = context["task_instance"].xcom_pull(
        task_ids="create_air_executor_job", key="job_name"
    )

    state_file = Path(f"/home/rmondo/repos/air-executor/.air-executor/jobs/{job_name}/state.json")

    if not state_file.exists():
        print(f"⏳ Waiting for job {job_name} to be picked up by Air-Executor manager...")
        return False

    with open(state_file) as f:
        state = json.load(f)

    current_state = state["state"]
    print(f"📊 Job {job_name} state: {current_state}")

    # Also show task progress
    tasks_file = state_file.parent / "tasks.json"
    if tasks_file.exists():
        with open(tasks_file) as f:
            tasks = json.load(f)

        completed = sum(1 for t in tasks if t["status"] == "completed")
        total = len(tasks)
        print(f"   Tasks: {completed}/{total} completed")

    return current_state in ["completed", "failed"]


def get_job_result(**context):
    """
    Get final Air-Executor job result and display in Airflow logs.
    """
    job_name = context["task_instance"].xcom_pull(
        task_ids="create_air_executor_job", key="job_name"
    )

    state_file = Path(f"/home/rmondo/repos/air-executor/.air-executor/jobs/{job_name}/state.json")
    tasks_file = state_file.parent / "tasks.json"

    with open(state_file) as f:
        state = json.load(f)

    with open(tasks_file) as f:
        tasks = json.load(f)

    print("\n" + "=" * 60)
    print("🎉 Air-Executor Job Results")
    print("=" * 60)
    print(f"Job Name: {job_name}")
    print(f"Final State: {state['state']}")
    print(f"Created: {state['created_at']}")
    print(f"Updated: {state['updated_at']}")
    print()
    print("Task Execution Details:")
    print("-" * 60)

    for task in tasks:
        status_icon = "✅" if task["status"] == "completed" else "❌"
        print(f"{status_icon} {task['id']}: {task['status']}")
        print(f"   Command: {task['command']} {' '.join(task['args'])}")
        if task["started_at"]:
            print(f"   Started: {task['started_at']}")
        if task["completed_at"]:
            print(f"   Completed: {task['completed_at']}")
        print()

    print("=" * 60)

    if state["state"] == "failed":
        raise JobFailedError(job_name)

    return {
        "job_name": job_name,
        "state": state["state"],
        "tasks_completed": sum(1 for t in tasks if t["status"] == "completed"),
        "total_tasks": len(tasks),
    }


# DAG definition
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2025, 10, 2),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}

with DAG(
    "air_executor_demo",
    default_args=default_args,
    description="Demo: Airflow orchestrating Air-Executor jobs",
    schedule=None,  # Manual trigger only (changed from schedule_interval in Airflow 3.x)
    catchup=False,
    tags=["air-executor", "demo", "integration"],
) as dag:
    # Task 1: Create Air-Executor job
    create_job = PythonOperator(
        task_id="create_air_executor_job",
        python_callable=create_air_executor_job,
        doc_md="""
        ### Create Air-Executor Job

        This task creates a new Air-Executor job with 3 tasks:
        1. Greet - Echo hello message
        2. Process - Sleep for 3 seconds
        3. Complete - Echo completion message

        The job is created in `.air-executor/jobs/` directory.
        """,
    )

    # Task 2: Wait for Air-Executor job completion
    wait_for_job = PythonSensor(
        task_id="wait_for_air_executor_completion",
        python_callable=check_job_status,
        mode="poke",
        poke_interval=2,  # Check every 2 seconds
        timeout=300,  # 5 minute timeout
        doc_md="""
        ### Monitor Air-Executor Job

        This sensor polls the Air-Executor job status every 2 seconds.
        It will wait until the job state is 'completed' or 'failed'.

        You can see live progress in the logs!
        """,
    )

    # Task 3: Get and display results
    get_results = PythonOperator(
        task_id="get_air_executor_results",
        python_callable=get_job_result,
        doc_md="""
        ### Display Results

        This task fetches the final Air-Executor job results
        and displays them in Airflow logs.

        Click "Log" to see detailed task execution information.
        """,
    )

    # Define task dependencies
    create_job >> wait_for_job >> get_results
