#!/bin/bash
# Run the Underwriting Assistant with Next.js frontend
# This script starts both the Python API server and the Next.js frontend

echo "================================================"
echo " Underwriting Assistant - Full Stack Launcher"
echo "================================================"
echo

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "Error: Please run this script from the project root directory"
    exit 1
fi

echo "Starting Python API server on port 8000..."
uv run python -m uvicorn api_server:app --reload --port 8000 &
API_PID=$!

echo "Waiting for API server to start..."
sleep 3

echo
echo "Starting Next.js frontend on port 3000..."
cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

echo
echo "================================================"
echo " Frontend: http://localhost:3000"
echo " API:      http://localhost:8000"
echo " API Docs: http://localhost:8000/docs"
echo "================================================"
echo

npm run dev

# Cleanup on exit
trap "kill $API_PID 2>/dev/null" EXIT
