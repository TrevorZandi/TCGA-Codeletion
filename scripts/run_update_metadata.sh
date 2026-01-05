#!/bin/bash
# Run the gene metadata update script

cd "$(dirname "$0")/.."

echo "Starting gene metadata update..."
echo "This will update all gene metadata files with genomic positions"
echo ""

python3 scripts/update_gene_metadata.py

echo ""
echo "Update complete!"
