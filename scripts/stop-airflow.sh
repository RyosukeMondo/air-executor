#!/bin/bash
# Stop Airflow standalone gracefully

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}🛑 Stopping Airflow...${NC}"

# Check if Airflow is running on port 8080
if ! lsof -Pi :8080 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${YELLOW}⚠️  Airflow is not running on port 8080${NC}"
    exit 0
fi

# Get PIDs of Airflow processes
AIRFLOW_PIDS=$(pgrep -f "airflow" || true)

if [ -z "$AIRFLOW_PIDS" ]; then
    echo -e "${YELLOW}⚠️  No Airflow processes found${NC}"
    exit 0
fi

echo -e "${YELLOW}📤 Found Airflow processes: $AIRFLOW_PIDS${NC}"
echo -e "${YELLOW}📤 Sending SIGTERM for graceful shutdown...${NC}"

# Send SIGTERM to all Airflow processes
for pid in $AIRFLOW_PIDS; do
    kill -TERM $pid 2>/dev/null || true
done

# Wait for graceful shutdown (max 30 seconds)
echo -e "${YELLOW}⏳ Waiting for graceful shutdown...${NC}"
for i in {1..30}; do
    # Check if any Airflow processes are still running
    if ! pgrep -f "airflow" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Airflow stopped cleanly${NC}"
        exit 0
    fi
    sleep 1
done

# Still running, force kill
echo -e "${YELLOW}⚠️  Processes did not stop gracefully${NC}"
echo -e "${YELLOW}🔨 Sending SIGKILL...${NC}"

for pid in $AIRFLOW_PIDS; do
    kill -9 $pid 2>/dev/null || true
done

sleep 2

if ! pgrep -f "airflow" >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Airflow stopped (forced)${NC}"
else
    echo -e "${RED}❌ Some Airflow processes may still be running${NC}"
    echo -e "${YELLOW}💡 You may need to manually kill:${NC}"
    pgrep -f "airflow" | while read pid; do
        echo -e "   kill -9 $pid"
    done
    exit 1
fi
