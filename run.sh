#!/bin/bash

# LIA Run Script
# This script starts both backend and frontend in separate terminals

set -e

echo "================================"
echo "LIA - Local Intelligent Agent"
echo "Starting Application"
echo "================================"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Check if setup has been run
if [ ! -d "backend/venv" ]; then
    echo -e "${RED}Backend not set up. Running setup first...${NC}"
    ./setup.sh
fi

if [ ! -d "frontend/node_modules" ]; then
    echo -e "${RED}Frontend not set up. Running setup first...${NC}"
    ./setup.sh
fi

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${RED}Warning: Ollama is not running on port 11434${NC}"
    echo "Please start Ollama in another terminal:"
    echo "  ollama serve"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo -e "${GREEN}Starting LIA...${NC}"
echo ""

# Get the current directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check which terminal emulator is available
if command -v gnome-terminal &> /dev/null; then
    TERMINAL="gnome-terminal"
elif command -v xterm &> /dev/null; then
    TERMINAL="xterm"
elif command -v konsole &> /dev/null; then
    TERMINAL="konsole"
else
    echo -e "${RED}No supported terminal found. Please run manually:${NC}"
    echo ""
    echo "Terminal 1: cd backend && source venv/bin/activate && python main.py"
    echo "Terminal 2: cd frontend && npm run dev"
    exit 1
fi

# Start backend in new terminal
echo -e "${BLUE}Starting backend...${NC}"
if [ "$TERMINAL" = "gnome-terminal" ]; then
    gnome-terminal -- bash -c "cd $DIR/backend && source venv/bin/activate && python main.py; exec bash"
elif [ "$TERMINAL" = "xterm" ]; then
    xterm -e "cd $DIR/backend && source venv/bin/activate && python main.py; bash" &
elif [ "$TERMINAL" = "konsole" ]; then
    konsole -e "cd $DIR/backend && source venv/bin/activate && python main.py; bash" &
fi

# Wait a moment for backend to start
sleep 2

# Start frontend in new terminal
echo -e "${BLUE}Starting frontend...${NC}"
if [ "$TERMINAL" = "gnome-terminal" ]; then
    gnome-terminal -- bash -c "cd $DIR/frontend && npm run dev; exec bash"
elif [ "$TERMINAL" = "xterm" ]; then
    xterm -e "cd $DIR/frontend && npm run dev; bash" &
elif [ "$TERMINAL" = "konsole" ]; then
    konsole -e "cd $DIR/frontend && npm run dev; bash" &
fi

echo ""
echo -e "${GREEN}LIA is starting!${NC}"
echo ""
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo ""
echo "The application will open in new terminal windows."
echo "To stop, close the terminal windows or press Ctrl+C in each."

