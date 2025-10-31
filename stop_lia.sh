#!/bin/bash

# LIA Stop Script
# Stops both backend and frontend services

echo "=========================================="
echo "  Stopping LIA..."
echo "=========================================="

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if PID file exists
if [ -f /tmp/lia_pids.txt ]; then
    echo -e "${BLUE}📋 Found running processes...${NC}"
    PIDS=$(cat /tmp/lia_pids.txt)
    
    for PID in $PIDS; do
        if ps -p $PID > /dev/null 2>&1; then
            echo -e "${YELLOW}  Stopping PID: $PID${NC}"
            kill $PID 2>/dev/null
        fi
    done
    
    rm -f /tmp/lia_pids.txt
    echo -e "${GREEN}✓ Stopped processes from PID file${NC}"
fi

# Kill any remaining Python backend processes
if pgrep -f "python.*main.py" > /dev/null; then
    echo -e "${YELLOW}  Stopping backend processes...${NC}"
    pkill -f "python.*main.py"
    echo -e "${GREEN}✓ Backend stopped${NC}"
fi

# Kill any remaining Vite frontend processes
if pgrep -f "vite" > /dev/null; then
    echo -e "${YELLOW}  Stopping frontend processes...${NC}"
    pkill -f "vite"
    echo -e "${GREEN}✓ Frontend stopped${NC}"
fi

# Clean up log files (optional)
if [ "$1" == "--clean-logs" ]; then
    echo -e "${BLUE}🧹 Cleaning log files...${NC}"
    rm -f /tmp/lia_backend.log /tmp/lia_frontend.log
    echo -e "${GREEN}✓ Logs cleaned${NC}"
fi

echo ""
echo -e "${GREEN}✅ LIA stopped successfully${NC}"
echo ""


