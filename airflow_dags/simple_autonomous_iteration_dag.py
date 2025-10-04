"""
Airflow DAG for Simple Autonomous Iteration.

Executes a prompt repeatedly until completion condition is met.

Access at: http://localhost:8080
Trigger with parameters:
{
    "prompt": "resume @claudedocs/testability-improvements-plan.md perform implementation one step at a time. when everything done, check 'everything done' sits at the very last of the md file. - [ ] everything done",
    "completion_file": "claudedocs/testability-improvements-plan.md",
    "completion_regex": "- \\[x\\] everything done",
    "max_iterations": 30,
    "project_path": "/home/rmondo/repos/air-executor"
}
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project to path BEFORE importing local modules
sys.path.insert(0, "/home/rmondo/repos/air-executor/airflow_dags")

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from simple_autonomous_iteration.simple_orchestrator import SimpleOrchestrator


def run_simple_iteration(**context):
    """
    Run simple autonomous iteration with streaming output.

    DAG parameters (pass via dag_run.conf):
    - prompt: Prompt to send to Claude on each iteration
    - completion_file: Path to file to check for completion (relative to project_path)
    - completion_regex: Regex pattern to match completion (default: "- \\[x\\] everything done")
    - max_iterations: Maximum number of iterations (default: 30)
    - project_path: Working directory (default: /home/rmondo/repos/air-executor)
    - wrapper_path: Path to claude_wrapper.py (default: scripts/claude_wrapper.py)
    - python_exec: Python executable (default: .venv/bin/python3)
    - circuit_breaker_threshold: Stop after N iterations without progress (default: 3)
    - require_git_changes: Require git changes for progress (default: true)
    """
    # Get parameters
    dag_run_conf = context.get("dag_run").conf or {}

    prompt = dag_run_conf.get(
        "prompt",
        "resume @claudedocs/testability-improvements-plan.md perform implementation one step at a time. when everything done, check 'everything done' sits at the very last of the md file. - [ ] everything done",
    )
    completion_file = dag_run_conf.get(
        "completion_file", "claudedocs/testability-improvements-plan.md"
    )
    completion_regex = dag_run_conf.get("completion_regex", r"- \[x\] everything done")
    max_iterations = dag_run_conf.get("max_iterations", 30)
    project_path = dag_run_conf.get("project_path", "/home/rmondo/repos/air-executor")
    wrapper_path = dag_run_conf.get("wrapper_path", "scripts/claude_wrapper.py")
    python_exec = dag_run_conf.get("python_exec", ".venv/bin/python3")
    circuit_breaker_threshold = dag_run_conf.get("circuit_breaker_threshold", 3)
    require_git_changes = dag_run_conf.get("require_git_changes", True)

    print("=" * 80)
    print("🚀 Starting Simple Autonomous Iteration")
    print("=" * 80)
    print(f"Prompt: {prompt[:100]}...")
    print(f"Completion file: {completion_file}")
    print(f"Completion regex: {completion_regex}")
    print(f"Max iterations: {max_iterations}")
    print(f"Project path: {project_path}")
    print(f"Circuit breaker: {circuit_breaker_threshold} iterations without progress")
    print(f"Git change tracking: {'enabled' if require_git_changes else 'disabled'}")
    print("=" * 80)
    print()

    # Create orchestrator
    orchestrator = SimpleOrchestrator(
        prompt=prompt,
        completion_check_file=str(Path(project_path) / completion_file),
        completion_regex=completion_regex,
        max_iterations=max_iterations,
        project_path=project_path,
        wrapper_path=wrapper_path,
        python_exec=python_exec,
        circuit_breaker_threshold=circuit_breaker_threshold,
        require_git_changes=require_git_changes,
    )

    # Run orchestrator
    result = orchestrator.run()

    print()
    print("=" * 80)
    if result["success"]:
        print("✅ Simple iteration completed successfully!")
        print(f"   Reason: {result['reason']}")
        print(f"   Iterations: {result['iterations_completed']}")
        print(f"   Duration: {result['total_duration']:.1f}s")
    else:
        print("❌ Simple iteration did not complete")
        print(f"   Reason: {result['reason']}")
        print(f"   Iterations: {result['iterations_completed']}")
        print(f"   Duration: {result['total_duration']:.1f}s")
    print("=" * 80)

    if not result["success"]:
        raise RuntimeError(f"Orchestrator did not complete: {result['reason']}")


# Default DAG arguments
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 0,  # Don't auto-retry (user can manually retry if needed)
    "retry_delay": timedelta(minutes=5),
}

# Create DAG
with DAG(
    "simple_autonomous_iteration",
    default_args=default_args,
    description="Run simple autonomous iteration with completion check",
    schedule=None,  # Manual trigger only
    start_date=datetime(2025, 10, 1),
    catchup=False,
    tags=["autonomous", "iteration", "simple", "claude"],
) as dag:
    iteration_task = PythonOperator(
        task_id="run_simple_iteration",
        python_callable=run_simple_iteration,
        execution_timeout=timedelta(hours=8),  # Allow up to 8 hours for 30 iterations
    )

    iteration_task


# Example usage in Airflow UI:
# 1. Go to http://localhost:8080
# 2. Find "simple_autonomous_iteration" DAG
# 3. Click "Trigger DAG w/ config"
# 4. Enter JSON:
#    {
#      "prompt": "resume @claudedocs/testability-improvements-plan.md perform implementation one step at a time. when everything done, check 'everything done' sits at the very last of the md file. - [ ] everything done",
#      "completion_file": "claudedocs/testability-improvements-plan.md",
#      "completion_regex": "- \\[x\\] everything done",
#      "max_iterations": 30,
#      "circuit_breaker_threshold": 3,
#      "require_git_changes": true
#    }
# 5. Click "Logs" to see streaming output in real-time!
