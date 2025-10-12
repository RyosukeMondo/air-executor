#!/bin/bash
# Simple Autonomous Iteration - Runs iterative AI execution
# Works with monitor.sh for real-time monitoring
#
# Usage:
#   ./scripts/simple_autonomous_iteration.sh <config.json>
#
# Example:
#   Terminal 1: ./scripts/monitor.sh
#   Terminal 2: ./scripts/simple_autonomous_iteration.sh airflow_dags/simple_autonomous_iteration/examples/testability_iteration.json

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# ============================================================================
# BANNER
# ============================================================================

echo -e "${BLUE}"
echo "================================================================================"
echo "🔁 Simple Autonomous Iteration"
echo "================================================================================"
echo -e "${NC}"

# ============================================================================
# ARGUMENT PARSING
# ============================================================================

if [ $# -lt 1 ]; then
    echo -e "${RED}❌ Missing arguments${NC}"
    echo ""
    echo "Usage: $0 <plan_document> [project_path] [max_iterations]"
    echo "   OR: $0 <config.json> [project_path]"
    echo "   OR: $0 --spec-workflow --spec <spec_name> --project <project_path> [options]"
    echo ""
    echo "Examples:"
    echo "  # Use plan document directly (recommended)"
    echo "  $0 claudedocs/testability-improvements-plan.md"
    echo "  $0 claudedocs/testability-improvements-plan.md /path/to/project 50"
    echo ""
    echo "  # Use config file"
    echo "  $0 airflow_dags/simple_autonomous_iteration/examples/testability_iteration.json"
    echo "  $0 config.json /path/to/project"
    echo ""
    echo "  # Use spec-workflow mode"
    echo "  $0 --spec-workflow --spec dev-quality-agent --project /path/to/project"
    echo "  $0 --spec-workflow --spec my-spec --project /path/to/project --max-iterations 50"
    echo ""
    echo "Arguments:"
    echo "  plan_document  - Markdown plan with '- [ ] everything done' marker"
    echo "  project_path   - (Optional) Working directory (default: current dir)"
    echo "  max_iterations - (Optional) Max iterations (default: 30)"
    echo ""
    echo "Spec-workflow options:"
    echo "  --spec-workflow      - Enable spec-workflow mode"
    echo "  --spec <name>        - Spec name (required in spec-workflow mode)"
    echo "  --project <path>     - Project path (required in spec-workflow mode)"
    echo "  --max-iterations <n> - Max iterations (default: 50)"
    echo "  --completion-task <n>- Final task number for completion (optional)"
    echo ""
    echo "Tip: Run ./scripts/monitor.sh in another terminal to see real-time progress"
    echo ""
    exit 1
fi

# Check for spec-workflow mode
if [[ "$1" == "--spec-workflow" ]]; then
    SPEC_WORKFLOW_MODE=true
    SPEC_NAME=""
    SPEC_PROJECT_PATH=""
    SPEC_MAX_ITERATIONS="50"
    SPEC_COMPLETION_TASK=""

    shift  # Remove --spec-workflow from args

    # Parse spec-workflow arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --spec)
                SPEC_NAME="$2"
                shift 2
                ;;
            --project)
                SPEC_PROJECT_PATH="$2"
                shift 2
                ;;
            --max-iterations)
                SPEC_MAX_ITERATIONS="$2"
                shift 2
                ;;
            --completion-task)
                SPEC_COMPLETION_TASK="$2"
                shift 2
                ;;
            *)
                echo -e "${RED}❌ Unknown argument: $1${NC}"
                exit 1
                ;;
        esac
    done

    # Validate required arguments
    if [ -z "$SPEC_NAME" ]; then
        echo -e "${RED}❌ --spec argument is required in spec-workflow mode${NC}"
        exit 1
    fi

    if [ -z "$SPEC_PROJECT_PATH" ]; then
        echo -e "${RED}❌ --project argument is required in spec-workflow mode${NC}"
        exit 1
    fi

    # Validate project path exists
    if [ ! -d "$SPEC_PROJECT_PATH" ]; then
        echo -e "${RED}❌ Project path does not exist: $SPEC_PROJECT_PATH${NC}"
        exit 1
    fi

    # Validate spec exists
    SPEC_DIR="${SPEC_PROJECT_PATH}/.spec-workflow/specs/${SPEC_NAME}"
    if [ ! -d "$SPEC_DIR" ]; then
        echo -e "${RED}❌ Spec not found: $SPEC_DIR${NC}"
        echo -e "${YELLOW}💡 Available specs:${NC}"
        if [ -d "${SPEC_PROJECT_PATH}/.spec-workflow/specs" ]; then
            ls -1 "${SPEC_PROJECT_PATH}/.spec-workflow/specs/" 2>/dev/null || echo "  (none)"
        else
            echo "  .spec-workflow directory not found in project"
        fi
        exit 1
    fi

    # Validate tasks.md exists
    TASKS_FILE="${SPEC_DIR}/tasks.md"
    if [ ! -f "$TASKS_FILE" ]; then
        echo -e "${RED}❌ Tasks file not found: $TASKS_FILE${NC}"
        echo -e "${YELLOW}💡 Expected file structure:${NC}"
        echo "  ${SPEC_DIR}/"
        echo "  ├── requirements.md"
        echo "  ├── design.md"
        echo "  └── tasks.md  <- missing"
        exit 1
    fi

    # Create temporary config for spec-workflow mode
    CONFIG_FILE="/tmp/simple_autonomous_iteration_spec_$$.json"
    TEMP_CONFIG_CREATED=true

    SPEC_WORKFLOW_PROMPT="Work on spec: ${SPEC_NAME}

**THIS ITERATION - Complete ONE task only:**
1. Use spec-workflow to fetch the next pending task from ${SPEC_NAME} spec
2. Implement ONLY that task
3. Make/update tests for what you changed
4. Run linter and fix any issues if applicable
5. Use spec-workflow to update task status to completed
6. Commit changes with descriptive message
7. Use spec-workflow to check remaining tasks
8. DONE - End this iteration (next iteration will continue with next task)

**Critical:**
- Complete ONLY ONE task per iteration (not multiple tasks)
- Use spec-workflow MCP tools to fetch, update, and check tasks
- After commit, this iteration is DONE
- Orchestrator will automatically start next iteration
- Each iteration = one task cycle
- End session without asking for further actions"

    COMPLETION_FILE="${SPEC_PROJECT_PATH}/.spec-workflow/specs/${SPEC_NAME}/tasks.md"

    # Determine completion regex (properly escaped for JSON)
    if [ -n "$SPEC_COMPLETION_TASK" ]; then
        COMPLETION_REGEX="\\\\[x\\\\] ${SPEC_COMPLETION_TASK}\\\\."
    else
        # Default: look for any final task completion pattern
        COMPLETION_REGEX="\\\\[x\\\\] [0-9]+\\\\. Final integration testing and bug fixes"
    fi

    cat > "$CONFIG_FILE" <<EOF
{
  "prompt": $(echo "$SPEC_WORKFLOW_PROMPT" | python3 -c 'import json, sys; print(json.dumps(sys.stdin.read()))'),
  "completion_file": "$COMPLETION_FILE",
  "completion_regex": "$COMPLETION_REGEX",
  "max_iterations": $SPEC_MAX_ITERATIONS,
  "project_path": "$SPEC_PROJECT_PATH",
  "wrapper_path": "$PROJECT_ROOT/scripts/claude_wrapper.py",
  "python_exec": "$PROJECT_ROOT/.venv/bin/python3",
  "circuit_breaker_threshold": 3,
  "require_git_changes": true
}
EOF

    echo -e "${GREEN}✓${NC} Spec-workflow mode: $SPEC_NAME"
    echo -e "${GREEN}✓${NC} Project: $SPEC_PROJECT_PATH"
    echo -e "${GREEN}✓${NC} Generated temporary config: $CONFIG_FILE"
    echo ""

    OVERRIDE_PROJECT_PATH=""
    OVERRIDE_MAX_ITERATIONS=""

else
    # Original modes
    SPEC_WORKFLOW_MODE=false
    FIRST_ARG="$1"
    OVERRIDE_PROJECT_PATH="${2:-}"
    OVERRIDE_MAX_ITERATIONS="${3:-}"
fi

# Determine mode: plan document (.md) or config file (.json)
CONFIG_FILE="${CONFIG_FILE:-}"
TEMP_CONFIG_CREATED="${TEMP_CONFIG_CREATED:-false}"

if [[ "$SPEC_WORKFLOW_MODE" == false ]] && [[ "$FIRST_ARG" == *.md ]]; then
    # Plan document mode - create temporary config
    PLAN_DOCUMENT="$FIRST_ARG"

    if [ ! -f "$PLAN_DOCUMENT" ]; then
        echo -e "${RED}❌ Plan document not found: $PLAN_DOCUMENT${NC}"
        exit 1
    fi

    # Use override or default for max iterations
    MAX_ITER="${OVERRIDE_MAX_ITERATIONS:-30}"

    # Use override or current directory for project path
    PROJ_PATH="${OVERRIDE_PROJECT_PATH:-.}"

    # Generic prompt for any plan document
    GENERIC_PROMPT="Resume work on @${PLAN_DOCUMENT}. Work incrementally with commits:

**THIS ITERATION - Complete ONE task only:**
1. Check the plan - find the NEXT uncompleted task
2. Implement ONLY that task (or couple tightly related tasks)
3. Make/update tests for what you changed
4. Run linter and fix any issues (.venv/bin/python3 -m ruff check --fix)
5. Update the plan document with progress (mark task complete)
6. Commit changes with descriptive message
7. DONE - End this iteration (next iteration will continue with next task)

**Critical:**
- Complete ONLY ONE task per iteration (not multiple tasks)
- After commit, this iteration is DONE
- Orchestrator will automatically start next iteration
- Each iteration = one task cycle
- ONLY mark '- [x] everything done' when ALL phases are truly complete"

    # Create temporary config file
    CONFIG_FILE="/tmp/simple_autonomous_iteration_$$.json"
    TEMP_CONFIG_CREATED=true

    cat > "$CONFIG_FILE" <<EOF
{
  "prompt": $(echo "$GENERIC_PROMPT" | python3 -c 'import json, sys; print(json.dumps(sys.stdin.read()))'),
  "completion_file": "$PLAN_DOCUMENT",
  "completion_regex": "- \\\\[x\\\\] everything done",
  "max_iterations": $MAX_ITER,
  "project_path": "$PROJ_PATH",
  "wrapper_path": "scripts/claude_wrapper.py",
  "python_exec": ".venv/bin/python3",
  "circuit_breaker_threshold": 3,
  "require_git_changes": true
}
EOF

    echo -e "${GREEN}✓${NC} Plan document mode: $PLAN_DOCUMENT"
    echo -e "${GREEN}✓${NC} Generated temporary config: $CONFIG_FILE"
    echo ""

elif [[ "$SPEC_WORKFLOW_MODE" == false ]] && [[ "$FIRST_ARG" == *.json ]]; then
    # Config file mode
    CONFIG_FILE="$FIRST_ARG"

    if [ ! -f "$CONFIG_FILE" ]; then
        echo -e "${RED}❌ Config file not found: $CONFIG_FILE${NC}"
        exit 1
    fi

    echo -e "${GREEN}✓${NC} Config file: $CONFIG_FILE"
    echo ""

elif [[ "$SPEC_WORKFLOW_MODE" == false ]]; then
    echo -e "${RED}❌ Invalid argument: must be .md (plan document), .json (config file), or --spec-workflow${NC}"
    echo "Got: $FIRST_ARG"
    exit 1
fi

# ============================================================================
# STEP 1: PYTHON ENVIRONMENT DETECTION
# ============================================================================

echo -e "${BLUE}[1/3] Detecting Python environment...${NC}"

PYTHON_CMD=""

# Try project venv first (.venv)
if [ -f ".venv/bin/python3" ]; then
    PYTHON_CMD=".venv/bin/python3"
    echo -e "${GREEN}✓${NC} Using project venv: .venv/bin/python3"
elif [ -f "$HOME/.venv/air-executor/bin/python" ]; then
    PYTHON_CMD="$HOME/.venv/air-executor/bin/python"
    echo -e "${GREEN}✓${NC} Using configured venv: ~/.venv/air-executor"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    echo -e "${YELLOW}⚠${NC}  Using system Python: python3"
else
    echo -e "${RED}❌ No Python found${NC}"
    exit 1
fi

# Verify Python
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
echo -e "${GREEN}✓${NC} $PYTHON_VERSION"

export PYTHONPATH="$PROJECT_ROOT"
echo ""

# ============================================================================
# STEP 2: VALIDATE CONFIG FILE
# ============================================================================

echo -e "${BLUE}[2/3] Validating config file...${NC}"

# Parse JSON config to extract parameters
PROMPT=$($PYTHON_CMD -c "
import json
with open('$CONFIG_FILE') as f:
    config = json.load(f)
    print(config.get('prompt', ''))
" 2>/dev/null || echo "")

if [ -z "$PROMPT" ]; then
    echo -e "${RED}❌ Invalid config file or missing 'prompt' field${NC}"
    exit 1
fi

COMPLETION_FILE=$($PYTHON_CMD -c "
import json
with open('$CONFIG_FILE') as f:
    config = json.load(f)
    print(config.get('completion_file', ''))
" 2>/dev/null || echo "")

MAX_ITERATIONS=$($PYTHON_CMD -c "
import json
with open('$CONFIG_FILE') as f:
    config = json.load(f)
    print(config.get('max_iterations', 30))
" 2>/dev/null || echo "30")

CIRCUIT_BREAKER=$($PYTHON_CMD -c "
import json
with open('$CONFIG_FILE') as f:
    config = json.load(f)
    print(config.get('circuit_breaker_threshold', 3))
" 2>/dev/null || echo "3")

echo -e "${GREEN}✓${NC} Config valid"
echo -e "   Prompt: ${PROMPT:0:60}..."
echo -e "   Completion file: $COMPLETION_FILE"
echo -e "   Max iterations: $MAX_ITERATIONS"
echo -e "   Circuit breaker: $CIRCUIT_BREAKER iterations without progress"
if [ -n "$OVERRIDE_PROJECT_PATH" ]; then
    echo -e "   ${YELLOW}Project path override:${NC} $OVERRIDE_PROJECT_PATH"
fi
echo ""

# ============================================================================
# STEP 3: RUN ORCHESTRATOR
# ============================================================================

echo -e "${BLUE}[3/3] Starting orchestrator...${NC}"
echo ""
echo "================================================================================"
echo -e "${GREEN}🔁 Launching Simple Autonomous Iteration${NC}"
echo "================================================================================"
echo "Config:      $CONFIG_FILE"
echo "Python:      $PYTHON_CMD"
echo "Working Dir: $PROJECT_ROOT"
echo "Log File:    logs/wrapper-realtime.log"
echo "================================================================================"
echo ""
echo -e "${YELLOW}💡 Tip: Run ./scripts/monitor.sh in another terminal to watch progress${NC}"
echo ""

# Create logs directory
mkdir -p logs

# Clear previous log for fresh monitoring
> logs/wrapper-realtime.log

# Extract all parameters from JSON and pass to orchestrator
COMPLETION_REGEX=$($PYTHON_CMD -c "
import json
with open('$CONFIG_FILE') as f:
    config = json.load(f)
    print(config.get('completion_regex', '- \\\\[x\\\\] everything done'))
" 2>/dev/null || echo "- \\[x\\] everything done")

# Get project path - use override if provided, otherwise from config
if [ -n "$OVERRIDE_PROJECT_PATH" ] && [ "$TEMP_CONFIG_CREATED" != true ]; then
    PROJECT_PATH="$OVERRIDE_PROJECT_PATH"
    echo -e "${GREEN}✓${NC} Using override project path: $PROJECT_PATH"
else
    PROJECT_PATH=$($PYTHON_CMD -c "
import json
with open('$CONFIG_FILE') as f:
    config = json.load(f)
    print(config.get('project_path', '.'))
" 2>/dev/null || echo ".")
    if [ -n "$OVERRIDE_PROJECT_PATH" ] && [ "$TEMP_CONFIG_CREATED" = true ]; then
        echo -e "${GREEN}✓${NC} Using project path: $PROJECT_PATH (from argument)"
    else
        echo -e "${GREEN}✓${NC} Using project path: $PROJECT_PATH (from config)"
    fi
fi

WRAPPER_PATH=$($PYTHON_CMD -c "
import json
with open('$CONFIG_FILE') as f:
    config = json.load(f)
    print(config.get('wrapper_path', 'scripts/claude_wrapper.py'))
" 2>/dev/null || echo "scripts/claude_wrapper.py")

PYTHON_EXEC=$($PYTHON_CMD -c "
import json
with open('$CONFIG_FILE') as f:
    config = json.load(f)
    print(config.get('python_exec', '.venv/bin/python3'))
" 2>/dev/null || echo ".venv/bin/python3")

REQUIRE_GIT=$($PYTHON_CMD -c "
import json
with open('$CONFIG_FILE') as f:
    config = json.load(f)
    require = config.get('require_git_changes', True)
    print('1' if require else '0')
" 2>/dev/null || echo "1")

# Build command arguments
CMD_ARGS=(
    "--prompt" "$PROMPT"
    "--completion-file" "$COMPLETION_FILE"
    "--completion-regex" "$COMPLETION_REGEX"
    "--max-iterations" "$MAX_ITERATIONS"
    "--project-path" "$PROJECT_PATH"
    "--wrapper-path" "$WRAPPER_PATH"
    "--python-exec" "$PYTHON_EXEC"
    "--circuit-breaker-threshold" "$CIRCUIT_BREAKER"
)

# Add --no-git-check if require_git_changes is false
if [ "$REQUIRE_GIT" = "0" ]; then
    CMD_ARGS+=("--no-git-check")
fi

# Run the orchestrator
$PYTHON_CMD -u "$PROJECT_ROOT/airflow_dags/simple_autonomous_iteration/simple_orchestrator.py" "${CMD_ARGS[@]}"

# Capture exit code
EXIT_CODE=$?

# Cleanup temp config if created
if [ "$TEMP_CONFIG_CREATED" = true ]; then
    rm -f "$CONFIG_FILE"
fi

exit $EXIT_CODE
