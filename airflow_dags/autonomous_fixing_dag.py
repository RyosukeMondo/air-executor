"""
Airflow DAG for Autonomous Code Fixing with Web UI Monitoring.

This DAG runs the autonomous fixing orchestrator and streams output
to the Airflow web UI for real-time monitoring.

Access at: http://localhost:8080
Trigger with parameters:
{
    "max_iterations": 10,
    "target_project": "/home/rmondo/repos/money-making-app",
    "simulation": false
}
"""

import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

import yaml

# Add project to path
sys.path.insert(0, "/home/rmondo/repos/air-executor/src")

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator

from airflow_dags.autonomous_fixing.domain.exceptions import OrchestratorExitError


def run_autonomous_fixing(**context):
    """
    Run autonomous code fixing orchestrator with streaming output.

    DAG parameters (pass via dag_run.conf):
    - max_iterations: Number of fixing iterations (default: 10)
    - target_project: Path to project to fix (default: from config)
    - simulation: If true, simulate without making changes (default: false)
    """
    # Get parameters
    dag_run_conf = context.get("dag_run").conf or {}
    max_iterations = dag_run_conf.get("max_iterations", 10)
    simulation = dag_run_conf.get("simulation", False)
    target_project = dag_run_conf.get("target_project")

    # Paths
    project_root = Path("/home/rmondo/repos/air-executor")
    orchestrator_path = project_root / "airflow_dags/autonomous_fixing/fix_orchestrator.py"
    config_path = project_root / "config/autonomous_fix.yaml"
    venv_python = Path.home() / ".venv/air-executor/bin/python"

    # Override target project in config if provided
    if target_project:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        config["target_project"]["path"] = target_project
        config_path_temp = project_root / "config/autonomous_fix_temp.yaml"
        with open(config_path_temp, "w", encoding="utf-8") as f:
            yaml.dump(config, f)
        config_path = config_path_temp

    # Build command
    cmd = [
        str(venv_python),
        str(orchestrator_path),
        str(config_path),
        f"--max-iterations={max_iterations}",
    ]

    if simulation:
        cmd.append("--simulation")

    print("=" * 80)
    print("🚀 Starting Autonomous Code Fixing Orchestrator")
    print("=" * 80)
    print(f"Max iterations: {max_iterations}")
    print(f"Simulation mode: {simulation}")
    print(f"Config: {config_path}")
    print(f"Command: {' '.join(cmd)}")
    print("=" * 80)
    print()

    # Run orchestrator with streaming output
    with subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,  # Combine stderr with stdout
        text=True,
        bufsize=1,  # Line buffered for real-time output
        universal_newlines=True,
    ) as process:
        # Stream output line by line (appears in Airflow UI)
        try:
            for line in process.stdout:
                # Print to Airflow logs (visible in web UI)
                print(line, end="", flush=True)

            # Wait for completion
            process.wait()

            print()
            print("=" * 80)
            if process.returncode == 0:
                print("✅ Autonomous fixing completed successfully!")
            else:
                print(f"❌ Autonomous fixing failed with exit code {process.returncode}")
            print("=" * 80)

            # Cleanup temp config if created
            if target_project:
                config_path.unlink(missing_ok=True)

            if process.returncode != 0:
                raise OrchestratorExitError(process.returncode)

        except Exception:
            process.kill()
            # Cleanup temp config
            if target_project:
                config_path.unlink(missing_ok=True)
            raise


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
    "autonomous_fixing",
    default_args=default_args,
    description="Run autonomous code fixing with Claude AI",
    schedule=None,  # Manual trigger only (can set schedule if desired)
    start_date=datetime(2025, 10, 1),
    catchup=False,
    tags=["autonomous", "fixing", "claude"],
) as dag:
    fixing_task = PythonOperator(
        task_id="run_autonomous_fixing",
        python_callable=run_autonomous_fixing,
        execution_timeout=timedelta(hours=4),  # Match config max_duration_hours
    )

    fixing_task


# Example usage in Airflow UI:
# 1. Go to http://localhost:8080
# 2. Find "autonomous_fixing" DAG
# 3. Click "Trigger DAG w/ config"
# 4. Enter JSON:
#    {
#      "max_iterations": 10,
#      "simulation": false
#    }
# 5. Click "Logs" to see streaming output in real-time!
