#!/bin/bash
# Launch autonomous code fixing orchestrator
#
# Usage:
#   ./scripts/run_autonomous_fixing.sh [--max-iterations=N] [--simulation]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_PYTHON="$HOME/.venv/air-executor/bin/python"

# Check prerequisites
if [ ! -f "$VENV_PYTHON" ]; then
    echo "❌ Virtual environment not found: $VENV_PYTHON"
    echo "   Run: python -m venv ~/.venv/air-executor && $VENV_PYTHON -m pip install redis pyyaml"
    exit 1
fi

# Check Redis
if ! redis-cli ping > /dev/null 2>&1; then
    echo "❌ Redis is not running"
    echo "   Start it with: redis-server"
    exit 1
fi

# Check Flutter
if [ ! -f "$HOME/flutter/bin/flutter" ]; then
    echo "⚠️  Flutter not found at ~/flutter/bin/flutter"
fi

cd "$PROJECT_ROOT"

echo "🚀 Starting Autonomous Code Fixing Orchestrator"
echo "   Config: config/autonomous_fix.yaml"
echo "   Python: $VENV_PYTHON"
echo ""

# Run orchestrator
exec "$VENV_PYTHON" airflow_dags/autonomous_fixing/fix_orchestrator.py \
    config/autonomous_fix.yaml \
    "$@"
