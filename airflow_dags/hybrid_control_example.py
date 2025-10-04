"""
Hybrid Control Flow: Airflow + Air-Executor

This DAG demonstrates how Airflow and Air-Executor share control:
- Airflow: Orchestration, scheduling, static tasks
- Air-Executor: Dynamic task discovery and execution
- Airflow: Post-processing after Air-Executor completes
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator
from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.standard.sensors.python import PythonSensor

sys.path.insert(0, "/home/rmondo/repos/air-executor")


def airflow_prepare_data(**context):
    """
    AIRFLOW CONTROLS: Preparation phase
    """
    print("🎯 [AIRFLOW] Preparing data for processing...")
    print("   - Validating inputs")
    print("   - Setting up workspace")
    print("   - Creating manifest")

    # Simulate prep work
    manifest = {
        "dataset": "customer_data_2025",
        "records": 10000,
        "format": "csv",
        "source": "s3://bucket/data/",
    }

    print(f"✅ [AIRFLOW] Preparation complete: {manifest}")
    context["task_instance"].xcom_push(key="manifest", value=manifest)


def handoff_to_air_executor(**context):
    """
    HAND OFF TO AIR-EXECUTOR: Create dynamic processing job
    """
    import re

    from scripts.example_python_usage import AirExecutorClient

    manifest = context["task_instance"].xcom_pull(task_ids="airflow_prepare", key="manifest")

    print("🤝 [HANDOFF] Airflow → Air-Executor")
    print(f"   Dataset: {manifest['dataset']}")
    print(f"   Records: {manifest['records']}")

    client = AirExecutorClient(base_path="/home/rmondo/repos/air-executor/.air-executor")

    # Create job with sanitized name
    run_id = context["dag_run"].run_id
    sanitized_run_id = re.sub(r"[^a-zA-Z0-9_-]", "_", run_id)
    job_name = f"hybrid-{sanitized_run_id}"

    # Initial job has ONE discovery task
    # This task will dynamically queue many more!
    client.create_job(
        job_name,
        [
            {
                "id": "discover-and-split",
                "command": "python",
                "args": [
                    "-c",
                    f"""
import json
from pathlib import Path
from datetime import datetime

job_name = '{job_name}'
tasks_file = Path(f'.air-executor/jobs/{{job_name}}/tasks.json')

print('🔍 [AIR-EXECUTOR] Discovering work...')
print('   Reading dataset: {manifest['dataset']}')

# Simulate discovering files/chunks to process
num_chunks = 10  # In reality, could be 100s or 1000s
print(f'   Found {{num_chunks}} chunks to process')

# Read existing tasks
with open(tasks_file, 'r') as f:
    tasks = json.load(f)

print(f'🔄 [AIR-EXECUTOR] Dynamically queuing {{num_chunks}} processing tasks...')

# Queue parallel processing tasks
chunk_ids = []
for i in range(num_chunks):
    task_id = f'process-chunk-{{i}}'
    chunk_ids.append(task_id)

    tasks.append({{
        'id': task_id,
        'job_name': job_name,
        'command': 'echo',
        'args': [f'Processing chunk {{i}}/{{num_chunks}}'],
        'dependencies': [],
        'status': 'pending',
        'created_at': datetime.utcnow().isoformat() + 'Z',
        'started_at': None,
        'completed_at': None,
        'error': None
    }})

# Queue merge task that depends on ALL chunks
tasks.append({{
    'id': 'merge-results',
    'job_name': job_name,
    'command': 'echo',
    'args': ['Merging results from all chunks'],
    'dependencies': chunk_ids,
    'status': 'pending',
    'created_at': datetime.utcnow().isoformat() + 'Z',
    'started_at': None,
    'completed_at': None,
    'error': None
}})

# Atomic write
temp = tasks_file.parent / f'.{{tasks_file.name}}.tmp'
with open(temp, 'w') as f:
    json.dump(tasks, f, indent=2)
temp.rename(tasks_file)

print(f'✅ [AIR-EXECUTOR] Queued {{num_chunks}} chunk tasks + 1 merge task')
print('   Air-Executor manager will execute them in parallel')
                """,
                ],
                "dependencies": [],
            }
        ],
    )

    print(f"✅ [HANDOFF] Air-Executor job created: {job_name}")
    print("   Air-Executor will:")
    print("   1. Discover chunks dynamically")
    print("   2. Queue N processing tasks")
    print("   3. Execute all in parallel")
    print("   4. Merge results")
    print("   5. Return control to Airflow")

    context["task_instance"].xcom_push(key="job_name", value=job_name)
    return job_name


def wait_for_air_executor(**context):
    """
    AIRFLOW WAITS: Monitor Air-Executor progress
    """
    job_name = context["task_instance"].xcom_pull(
        task_ids="handoff_to_air_executor", key="job_name"
    )

    state_file = Path(f"/home/rmondo/repos/air-executor/.air-executor/jobs/{job_name}/state.json")
    tasks_file = state_file.parent / "tasks.json"

    if not state_file.exists():
        print(f"⏳ [AIRFLOW] Waiting for Air-Executor to start job {job_name}...")
        return False

    with open(state_file) as f:
        state = json.load(f)

    with open(tasks_file) as f:
        tasks = json.load(f)

    total = len(tasks)
    completed = sum(1 for t in tasks if t["status"] == "completed")
    pending = sum(1 for t in tasks if t["status"] == "pending")

    print("⏳ [AIRFLOW] Air-Executor in control...")
    print(f"   Job state: {state['state']}")
    print(f"   Tasks: {completed}/{total} completed ({pending} pending)")
    print("   Air-Executor handling dynamic task execution...")

    return state["state"] in ["completed", "failed"]


def airflow_post_process(**context):
    """
    AIRFLOW TAKES CONTROL BACK: Post-processing
    """
    job_name = context["task_instance"].xcom_pull(
        task_ids="handoff_to_air_executor", key="job_name"
    )

    state_file = Path(f"/home/rmondo/repos/air-executor/.air-executor/jobs/{job_name}/state.json")
    tasks_file = state_file.parent / "tasks.json"

    with open(state_file) as f:
        state = json.load(f)

    with open(tasks_file) as f:
        tasks = json.load(f)

    print("🎯 [AIRFLOW] Control returned from Air-Executor")
    print(f"   Job: {job_name}")
    print(f"   Final state: {state['state']}")
    print(f"   Tasks completed: {sum(1 for t in tasks if t['status'] == 'completed')}/{len(tasks)}")
    print()
    print("✅ [AIRFLOW] Continuing with post-processing...")
    print("   - Validating results")
    print("   - Updating database")
    print("   - Sending notifications")

    if state["state"] == "failed":
        raise Exception(f"Air-Executor job {job_name} failed!")

    return {
        "job_name": job_name,
        "tasks_executed": len(tasks),
        "execution_time": "calculated_from_timestamps",
    }


# DAG Definition
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2025, 10, 2),
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}

with DAG(
    "hybrid_control_flow",
    default_args=default_args,
    description="Demo: Hybrid Airflow + Air-Executor control flow",
    schedule=None,
    catchup=False,
    tags=["hybrid", "air-executor", "dynamic"],
) as dag:
    # Phase 1: AIRFLOW CONTROLS
    prepare = PythonOperator(
        task_id="airflow_prepare",
        python_callable=airflow_prepare_data,
        doc_md="""
        ### Airflow Preparation Phase

        Airflow handles:
        - Data validation
        - Setup tasks
        - Static preparation work

        Then hands off to Air-Executor for dynamic processing.
        """,
    )

    # Phase 2: HAND OFF TO AIR-EXECUTOR
    handoff = PythonOperator(
        task_id="handoff_to_air_executor",
        python_callable=handoff_to_air_executor,
        doc_md="""
        ### Hand Off to Air-Executor

        Creates Air-Executor job with dynamic task discovery.

        Air-Executor will:
        1. Start with 1 discovery task
        2. Dynamically queue N tasks at runtime
        3. Execute all tasks (parallel where possible)
        4. Handle dependencies automatically
        5. Complete when no more tasks remain
        """,
    )

    # Phase 3: AIRFLOW WAITS (Air-Executor in control)
    wait = PythonSensor(
        task_id="wait_for_air_executor",
        python_callable=wait_for_air_executor,
        mode="poke",
        poke_interval=5,
        timeout=600,
        doc_md="""
        ### Airflow Waits

        Airflow monitors Air-Executor progress but doesn't control execution.

        Air-Executor is fully in control during this phase:
        - Discovering work
        - Queuing tasks dynamically
        - Executing in parallel
        - Managing dependencies

        Airflow just waits for completion.
        """,
    )

    # Phase 4: AIRFLOW TAKES CONTROL BACK
    post_process = PythonOperator(
        task_id="airflow_post_process",
        python_callable=airflow_post_process,
        doc_md="""
        ### Airflow Post-Processing

        Control returns to Airflow for:
        - Result validation
        - Database updates
        - Notifications
        - Cleanup
        - Next steps in DAG
        """,
    )

    # Optional: Continue with more Airflow tasks
    notify = BashOperator(
        task_id="airflow_notify",
        bash_command='echo "✅ [AIRFLOW] Pipeline complete! Sending notifications..."',
        doc_md="""
        ### Final Airflow Tasks

        Airflow continues with remaining orchestration:
        - Notifications
        - Reporting
        - Triggering downstream DAGs
        """,
    )

    # Define flow
    prepare >> handoff >> wait >> post_process >> notify
