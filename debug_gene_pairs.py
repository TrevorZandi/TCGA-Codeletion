#!/usr/bin/env python3
"""Debug script for gene pairs table."""

import os
os.environ['USE_S3'] = 'true'
os.environ['S3_BUCKET'] = 'tcga-codeletion-data'

from data import processed_loader
from visualization import codeletion_heatmap

study_id = 'brca_tcga_pan_can_atlas_2018'
chromosome = '13'

print(f"Testing gene pairs table for {study_id}, chromosome {chromosome}")
print("=" * 60)

# Load all required data
print("\n1. Loading conditional matrix...")
conditional_matrix = processed_loader.load_conditional_matrix(
    chromosome=chromosome,
    study_id=study_id
)
print(f"   ✓ Shape: {conditional_matrix.shape}")
print(f"   ✓ Type: {type(conditional_matrix)}")
print(f"   ✓ Columns (first 3): {conditional_matrix.columns[:3].tolist()}")

print("\n2. Loading deletion frequencies...")
deletion_freqs = processed_loader.load_deletion_frequencies(
    chromosome=chromosome,
    study_id=study_id
)
print(f"   ✓ Type: {type(deletion_freqs)}")
print(f"   ✓ Length: {len(deletion_freqs)}")
if hasattr(deletion_freqs, 'head'):
    print(f"   ✓ First 3 entries: {deletion_freqs.head(3).to_dict()}")
else:
    print(f"   ✓ First 3 entries: {dict(list(deletion_freqs.items())[:3])}")

print("\n3. Loading joint data (codeletion pairs)...")
joint_data = processed_loader.load_codeletion_pairs(
    chromosome=chromosome,
    study_id=study_id
)
print(f"   ✓ Type: {type(joint_data)}")
if joint_data is not None:
    print(f"   ✓ Shape: {joint_data.shape}")
    print(f"   ✓ Columns: {joint_data.columns.tolist()}")
    if len(joint_data) > 0:
        print(f"   ✓ First row: {joint_data.iloc[0].to_dict()}")
else:
    print("   ✗ Joint data is None!")

print("\n4. Loading gene metadata...")
gene_metadata = processed_loader.load_gene_metadata(
    chromosome=chromosome,
    study_id=study_id
)
print(f"   ✓ Type: {type(gene_metadata)}")
if gene_metadata is not None:
    print(f"   ✓ Shape: {gene_metadata.shape}")
    print(f"   ✓ Columns: {gene_metadata.columns.tolist()}")
    if len(gene_metadata) > 0:
        print(f"   ✓ First gene: {gene_metadata.iloc[0].to_dict()}")
else:
    print("   ✗ Gene metadata is None!")

print("\n5. Creating gene pairs table...")
try:
    table = codeletion_heatmap.create_top_pairs_table_data(
        conditional_matrix=conditional_matrix,
        deletion_freqs=deletion_freqs,
        joint_data=joint_data,
        gene_metadata=gene_metadata,
        n=10
    )
    print(f"   ✓ Table created successfully!")
    print(f"   ✓ Table type: {type(table)}")
    
    # Check if it's a DataTable with data
    if hasattr(table, 'data'):
        print(f"   ✓ Table has 'data' attribute: {len(table.data)} rows")
    elif hasattr(table, 'children'):
        print(f"   ✓ Table has 'children' attribute: {table.children}")
    else:
        print(f"   ✓ Table attributes: {dir(table)}")
        
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Debug complete!")
