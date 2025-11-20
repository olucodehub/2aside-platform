#!/bin/bash
# Azure App Service startup script for User Service

# Install dependencies
pip install -r requirements.txt

# Run the application with gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000
