#!/bin/bash
# Validate Airflow DAG files and check for common issues

set -e

AIRFLOW_DAGS="${AIRFLOW_DAGS:-/home/rmondo/airflow/dags}"
VENV_PYTHON="${VENV_PYTHON:-/home/rmondo/repos/air-executor/.venv/bin/python}"

echo "🔍 Airflow DAG Validation Tool"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "DAGs folder: $AIRFLOW_DAGS"
echo ""

# Check if DAGs folder exists
if [ ! -d "$AIRFLOW_DAGS" ]; then
    echo "❌ DAGs folder not found: $AIRFLOW_DAGS"
    exit 1
fi

# Find all Python files in DAGs folder
DAG_FILES=$(find "$AIRFLOW_DAGS" -maxdepth 1 -name "*.py" ! -name "__*" -type f)

if [ -z "$DAG_FILES" ]; then
    echo "⚠️  No DAG files found in $AIRFLOW_DAGS"
    exit 0
fi

echo "📋 Found DAG files:"
echo "$DAG_FILES" | while read -r file; do
    echo "   - $(basename "$file")"
done
echo ""

TOTAL=0
PASSED=0
FAILED=0

# Validation function with detailed checks
validate_dag_detailed() {
    local dag_file=$1
    local dag_name=$(basename "$dag_file")

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Validating: $dag_name"
    echo ""

    local has_error=0

    # 1. Check syntax
    echo "  [1/5] Checking Python syntax..."
    if $VENV_PYTHON -m py_compile "$dag_file" 2>/dev/null; then
        echo "        ✓ Syntax valid"
    else
        echo "        ✗ Syntax error detected"
        $VENV_PYTHON -m py_compile "$dag_file" 2>&1 | sed 's/^/          /'
        has_error=1
    fi

    # 2. Check imports
    echo "  [2/5] Checking imports..."
    cd "$AIRFLOW_DAGS"
    IMPORT_OUTPUT=$($VENV_PYTHON -c "
import sys
import os
sys.path.insert(0, '$AIRFLOW_DAGS')
os.chdir('$AIRFLOW_DAGS')
try:
    exec(open('$dag_file').read())
    print('OK')
except ModuleNotFoundError as e:
    print(f'MISSING_MODULE:{e.name}')
    sys.exit(1)
except Exception as e:
    print(f'ERROR:{type(e).__name__}: {e}')
    sys.exit(1)
" 2>&1)

    if [ $? -eq 0 ]; then
        echo "        ✓ All imports successful"
    else
        echo "        ✗ Import error:"
        echo "$IMPORT_OUTPUT" | sed 's/^/          /'
        has_error=1
    fi
    cd - > /dev/null

    # 3. Check for DAG object
    echo "  [3/5] Checking for DAG definition..."
    if grep -q "with DAG\|@dag\|DAG(" "$dag_file"; then
        echo "        ✓ DAG definition found"
    else
        echo "        ⚠  No DAG definition found (may not be a DAG file)"
    fi

    # 4. Check for common issues
    echo "  [4/5] Checking for common issues..."

    # Check for hardcoded paths
    if grep -q "/home/\|/Users/\|C:\\\\" "$dag_file"; then
        echo "        ⚠  Warning: Hardcoded paths detected"
        grep -n "/home/\|/Users/\|C:\\\\" "$dag_file" | head -3 | sed 's/^/          Line /'
    fi

    # Check for print statements (should use logging)
    if grep -q "^\s*print(" "$dag_file"; then
        echo "        ⚠  Warning: print() statements found (use logging instead)"
    fi

    # Check for missing docstring
    if ! head -20 "$dag_file" | grep -q '"""'; then
        echo "        ⚠  Warning: No module docstring found"
    fi

    echo "        ✓ Common issues check complete"

    # 5. Check Airflow can parse it
    echo "  [5/5] Checking Airflow parsing..."
    if command -v airflow &> /dev/null; then
        cd "$AIRFLOW_DAGS"
        PARSE_OUTPUT=$(source /home/rmondo/repos/air-executor/.venv/bin/activate && airflow dags list-import-errors 2>&1 | grep "$dag_name" || echo "")
        cd - > /dev/null

        if [ -z "$PARSE_OUTPUT" ]; then
            echo "        ✓ No Airflow import errors"
        else
            echo "        ✗ Airflow import error:"
            echo "$PARSE_OUTPUT" | sed 's/^/          /'
            has_error=1
        fi
    else
        echo "        ⚠  Airflow CLI not available, skipping"
    fi

    echo ""
    if [ $has_error -eq 0 ]; then
        echo "  ✅ $dag_name validation PASSED"
        return 0
    else
        echo "  ❌ $dag_name validation FAILED"
        return 1
    fi
}

# Validate each DAG
echo "$DAG_FILES" | while read -r dag_file; do
    if validate_dag_detailed "$dag_file"; then
        PASSED=$((PASSED + 1))
    else
        FAILED=$((FAILED + 1))
    fi
    TOTAL=$((TOTAL + 1))
    echo ""
done

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Validation Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Count results (need to re-run since while loop is in subshell)
TOTAL=$(echo "$DAG_FILES" | wc -l)
PASSED=0
FAILED=0

echo "$DAG_FILES" | while read -r dag_file; do
    if $VENV_PYTHON -m py_compile "$dag_file" 2>/dev/null; then
        PASSED=$((PASSED + 1))
    else
        FAILED=$((FAILED + 1))
    fi
done

echo "Total DAGs checked: $TOTAL"
echo ""

# Check Airflow DAG list
if command -v airflow &> /dev/null; then
    echo "📋 Registered DAGs in Airflow:"
    source /home/rmondo/repos/air-executor/.venv/bin/activate
    airflow dags list 2>/dev/null | grep -E "^(claude_query|python_cleanup|air_executor)" | sed 's/^/  - /'
fi

echo ""
echo "✅ Validation complete!"
