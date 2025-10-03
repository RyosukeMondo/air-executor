#!/bin/bash
# Quick tool validation check - uses same Python detection as run_autonomous_fix.sh
# KISS principle: Simple, robust, always works

set -e

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# ============================================================================
# PYTHON ENVIRONMENT AUTO-DETECTION (same logic as run_autonomous_fix.sh)
# ============================================================================

PYTHON_CMD=""

if [ -f ".venv/bin/python" ]; then
    PYTHON_CMD=".venv/bin/python"
elif [ -f ".venv/air-executor/bin/python" ]; then
    PYTHON_CMD=".venv/air-executor/bin/python"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ No Python found!"
    exit 1
fi

# Set PYTHONPATH
export PYTHONPATH="$PROJECT_ROOT"

# ============================================================================
# RUN VALIDATION
# ============================================================================

MODE="${1:---check-all}"

case "$MODE" in
    --check-all|all)
        $PYTHON_CMD airflow_dags/autonomous_fixing/core/tool_validator.py --check-all
        ;;
    --check-flutter|flutter)
        $PYTHON_CMD airflow_dags/autonomous_fixing/core/tool_validator.py --check-flutter
        ;;
    --help|-h)
        echo "Usage: $0 [MODE]"
        echo ""
        echo "Modes:"
        echo "  --check-all      Check all language toolchains (default)"
        echo "  --check-flutter  Check Flutter toolchain only"
        echo "  --help           Show this help"
        echo ""
        echo "Examples:"
        echo "  $0                    # Check all"
        echo "  $0 --check-flutter    # Check Flutter only"
        ;;
    *)
        echo "❌ Unknown mode: $MODE"
        echo "Use --help for usage"
        exit 1
        ;;
esac
