@echo off
REM Run the Underwriting Assistant with Next.js frontend
REM This script starts both the Python API server and the Next.js frontend

echo ================================================
echo  Underwriting Assistant - Full Stack Launcher
echo ================================================
echo.

REM Check if we're in the right directory
if not exist "pyproject.toml" (
    echo Error: Please run this script from the project root directory
    exit /b 1
)

echo Starting Python API server on port 8000...
start "API Server" cmd /c "uv run python -m uvicorn api_server:app --reload --port 8000"

echo Waiting for API server to start...
timeout /t 3 /nobreak > nul

echo.
echo Starting Next.js frontend on port 3000...
cd frontend

REM Check if node_modules exists
if not exist "node_modules" (
    echo Installing frontend dependencies...
    call npm install
)

echo.
echo ================================================
echo  Frontend: http://localhost:3000
echo  API:      http://localhost:8000
echo  API Docs: http://localhost:8000/docs
echo ================================================
echo.

call npm run dev
