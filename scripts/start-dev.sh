#!/bin/bash
# Start Air-Executor in development mode

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Air-Executor in development mode...${NC}"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment not found!${NC}"
    echo -e "${YELLOW}   Run ./setup-dev.sh first${NC}"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if already running
if [ -f ".air-executor/manager.pid" ]; then
    PID=$(cat .air-executor/manager.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Air-Executor is already running (PID: $PID)${NC}"
        echo -e "${YELLOW}   Run ./stop-dev.sh to stop it first${NC}"
        exit 1
    else
        echo -e "${YELLOW}⚠️  Found stale PID file, cleaning up...${NC}"
        rm .air-executor/manager.pid
    fi
fi

# Start job manager in foreground with output
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✨ Air-Executor Job Manager${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}📋 Configuration:${NC}"
echo -e "   Config: .air-executor/config.yaml"
echo -e "   Jobs: .air-executor/jobs/"
echo -e "   Logs: .air-executor/manager.log"
echo ""
echo -e "${BLUE}🎮 Controls:${NC}"
echo -e "   Press Ctrl+C to stop"
echo ""
echo -e "${BLUE}💡 Tips:${NC}"
echo -e "   • Open another terminal and run: source venv/bin/activate"
echo -e "   • Then check status: python -m air_executor.cli.main status"
echo -e "   • View logs: tail -f .air-executor/manager.log"
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Start directly with Python using run_manager.py
exec python run_manager.py 2>&1 | tee .air-executor/manager.log
