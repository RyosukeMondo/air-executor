#!/bin/bash
# Quick DAG deployment with validation and instant discovery

set -e  # Exit on error

DAG_FILE=$1

if [ -z "$DAG_FILE" ]; then
    echo "❌ Usage: ./scripts/quick_deploy_dag.sh <dag_file>"
    echo ""
    echo "Example:"
    echo "  ./scripts/quick_deploy_dag.sh airflow_dags/my_dag.py"
    exit 1
fi

if [ ! -f "$DAG_FILE" ]; then
    echo "❌ File not found: $DAG_FILE"
    exit 1
fi

echo "🚀 Quick DAG Deployment"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Activate venv
source .venv/bin/activate

# Step 1: Validate
echo ""
echo "📝 Step 1: Validating DAG..."
python scripts/validate_dag.py "$DAG_FILE" || {
    echo ""
    echo "❌ Validation failed! Fix errors before deploying."
    exit 1
}

# Step 2: Sync
echo ""
echo "📝 Step 2: Syncing to Airflow..."
./airflow_dags/sync_to_airflow.sh

# Step 3: Force discovery (already done by validate_dag.py, but ensuring)
echo ""
echo "📝 Step 3: Ensuring discovery..."
airflow dags reserialize > /dev/null 2>&1

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ DAG deployed successfully!"
echo ""
echo "🌐 Access Airflow UI: http://localhost:8080"
echo ""
echo "Next: Unpause and trigger your DAG in the UI"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
