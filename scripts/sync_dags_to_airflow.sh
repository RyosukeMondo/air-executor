#!/bin/bash
# Sync DAG files to Airflow and validate them

set -e

PROJECT_ROOT="/home/rmondo/repos/air-executor"
AIRFLOW_DAGS="/home/rmondo/airflow/dags"
VENV_PYTHON="/home/rmondo/repos/air-executor/.venv/bin/python"

echo "📦 Syncing DAG files to Airflow"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Create directory if needed
mkdir -p "$AIRFLOW_DAGS"

# List of DAG files to sync
DAG_FILES=(
    "claude_query_dag.py"
    "claude_query_sdk.py"
    "python_cleanup_dag.py"
)

echo ""
echo "📋 Files to sync:"
for file in "${DAG_FILES[@]}"; do
    echo "   - $file"
done
echo ""

# Sync each file
for file in "${DAG_FILES[@]}"; do
    SOURCE="$PROJECT_ROOT/airflow_dags/$file"
    DEST="$AIRFLOW_DAGS/$file"

    if [ ! -f "$SOURCE" ]; then
        echo "❌ Source file not found: $SOURCE"
        exit 1
    fi

    cp "$SOURCE" "$DEST"
    echo "✅ Synced: $file"
done

echo ""
echo "🔍 Validating DAG files..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Validation function
validate_dag() {
    local dag_file=$1
    local dag_path="$AIRFLOW_DAGS/$dag_file"

    echo ""
    echo "Validating: $dag_file"

    # Test Python syntax
    if ! $VENV_PYTHON -m py_compile "$dag_path" 2>&1; then
        echo "❌ Syntax error in $dag_file"
        return 1
    fi
    echo "  ✓ Syntax OK"

    # Test DAG import (run in dags directory to ensure imports work)
    cd "$AIRFLOW_DAGS"
    if ! $VENV_PYTHON -c "
import sys
sys.path.insert(0, '$AIRFLOW_DAGS')
try:
    import ${dag_file%.py}
    print('  ✓ Import OK')
except Exception as e:
    print(f'  ✗ Import failed: {e}')
    sys.exit(1)
" 2>&1; then
        echo "❌ Import error in $dag_file"
        cd - > /dev/null
        return 1
    fi
    cd - > /dev/null

    echo "  ✓ DAG validation passed"
    return 0
}

# Validate each DAG
VALIDATION_FAILED=0
for file in "${DAG_FILES[@]}"; do
    if ! validate_dag "$file"; then
        VALIDATION_FAILED=1
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $VALIDATION_FAILED -eq 1 ]; then
    echo "❌ Validation failed for one or more DAGs"
    echo "   Check the errors above"
    exit 1
fi

echo "✅ All DAG files synced and validated successfully!"
echo ""
echo "📊 Checking Airflow DAG list..."

# Check if DAGs appear in Airflow
if command -v airflow &> /dev/null; then
    echo ""
    source "$PROJECT_ROOT/.venv/bin/activate"
    airflow dags list 2>/dev/null | grep -E "^(claude_query|python_cleanup)" || echo "⚠️  DAGs not yet visible (scheduler may need time to refresh)"
else
    echo "⚠️  Airflow CLI not available"
fi

echo ""
echo "✅ Sync complete!"
echo ""
echo "💡 To trigger the python_cleanup DAG:"
echo "   airflow dags trigger python_cleanup"
echo "   airflow dags trigger python_cleanup --conf '{\"working_directory\": \"/path/to/repo\"}'"
