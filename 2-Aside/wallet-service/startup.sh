#!/bin/bash
# Azure App Service startup script for Wallet Service

echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Starting application..."
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000
