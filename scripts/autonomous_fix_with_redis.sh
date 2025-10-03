#!/bin/bash
# Complete startup script for autonomous fixing
# Starts Redis, validates tools, and runs the orchestrator
#
# Usage:
#   ./scripts/start_autonomous_fixing.sh <project-config.yaml>
#
# Example:
#   ./scripts/start_autonomous_fixing.sh config/money-making-app.yaml

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
echo "🚀 Autonomous Fixing - Complete Startup"
echo "================================================================================"
echo -e "${NC}"

# ============================================================================
# ARGUMENT PARSING
# ============================================================================

if [ $# -lt 1 ]; then
    echo -e "${RED}❌ Missing config file${NC}"
    echo ""
    echo "Usage: $0 <config.yaml>"
    echo ""
    echo "Examples:"
    echo "  $0 config/money-making-app.yaml"
    echo "  $0 config/air-executor.yaml"
    echo ""
    exit 1
fi

CONFIG_FILE="$1"

if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}❌ Config file not found: $CONFIG_FILE${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Config file: $CONFIG_FILE"
echo ""

# ============================================================================
# STEP 1: CHECK REDIS
# ============================================================================

echo -e "${BLUE}[1/5] Checking Redis...${NC}"

if ! command -v redis-cli &> /dev/null; then
    echo -e "${RED}❌ Redis not installed${NC}"
    echo ""
    echo "Install with:"
    echo "  ./scripts/install_redis.sh"
    echo "  OR"
    echo "  sudo apt install redis-server"
    exit 1
fi

echo -e "${GREEN}✓${NC} Redis is installed"

# Check if Redis is running
if redis-cli ping &> /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Redis is already running"
else
    echo -e "${YELLOW}⚠${NC}  Redis is not running. Starting..."

    # Try to start Redis in background
    if command -v redis-server &> /dev/null; then
        # Start Redis in background (daemonized)
        redis-server --daemonize yes --port 6379 &> /dev/null || {
            echo -e "${RED}❌ Failed to start Redis${NC}"
            echo "   Try manually: redis-server --daemonize yes"
            exit 1
        }

        # Wait for Redis to be ready
        sleep 2

        if redis-cli ping &> /dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} Redis started successfully"
        else
            echo -e "${RED}❌ Redis failed to start${NC}"
            exit 1
        fi
    else
        echo -e "${RED}❌ redis-server command not found${NC}"
        exit 1
    fi
fi

echo ""

# ============================================================================
# STEP 2: PYTHON ENVIRONMENT DETECTION
# ============================================================================

echo -e "${BLUE}[2/5] Detecting Python environment...${NC}"

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
# STEP 3: VALIDATE REQUIRED PYTHON PACKAGES
# ============================================================================

echo -e "${BLUE}[3/5] Checking Python dependencies...${NC}"

REQUIRED_PACKAGES=("yaml" "redis")
MISSING_PACKAGES=()

for package in "${REQUIRED_PACKAGES[@]}"; do
    if $PYTHON_CMD -c "import $package" &> /dev/null; then
        echo -e "${GREEN}✓${NC} $package"
    else
        echo -e "${RED}✗${NC} $package (missing)"
        MISSING_PACKAGES+=("$package")
    fi
done

if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
    echo ""
    echo -e "${RED}❌ Missing packages: ${MISSING_PACKAGES[*]}${NC}"
    echo ""
    echo "Install with:"
    echo "  $PYTHON_CMD -m pip install pyyaml redis"
    exit 1
fi

echo ""

# ============================================================================
# STEP 4: VALIDATE TOOLS (LANGUAGE-SPECIFIC)
# ============================================================================

echo -e "${BLUE}[4/5] Validating language-specific tools...${NC}"

# Check what languages are enabled in config
LANGUAGES_ENABLED=$($PYTHON_CMD -c "
import yaml
with open('$CONFIG_FILE') as f:
    config = yaml.safe_load(f)
    languages = config.get('languages', {}).get('enabled', [])
    print(','.join(languages))
" 2>/dev/null || echo "")

if [ -z "$LANGUAGES_ENABLED" ]; then
    echo -e "${YELLOW}⚠${NC}  Could not detect enabled languages from config"
    LANGUAGES_ENABLED="python,flutter"  # defaults
fi

echo -e "   Enabled languages: ${LANGUAGES_ENABLED}"

# Validate based on languages
if [[ "$LANGUAGES_ENABLED" == *"flutter"* ]]; then
    if command -v flutter &> /dev/null; then
        FLUTTER_VERSION=$(flutter --version 2>&1 | head -1 | awk '{print $2}')
        echo -e "${GREEN}✓${NC} Flutter $FLUTTER_VERSION"
    else
        echo -e "${RED}✗${NC} Flutter (not found)"
        echo "   Install: ./scripts/install_flutter.sh"
    fi
fi

if [[ "$LANGUAGES_ENABLED" == *"python"* ]]; then
    if command -v pylint &> /dev/null; then
        echo -e "${GREEN}✓${NC} pylint"
    else
        echo -e "${YELLOW}⚠${NC}  pylint (optional)"
    fi
fi

echo ""

# ============================================================================
# STEP 5: RUN ORCHESTRATOR
# ============================================================================

echo -e "${BLUE}[5/5] Starting orchestrator...${NC}"
echo ""
echo "================================================================================"
echo -e "${GREEN}🚀 Launching Autonomous Fixing${NC}"
echo "================================================================================"
echo "Config:      $CONFIG_FILE"
echo "Python:      $PYTHON_CMD"
echo "Working Dir: $PROJECT_ROOT"
echo "Redis:       localhost:6379"
echo "================================================================================"
echo ""

# Create logs directory
mkdir -p logs

# Run the orchestrator
exec $PYTHON_CMD -u "$PROJECT_ROOT/run_orchestrator.py" "$CONFIG_FILE"
