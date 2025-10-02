"""
Airflow DAG for intelligent git commit and push operations.

This DAG:
- Reuses run_claude_query_sdk function (SSOT, SRP)
- Uses a pre-defined prompt for git operations
- Parameterizable working directory
"""

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from datetime import datetime, timedelta

# Try new import path first, fallback to old for compatibility
try:
    from airflow.sdk import Param
except ImportError:
    from airflow.models.param import Param

# Import the reusable function (SSOT - Single Source of Truth)
# Note: claude_query_sdk.py must be in the same dags folder
import sys
from pathlib import Path

# Ensure dags folder is in path for imports
sys.path.insert(0, str(Path(__file__).parent))

from claude_query_sdk import run_claude_query_sdk


# Pre-defined git commit and push prompt for stable, repeatable execution
GIT_COMMIT_PUSH_PROMPT = """Perform intelligent git commit and push operations:

1. Check git status for uncommitted and untracked files
2. Analyze the changes to understand what was modified
3. Group related changes into logical, atomic commits
4. For each group of changes:
   - Stage the related files
   - Write a descriptive commit message that explains WHY the changes were made
   - Create the commit
5. After all commits are made, push to the remote repository
6. Report what was committed and pushed

Important:
- Make atomic commits (each commit should be a logical unit of work)
- Write clear, descriptive commit messages
- Follow conventional commit format if the repo uses it
- Do NOT clean up files, only perform git operations"""


def commit_and_push(**context):
    """
    Wrapper function that calls run_claude_query_sdk with git commit/push prompt.

    This follows SRP (Single Responsibility Principle):
    - This function: Provides domain-specific configuration
    - run_claude_query_sdk: Handles Claude SDK execution

    Allows working_directory override via DAG params or dag_run.conf.
    """
    # Get params from context (set in UI or CLI)
    params = context.get('params', {})
    dag_run_conf = context.get('dag_run').conf or {}

    # Merge: dag_run.conf takes precedence over params
    working_directory = dag_run_conf.get('working_directory') or params.get('working_directory')

    # Build config with commit/push prompt
    config = {
        'prompt': GIT_COMMIT_PUSH_PROMPT,
        'working_directory': working_directory,
    }

    # Update context with merged config
    context['dag_run'].conf = config

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
    'commit_and_push',
    default_args=default_args,
    description='Intelligently commit and push changes to git repository',
    schedule=None,  # Manual trigger only
    catchup=False,
    tags=['git', 'commit', 'push', 'automation'],
    params={
        'working_directory': Param(
            default='/home/rmondo/repos/air-executor',
            type='string',
            title='Working Directory',
            description='Repository path to commit and push. Defaults to air-executor project root.',
            minLength=1,
            section='Repository Configuration',
        ),
    },
) as dag:

    commit_push_task = PythonOperator(
        task_id='commit_and_push',
        python_callable=commit_and_push,
        doc_md="""
        ### Git Commit and Push Automation

        This task reuses `run_claude_query_sdk` to intelligently commit and push changes.

        **What it does:**
        - Analyzes uncommitted and untracked files
        - Groups related changes into atomic commits
        - Writes descriptive commit messages
        - Pushes all commits to remote repository

        **Default Working Directory:** `/home/rmondo/repos/air-executor`

        **Override working directory (Web UI):**
        1. Click "Trigger DAG w/ config"
        2. Edit "Working Directory" field in the form
        3. Click "Trigger"

        **Override working directory (CLI):**
        ```bash
        airflow dags trigger commit_and_push --conf '{"working_directory": "/path/to/repo"}'
        ```

        **Architecture:**
        - ✅ **SSOT**: Reuses `run_claude_query_sdk` for Claude SDK execution
        - ✅ **SRP**: Wrapper provides domain-specific configuration only
        - ✅ Pre-defined stable prompt for repeatable git operations
        - ✅ Parameterizable working directory
        - ✅ Non-blocking execution via claude_wrapper.py

        **Output:** Check logs to see what was committed and pushed!
        """,
    )

    commit_push_task
