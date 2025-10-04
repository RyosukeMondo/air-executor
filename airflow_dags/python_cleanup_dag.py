"""
Airflow DAG for cleaning up Python-generated artifacts from repositories.

This DAG:
- Reuses run_claude_query_sdk function (SSOT, SRP)
- Uses a pre-defined prompt for stable Python cleanup
- Parameterizable working directory
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

# Ensure dags folder is in path for imports BEFORE importing local modules
sys.path.insert(0, str(Path(__file__).parent))

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator

# Try new import path first, fallback to old for compatibility
try:
    from airflow.sdk import Param
except ImportError:
    from airflow.models.param import Param

from claude_query_sdk import run_claude_query_sdk

# Pre-defined cleanup prompt for stable, repeatable execution
PYTHON_CLEANUP_PROMPT = """
Find and clean up Python-generated artifacts that shouldn't be tracked:

1. Find all __pycache__ directories, .pyc, .pyo files
2. Find other Python artifacts (.egg-info, .pytest_cache, .coverage, .tox, etc.)
3. Remove all found artifacts from the working directory
4. Report what was cleaned up

Important: DO NOT commit or push changes. This DAG only cleans the working directory."""


def cleanup_python_artifacts(**context):
    """
    Wrapper function that calls run_claude_query_sdk with cleanup prompt.

    This follows SRP (Single Responsibility Principle):
    - This function: Provides domain-specific configuration
    - run_claude_query_sdk: Handles Claude SDK execution

    Allows working_directory override via DAG params or dag_run.conf.
    """
    # Get params from context (set in UI or CLI)
    params = context.get("params", {})
    dag_run_conf = context.get("dag_run").conf or {}

    # Merge: dag_run.conf takes precedence over params
    working_directory = dag_run_conf.get("working_directory") or params.get("working_directory")

    # Build config with cleanup prompt
    config = {
        "prompt": PYTHON_CLEANUP_PROMPT,
        "working_directory": working_directory,
    }

    # Update context with merged config
    context["dag_run"].conf = config

    # Delegate to the reusable function (SSOT)
    return run_claude_query_sdk(**context)


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
    "python_cleanup",
    default_args=default_args,
    description="Clean up Python artifacts (__pycache__, .pyc, etc.) from repository",
    schedule=None,  # Manual trigger only
    catchup=False,
    tags=["python", "cleanup", "maintenance"],
    params={
        "working_directory": Param(
            default="/home/rmondo/repos/air-executor",
            type="string",
            title="Working Directory",
            description="Repository path to clean. Defaults to air-executor project root.",
            minLength=1,
            section="Repository Configuration",
        ),
    },
) as dag:
    cleanup_task = PythonOperator(
        task_id="cleanup_python_artifacts",
        python_callable=cleanup_python_artifacts,
        doc_md="""
        ### Python Artifacts Cleanup

        This task reuses `run_claude_query_sdk` to clean Python-generated files.

        **What it cleans:**
        - `__pycache__/` directories
        - `*.pyc`, `*.pyo` files
        - `*.egg-info/` directories
        - `.pytest_cache/`, `.tox/`, `.coverage` files

        **Default Working Directory:** `/home/rmondo/repos/air-executor`

        **Override working directory (Web UI):**
        1. Click "Trigger DAG w/ config"
        2. Edit "Working Directory" field in the form
        3. Click "Trigger"

        **Override working directory (CLI):**
        ```bash
        airflow dags trigger python_cleanup --conf '{"working_directory": "/path/to/repo"}'
        ```

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
