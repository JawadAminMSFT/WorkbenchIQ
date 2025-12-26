#!/bin/bash
# Azure App Service startup script for FastAPI

# Install dependencies
pip install -r requirements.txt

# Start the FastAPI application with Gunicorn and Uvicorn workers
# -w 2: Number of worker processes (adjust based on your App Service plan)
# -k uvicorn.workers.UvicornWorker: Use Uvicorn worker class for async support
# -b 0.0.0.0:8000: Bind to all interfaces on port 8000
# --timeout 600: Worker timeout in seconds
gunicorn -w 2 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 --timeout 600 api_server:app
