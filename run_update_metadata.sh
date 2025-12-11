#!/bin/bash
# Run the gene metadata update script

echo "Starting gene metadata update..."
echo "This will update all gene metadata files with genomic positions"
echo ""

python3 update_gene_metadata.py

echo ""
echo "Update complete!"
