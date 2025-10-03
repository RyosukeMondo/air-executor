#!/bin/bash
# Robust wrapper for autonomous fixing - handles Python environment automatically
# KISS principle: One script, all environments work

set -e

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Change to project root
cd "$PROJECT_ROOT"

# ============================================================================
# PYTHON ENVIRONMENT AUTO-DETECTION
# ============================================================================

PYTHON_CMD=""
PYTHON_ENV="system"

# 1. Try project venv first (.venv)
if [ -f ".venv/bin/python" ]; then
    PYTHON_CMD=".venv/bin/python"
    PYTHON_ENV="venv(.venv)"
    echo "✅ Using project virtual environment: .venv"

# 2. Try config-specified venv
elif [ -f ".venv/air-executor/bin/python" ]; then
    PYTHON_CMD=".venv/air-executor/bin/python"
    PYTHON_ENV="venv(.venv/air-executor)"
    echo "✅ Using configured virtual environment: .venv/air-executor"

# 3. Try system python3
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    PYTHON_ENV="system(python3)"
    echo "✅ Using system Python: python3"

# 4. Try system python
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
    PYTHON_ENV="system(python)"
    echo "⚠️  Using system Python: python (not python3)"

else
    echo "❌ No Python found!"
    echo "   Install Python: sudo apt install python3"
    exit 1
fi

# Verify Python works
$PYTHON_CMD --version || {
    echo "❌ Python command failed: $PYTHON_CMD"
    exit 1
}

# ============================================================================
# PYTHONPATH SETUP
# ============================================================================

# Always set PYTHONPATH to project root
export PYTHONPATH="$PROJECT_ROOT"
echo "✅ PYTHONPATH=$PYTHONPATH"

# ============================================================================
# PARSE ARGUMENTS
# ============================================================================

if [ $# -lt 1 ]; then
    echo ""
    echo "Usage: $0 <config.yaml> [options]"
    echo ""
    echo "Examples:"
    echo "  $0 config/projects/money-making-app.yaml"
    echo "  $0 config/projects/air-executor.yaml"
    echo "  $0 config/projects/cc-task-manager.yaml"
    echo ""
    echo "Options:"
    echo "  --background    Run in background"
    echo "  --log FILE      Custom log file (default: logs/orchestrator_run.log)"
    echo "  --check-tools   Run tool validation only"
    echo ""
    exit 1
fi

CONFIG_FILE="$1"
shift

# Check config exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ Config file not found: $CONFIG_FILE"
    exit 1
fi

# Parse options
RUN_BACKGROUND=false
LOG_FILE="logs/orchestrator_run.log"
CHECK_TOOLS_ONLY=false

while [ $# -gt 0 ]; do
    case "$1" in
        --background)
            RUN_BACKGROUND=true
            shift
            ;;
        --log)
            LOG_FILE="$2"
            shift 2
            ;;
        --check-tools)
            CHECK_TOOLS_ONLY=true
            shift
            ;;
        *)
            echo "❌ Unknown option: $1"
            exit 1
            ;;
    esac
done

# ============================================================================
# TOOL VALIDATION (OPTIONAL PRE-FLIGHT)
# ============================================================================

if [ "$CHECK_TOOLS_ONLY" = true ]; then
    echo ""
    echo "Running tool validation only..."
    $PYTHON_CMD airflow_dags/autonomous_fixing/core/tool_validator.py --check-all
    exit $?
fi

# ============================================================================
# RUN ORCHESTRATOR
# ============================================================================

echo ""
echo "============================================================================"
echo "🚀 Starting Autonomous Fix"
echo "============================================================================"
echo "Config:      $CONFIG_FILE"
echo "Python:      $PYTHON_CMD ($PYTHON_ENV)"
echo "Working Dir: $PROJECT_ROOT"
echo "Log File:    $LOG_FILE"
echo "============================================================================"
echo ""

# Create logs directory
mkdir -p "$(dirname "$LOG_FILE")"
mkdir -p "logs/debug"

if [ "$RUN_BACKGROUND" = true ]; then
    # Background mode
    echo "Running in background..."
    $PYTHON_CMD airflow_dags/autonomous_fixing/multi_language_orchestrator.py "$CONFIG_FILE" > "$LOG_FILE" 2>&1 &
    PID=$!
    echo "✅ Started with PID: $PID"
    echo ""
    echo "Monitor with:"
    echo "  tail -f $LOG_FILE"
    echo "  tail -f logs/debug/multi-project_*.jsonl"
    echo ""
    echo "Stop with:"
    echo "  kill $PID"
    echo ""
else
    # Foreground mode (with tee for live output + logging)
    $PYTHON_CMD -u airflow_dags/autonomous_fixing/multi_language_orchestrator.py "$CONFIG_FILE" 2>&1 | tee "$LOG_FILE"
    EXIT_CODE=${PIPESTATUS[0]}

    echo ""
    echo "============================================================================"
    if [ $EXIT_CODE -eq 0 ]; then
        echo "✅ Autonomous fix completed successfully"
    else
        echo "❌ Autonomous fix failed with exit code: $EXIT_CODE"
    fi
    echo "============================================================================"
    echo ""

    exit $EXIT_CODE
fi
