#!/bin/bash
# Startup script for main.py ETL pipeline using .venv Python

cd "$(dirname "$0")"

# Activate virtual environment
source .venv/bin/activate

# Run the ETL pipeline
python main.py
