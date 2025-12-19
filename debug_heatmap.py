#!/usr/bin/env python3
"""
Debug script to test the heatmap visualization.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from data import processed_loader
from visualization import codeletion_heatmap

# Test with BRCA, chr13
study_id = 'brca_tcga_pan_can_atlas_2018'
chromosome = '13'

print(f"Testing heatmap for {study_id}, chromosome {chromosome}")
print("=" * 60)

try:
    print("\n1. Loading conditional matrix...")
    conditional_matrix = processed_loader.load_conditional_matrix(
        chromosome=chromosome,
        study_id=study_id
    )
    print(f"   ✓ Shape: {conditional_matrix.shape}")
    print(f"   ✓ Type: {type(conditional_matrix)}")
    print(f"   ✓ Columns (first 5): {conditional_matrix.columns.tolist()[:5]}")
    print(f"   ✓ Has NaN values: {conditional_matrix.isna().any().any()}")
    print(f"   ✓ Value range: {conditional_matrix.min().min():.3f} to {conditional_matrix.max().max():.3f}")

    print("\n2. Loading gene metadata...")
    gene_metadata = processed_loader.load_gene_metadata(
        chromosome=chromosome,
        study_id=study_id
    )
    print(f"   ✓ Shape: {gene_metadata.shape}")
    print(f"   ✓ Type: {type(gene_metadata)}")
    print(f"   ✓ Columns: {gene_metadata.columns.tolist()}")
    print(f"   ✓ First gene: {gene_metadata.iloc[0].to_dict()}")

    print("\n3. Creating heatmap figure...")
    print(f"   Parameters:")
    print(f"     - mat shape: {conditional_matrix.shape}")
    print(f"     - colorscale: Viridis")
    print(f"     - n_labels: 20")
    print(f"     - cytobands type: {type(gene_metadata)}")
    
    fig = codeletion_heatmap.create_heatmap_figure(
        mat=conditional_matrix,
        colorscale='Viridis',
        n_labels=20,
        cytobands=gene_metadata
    )
    
    print(f"   ✓ Figure created successfully")
    print(f"   ✓ Figure type: {type(fig)}")
    print(f"   ✓ Number of data traces: {len(fig.data)}")
    
    if len(fig.data) > 0:
        heatmap_data = fig.data[0]
        print(f"   ✓ Heatmap data type: {type(heatmap_data)}")
        print(f"   ✓ Heatmap z shape: {heatmap_data.z.shape if hasattr(heatmap_data, 'z') else 'N/A'}")
        print(f"   ✓ Heatmap colorscale: {heatmap_data.colorscale if hasattr(heatmap_data, 'colorscale') else 'N/A'}")
    
    # Check layout
    if hasattr(fig, 'layout'):
        print(f"   ✓ Layout title: {fig.layout.title.text if hasattr(fig.layout, 'title') else 'N/A'}")
        print(f"   ✓ Layout xaxis: {hasattr(fig.layout, 'xaxis')}")
        print(f"   ✓ Layout yaxis: {hasattr(fig.layout, 'yaxis')}")
    
    print("\n4. Testing with correct parameters (gene_metadata as list)...")
    
    # The function expects cytobands as a list, not a DataFrame
    # Let's check what gene_metadata is
    if isinstance(gene_metadata, pd.DataFrame):
        print("   ⚠ gene_metadata is a DataFrame, but function expects a list!")
        print("   Converting to list of gene symbols...")
        
        if 'hugoGeneSymbol' in gene_metadata.columns:
            gene_list = gene_metadata['hugoGeneSymbol'].tolist()
            print(f"   ✓ Extracted {len(gene_list)} gene symbols")
            print(f"   ✓ First 5 genes: {gene_list[:5]}")
            
            # Try creating heatmap with gene list
            fig2 = codeletion_heatmap.create_heatmap_figure(
                mat=conditional_matrix,
                colorscale='Viridis',
                n_labels=20,
                cytobands=gene_list
            )
            print(f"   ✓ Figure with gene list created successfully")
        else:
            print(f"   ✗ No 'hugoGeneSymbol' column in gene_metadata")
            print(f"   Available columns: {gene_metadata.columns.tolist()}")

except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Debug complete!")
