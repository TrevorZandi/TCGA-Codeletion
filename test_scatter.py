"""
Test script for deletion frequency scatter plot.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from data import processed_loader
from visualization import codeletion_heatmap

# Load data for PRAD
study_id = "prad_tcga_pan_can_atlas_2018"

print("Loading deletion frequencies...")
deletion_freqs = processed_loader.load_deletion_frequencies(
    chromosome="13",
    study_id=study_id
)

print(f"Loaded {len(deletion_freqs)} genes")
print(f"Deletion frequency range: {deletion_freqs.min():.3f} - {deletion_freqs.max():.3f}")
print(f"\nTop 10 most frequently deleted genes:")
print(deletion_freqs.sort_values(ascending=False).head(10))

print("\nLoading gene metadata...")
gene_metadata = processed_loader.load_gene_metadata(
    chromosome="13",
    study_id=study_id
)

print(f"Loaded metadata for {len(gene_metadata)} genes")

print("\nCreating scatter plot...")
fig = codeletion_heatmap.create_deletion_frequency_scatter(
    deletion_freqs=deletion_freqs,
    gene_metadata=gene_metadata
)

print("✓ Figure created successfully")
print(f"  Figure type: {type(fig)}")
print(f"  Data points: {len(fig.data[0].x)}")

# Save to test file
output_path = os.path.join("data", "processed", "test_deletion_scatter.html")
fig.write_html(output_path)
print(f"\n✓ Saved test plot to: {output_path}")
