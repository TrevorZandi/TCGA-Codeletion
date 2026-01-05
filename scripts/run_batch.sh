#!/bin/bash
# Batch processing script for all TCGA studies using .venv Python

cd "$(dirname "$0")/.."

# Activate virtual environment
source .venv/bin/activate

# Run the batch processing
echo "Starting batch processing of TCGA studies..."
echo "This may take a while depending on API response times and caching."
echo ""

python src/batch_process.py
