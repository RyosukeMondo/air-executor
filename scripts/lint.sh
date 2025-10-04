#!/bin/bash
# Hybrid linting wrapper script

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
MODE="fast"
TARGET="airflow_dags/"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --full|--comprehensive)
            MODE="full"
            shift
            ;;
        --fast)
            MODE="fast"
            shift
            ;;
        --fix)
            FIX=true
            shift
            ;;
        *)
            TARGET="$1"
            shift
            ;;
    esac
done

# Activate virtual environment
source .venv/bin/activate

echo -e "${YELLOW}=== Linting: $TARGET ===${NC}\n"

if [ "$MODE" = "fast" ]; then
    echo -e "${GREEN}Running fast checks (ruff)...${NC}"
    if [ "$FIX" = true ]; then
        ruff check --fix "$TARGET"
    else
        ruff check "$TARGET"
    fi
    echo -e "${GREEN}✓ Fast checks complete${NC}"
else
    echo -e "${GREEN}Running fast checks (ruff)...${NC}"
    ruff check "$TARGET" || true

    echo -e "\n${GREEN}Running comprehensive checks (pylint)...${NC}"
    PYTHONPATH=. pylint "$TARGET" || true

    echo -e "\n${GREEN}✓ Comprehensive checks complete${NC}"
fi
