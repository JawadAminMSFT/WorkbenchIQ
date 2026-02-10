#!/bin/bash
# Azure App Service startup script for FastAPI

# Use PORT environment variable set by Azure, default to 8000
PORT="${PORT:-8000}"

# Start the FastAPI application with Gunicorn and Uvicorn workers
# -w 2: Number of worker processes (adjust based on your App Service plan)
# -k uvicorn.workers.UvicornWorker: Use Uvicorn worker class for async support
# -b 0.0.0.0:$PORT: Bind to all interfaces on the Azure-assigned port
# --timeout 600: Worker timeout in seconds
gunicorn -w 2 -k uvicorn.workers.UvicornWorker -b "0.0.0.0:$PORT" --timeout 600 api_server:app
