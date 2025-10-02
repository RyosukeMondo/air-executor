#!/usr/bin/env python3
"""
DAG Validation and Quick Discovery Tool

This script:
1. Validates DAG syntax before deployment
2. Forces immediate DAG discovery (no 5-minute wait)
3. Checks for common issues
4. Provides instant feedback
"""

import sys
import subprocess
from pathlib import Path
import importlib.util


def validate_dag_file(dag_file: Path) -> tuple[bool, str]:
    """
    Validate a DAG file for syntax and import errors.

    Returns:
        (is_valid, message)
    """
    print(f"🔍 Validating {dag_file.name}...")

    # Check file exists
    if not dag_file.exists():
        return False, f"❌ File not found: {dag_file}"

    # Try to import the module
    try:
        spec = importlib.util.spec_from_file_location("dag_module", dag_file)
        if spec is None or spec.loader is None:
            return False, f"❌ Could not load module spec for {dag_file}"

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Check if module has DAG objects
        has_dag = False
        dag_ids = []

        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if hasattr(attr, '__class__') and attr.__class__.__name__ == 'DAG':
                has_dag = True
                dag_ids.append(attr.dag_id)

        if not has_dag:
            return False, "❌ No DAG objects found in file"

        return True, f"✅ Valid! Found DAG(s): {', '.join(dag_ids)}"

    except Exception as e:
        return False, f"❌ Import error: {str(e)}"


def force_dag_discovery():
    """Force Airflow to discover new DAGs immediately."""
    print("\n🔄 Forcing DAG discovery...")
    try:
        result = subprocess.run(
            ["airflow", "dags", "reserialize"],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            print("✅ DAG reserialize completed")
            return True
        else:
            print(f"⚠️  Reserialize warning: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("⚠️  Reserialize timed out (this is sometimes normal)")
        return True
    except Exception as e:
        print(f"❌ Failed to force discovery: {e}")
        return False


def check_dag_in_airflow(dag_id: str) -> bool:
    """Check if DAG is registered in Airflow."""
    print(f"\n🔎 Checking if '{dag_id}' is registered in Airflow...")
    try:
        result = subprocess.run(
            ["airflow", "dags", "list"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if dag_id in result.stdout:
            print(f"✅ DAG '{dag_id}' is registered!")
            return True
        else:
            print(f"⚠️  DAG '{dag_id}' not yet registered (may take up to 5 minutes)")
            return False
    except Exception as e:
        print(f"❌ Failed to check DAG: {e}")
        return False


def main():
    """Main validation workflow."""
    if len(sys.argv) < 2:
        print("Usage: ./validate_dag.py <path_to_dag.py>")
        print("\nExample:")
        print("  ./validate_dag.py airflow_dags/claude_query_dag.py")
        sys.exit(1)

    dag_file = Path(sys.argv[1])

    print("=" * 60)
    print("🚀 DAG Validation and Discovery Tool")
    print("=" * 60)

    # Step 1: Validate syntax
    is_valid, message = validate_dag_file(dag_file)
    print(message)

    if not is_valid:
        print("\n❌ Validation failed! Fix errors before deploying.")
        sys.exit(1)

    # Extract DAG ID from validation message
    dag_id = None
    if "Found DAG(s):" in message:
        dag_id = message.split("Found DAG(s): ")[1].split(",")[0].strip()

    # Step 2: Force discovery
    print("\n" + "=" * 60)
    force_dag_discovery()

    # Step 3: Check registration
    if dag_id:
        print("=" * 60)
        check_dag_in_airflow(dag_id)

    # Step 4: Provide next steps
    print("\n" + "=" * 60)
    print("📋 Next Steps:")
    print("=" * 60)
    print("1. Copy DAG to Airflow: ./airflow_dags/sync_to_airflow.sh")
    print("2. Access Airflow UI: http://localhost:8080")
    print(f"3. Find DAG: '{dag_id}'" if dag_id else "3. Find your DAG in the UI")
    print("4. Unpause DAG: Toggle the switch in UI")
    print("5. Trigger DAG: Click the play button")
    print("\n💡 Tip: DAGs are scanned every 5 minutes by default.")
    print("   Use 'airflow dags reserialize' to force immediate discovery.")
    print("=" * 60)


if __name__ == "__main__":
    main()
