#!/bin/bash
# Stop Air-Executor gracefully

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}🛑 Stopping Air-Executor...${NC}"

# Check if PID file exists
if [ ! -f ".air-executor/manager.pid" ]; then
    echo -e "${YELLOW}⚠️  No PID file found${NC}"
    echo -e "${YELLOW}   Air-Executor is not running (or not started with ./start-dev.sh)${NC}"
    exit 0
fi

# Read PID
PID=$(cat .air-executor/manager.pid)

# Check if process exists
if ! ps -p $PID > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Process not found (PID: $PID)${NC}"
    echo -e "${YELLOW}   Cleaning up stale PID file...${NC}"
    rm .air-executor/manager.pid
    exit 0
fi

# Send SIGTERM
echo -e "${YELLOW}📤 Sending SIGTERM to process $PID...${NC}"
kill -TERM $PID

# Wait for graceful shutdown (max 15 seconds)
echo -e "${YELLOW}⏳ Waiting for graceful shutdown...${NC}"
for i in {1..15}; do
    if ! ps -p $PID > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Air-Executor stopped cleanly${NC}"
        rm -f .air-executor/manager.pid
        exit 0
    fi
    sleep 1
done

# Still running, force kill
echo -e "${YELLOW}⚠️  Process did not stop gracefully${NC}"
echo -e "${YELLOW}🔨 Sending SIGKILL...${NC}"
kill -9 $PID

sleep 1

if ! ps -p $PID > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Air-Executor stopped (forced)${NC}"
    rm -f .air-executor/manager.pid
else
    echo -e "${RED}❌ Failed to stop process $PID${NC}"
    exit 1
fi
