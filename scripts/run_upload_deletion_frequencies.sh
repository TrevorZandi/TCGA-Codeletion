#!/bin/bash
# Upload missing deletion frequency files to S3

cd "$(dirname "$0")/.."

echo "Starting upload of deletion frequency files to S3..."
echo ""

# Test mode - process only chr13 for 2 studies
if [ "$1" == "--test" ]; then
    echo "TEST MODE: Processing chr13 for test studies only"
    python3 scripts/upload_deletion_frequencies.py --test "$@"
# Single study mode
elif [ "$1" == "--study" ]; then
    echo "Single study mode: $2"
    python3 scripts/upload_deletion_frequencies.py "$@"
# Full mode
else
    echo "FULL MODE: Processing all 24 chromosomes for 32 studies"
    echo "This will take several hours..."
    echo ""
    read -p "Continue? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        python3 upload_deletion_frequencies.py "$@"
    else
        echo "Cancelled"
        exit 1
    fi
fi
