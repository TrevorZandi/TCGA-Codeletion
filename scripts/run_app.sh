#!/bin/bash
# Startup script for Dash application using .venv Python

cd "$(dirname "$0")/.."

# Activate virtual environment
source .venv/bin/activate

# Run the app
python src/app.py
