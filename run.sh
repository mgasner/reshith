#!/bin/bash

# Reshith Development Runner
# Runs both backend and frontend with hot-reloading
#
# Usage:
#   ./run.sh          - Start both frontend and backend
#   ./run.sh backend  - Start only the backend
#   ./run.sh frontend - Start only the frontend
#   ./run.sh test     - Run all tests

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

cleanup() {
    echo ""
    echo "Shutting down..."
    [ -n "$BACKEND_PID" ] && kill $BACKEND_PID 2>/dev/null || true
    [ -n "$FRONTEND_PID" ] && kill $FRONTEND_PID 2>/dev/null || true
    exit 0
}

check_dependencies() {
    local missing=0
    
    if ! command -v uv &> /dev/null; then
        echo -e "${RED}Error: 'uv' is not installed.${NC}"
        echo "Install it with: curl -LsSf https://astral.sh/uv/install.sh | sh"
        missing=1
    fi
    
    if ! command -v node &> /dev/null; then
        echo -e "${RED}Error: 'node' is not installed.${NC}"
        echo "Install it from: https://nodejs.org/"
        missing=1
    fi
    
    if [ $missing -eq 1 ]; then
        exit 1
    fi
}

start_backend() {
    echo -e "${GREEN}Starting backend (FastAPI + Strawberry GraphQL)...${NC}"
    cd "$SCRIPT_DIR/backend"
    uv run uvicorn reshith.main:app --reload --host 0.0.0.0 --port 8000
}

start_frontend() {
    echo -e "${GREEN}Starting frontend (Vite + React)...${NC}"
    cd "$SCRIPT_DIR/frontend"
    npm run dev
}

run_tests() {
    echo -e "${GREEN}Running backend tests...${NC}"
    cd "$SCRIPT_DIR/backend"
    uv run pytest tests/ -v
    
    echo ""
    echo -e "${GREEN}Running backend linting...${NC}"
    uv run ruff check reshith/ tests/
    
    echo ""
    echo -e "${GREEN}All tests passed!${NC}"
}

start_both() {
    trap cleanup SIGINT SIGTERM

    echo -e "${GREEN}Starting Reshith development servers...${NC}"
    echo ""

    # Start backend
    echo -e "${YELLOW}Starting backend (FastAPI + Strawberry GraphQL)...${NC}"
    cd "$SCRIPT_DIR/backend"
    uv run uvicorn reshith.main:app --reload --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!

    # Give backend a moment to start
    sleep 2

    # Start frontend
    echo -e "${YELLOW}Starting frontend (Vite + React)...${NC}"
    cd "$SCRIPT_DIR/frontend"
    npm run dev &
    FRONTEND_PID=$!

    echo ""
    echo "=========================================="
    echo -e "${GREEN}Reshith is running!${NC}"
    echo ""
    echo "  Frontend: http://localhost:5173"
    echo "  Backend:  http://localhost:8000"
    echo "  GraphQL:  http://localhost:8000/graphql"
    echo ""
    echo "Press Ctrl+C to stop both servers"
    echo "=========================================="
    echo ""

    wait
}

# Main
case "${1:-}" in
    backend)
        check_dependencies
        start_backend
        ;;
    frontend)
        check_dependencies
        start_frontend
        ;;
    test)
        check_dependencies
        run_tests
        ;;
    help|--help|-h)
        echo "Reshith Development Runner"
        echo ""
        echo "Usage:"
        echo "  ./run.sh          - Start both frontend and backend"
        echo "  ./run.sh backend  - Start only the backend"
        echo "  ./run.sh frontend - Start only the frontend"
        echo "  ./run.sh test     - Run all tests"
        echo "  ./run.sh help     - Show this help message"
        ;;
    *)
        check_dependencies
        start_both
        ;;
esac
