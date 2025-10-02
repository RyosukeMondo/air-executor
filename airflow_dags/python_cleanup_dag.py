"""
Airflow DAG for cleaning up Python-generated artifacts from repositories.

This DAG:
- Reuses run_claude_query_sdk function (SSOT, SRP)
- Uses a pre-defined prompt for stable Python cleanup
- Parameterizable working directory
"""

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from datetime import datetime, timedelta

# Import the reusable function (SSOT - Single Source of Truth)
# Note: claude_query_sdk.py must be in the same dags folder
import sys
from pathlib import Path

# Ensure dags folder is in path for imports
sys.path.insert(0, str(Path(__file__).parent))

from claude_query_sdk import run_claude_query_sdk


# Pre-defined cleanup prompt for stable, repeatable execution
PYTHON_CLEANUP_PROMPT = """Find and clean up Python-generated artifacts that shouldn't be tracked by the repository:

1. Find all __pycache__ directories, .pyc, .pyo files
2. Find other Python artifacts (.egg-info, .pytest_cache, .coverage, .tox, etc.)
3. Remove all found artifacts from the working directory
4. Verify nothing is tracked in git
5. Report what was cleaned up

Do not commit or push - just clean the working directory."""


def cleanup_python_artifacts(**context):
    """
    Wrapper function that calls run_claude_query_sdk with cleanup prompt.

    This follows SRP (Single Responsibility Principle):
    - This function: Provides domain-specific configuration
    - run_claude_query_sdk: Handles Claude SDK execution

    Allows working_directory override via dag_run.conf.
    """
    # Merge default prompt with any user-provided config
    dag_run_conf = context.get('dag_run').conf or {}

    # Allow working_directory override, but always use cleanup prompt
    if 'prompt' not in dag_run_conf:
        dag_run_conf['prompt'] = PYTHON_CLEANUP_PROMPT

    # Update context with merged config
    context['dag_run'].conf = dag_run_conf

    # Delegate to the reusable function (SSOT)
    return run_claude_query_sdk(**context)


# DAG definition
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2025, 10, 2),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

with DAG(
    'python_cleanup',
    default_args=default_args,
    description='Clean up Python artifacts (__pycache__, .pyc, etc.) from repository',
    schedule=None,  # Manual trigger only
    catchup=False,
    tags=['python', 'cleanup', 'maintenance'],
) as dag:

    cleanup_task = PythonOperator(
        task_id='cleanup_python_artifacts',
        python_callable=cleanup_python_artifacts,
        doc_md="""
        ### Python Artifacts Cleanup

        This task reuses `run_claude_query_sdk` to clean Python-generated files.

        **What it cleans:**
        - `__pycache__/` directories
        - `*.pyc`, `*.pyo` files
        - `*.egg-info/` directories
        - `.pytest_cache/`, `.tox/`, `.coverage` files

        **Default Working Directory:** Project root (from config)

        **Override working directory (CLI):**
        ```bash
        airflow dags trigger python_cleanup --conf '{"working_directory": "/path/to/repo"}'
        ```

        **Override working directory (UI):**
        1. Click "Trigger DAG"
        2. Add JSON: `{"working_directory": "/path/to/repo"}`
        3. Click "Trigger"

        **Architecture:**
        - ✅ **SSOT**: Reuses `run_claude_query_sdk` for Claude SDK execution
        - ✅ **SRP**: Wrapper provides domain-specific configuration only
        - ✅ Pre-defined stable prompt for repeatable cleanup
        - ✅ Parameterizable working directory
        - ✅ Non-blocking execution via claude_wrapper.py

        **Output:** Check logs to see what was cleaned!
        """,
    )

    cleanup_task

