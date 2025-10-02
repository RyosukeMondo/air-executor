"""
Simple Airflow DAG that runs: claude -p "hello, how old are you?"
and captures the output.
"""

from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator
from datetime import datetime, timedelta

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
    'claude_query',
    default_args=default_args,
    description='Simple DAG to run Claude query and return output',
    schedule=None,  # Manual trigger only
    catchup=False,
    tags=['claude', 'simple'],
) as dag:

    # Single task: Run claude command
    run_claude = BashOperator(
        task_id='run_claude_query',
        bash_command='claude -p "hello, how old are you?"',
        doc_md="""
        ### Run Claude Query

        This task executes the Claude CLI with the prompt:
        "hello, how old are you?"

        The output will be captured in the task logs.
        Click "Log" to see Claude's response.
        """,
    )

    run_claude
