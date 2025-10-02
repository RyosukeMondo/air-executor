#!/bin/bash
# Start Airflow in standalone mode

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🚀 Starting Airflow Standalone...${NC}"
echo ""

# Activate virtual environment
source .venv/bin/activate

# Check if Airflow is already running
if lsof -Pi :8080 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${YELLOW}⚠️  Airflow is already running on port 8080${NC}"
    echo ""
    echo "Access at: http://localhost:8080"
    echo "Username: admin"
    echo "Password: (see ~/airflow/simple_auth_manager_passwords.json.generated)"
    exit 0
fi

# Start Airflow
echo "Starting Airflow components..."
echo "  - Webserver (port 8080)"
echo "  - Scheduler"
echo "  - Triggerer"
echo ""

airflow standalone

# Note: This runs in foreground. Press Ctrl+C to stop.
