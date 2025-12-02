"""
Main workflow for chromosome co-deletion analysis.

This script orchestrates the complete analysis pipeline:
1. Query cBioPortal for CNA data
2. Build deletion matrix
3. Compute co-deletion frequencies
4. Generate visualizations and export results

Usage:
    python main.py [chromosome] [study_id]
    
Examples:
    python main.py                          # Default: chr13, PRAD
    python main.py 17                       # Chr17, PRAD
    python main.py 13 brca_tcga_pan_can_atlas_2018  # Chr13, BRCA
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from data import queries
from analysis import codeletion_calc
from visualization import codeletion_heatmap


def main():
    # Parse command-line arguments
    chromosome = sys.argv[1] if len(sys.argv) > 1 else "13"
    study_id = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Set up output directory
    output_dir = os.path.join(os.path.dirname(__file__), "data", "processed")
    os.makedirs(output_dir, exist_ok=True)
    
    # Step 1: Get study information
    print("=" * 60)
    print("Fetching study information...")
    print("=" * 60)
    
    study_id = queries.get_study_id(study_id)
    cna_profile_id = queries.get_cna_profile_id(study_id)
    sample_list_id = queries.get_cna_sample_list_id(study_id)
    
    print(f"Study: {study_id}")
    print(f"CNA profile: {cna_profile_id}")
    print(f"Sample list: {sample_list_id}")
    print(f"Chromosome: {chromosome}")
    
    # Step 2: Get chromosome genes
    print("\n" + "=" * 60)
    print(f"Fetching chromosome {chromosome} genes...")
    print("=" * 60)
    
    chr_genes = queries.get_chromosome_genes(chromosome)
    print(f"Found {len(chr_genes)} genes on chr{chromosome}")
    
    # Save gene metadata for Dash app
    chr_genes.to_excel(os.path.join(output_dir, f"chr{chromosome}_genes_metadata.xlsx"), index=False)
    print(f"Saved gene metadata with cytobands")
    
    # Step 3: Fetch CNA data
    print("\n" + "=" * 60)
    print("Fetching CNA data...")
    print("=" * 60)
    
    cna_data = queries.fetch_cna_for_genes(cna_profile_id, sample_list_id, chr_genes)
    print(f"Fetched {len(cna_data)} CNA calls")
    
    # Step 4: Build deletion matrix
    print("\n" + "=" * 60)
    print("Building deletion matrix...")
    print("=" * 60)
    
    deletion_mat = queries.build_deletion_matrix(cna_data, chr_genes, deletion_cutoff=-1)
    print(f"Matrix shape: {deletion_mat.shape} (samples x genes)")
    
    # Step 5: Extract specific genes of interest (optional example for chr13)
    if chromosome == "13":
        symbols = {"BRCA2", "PDS5B"}
        subset = queries.select_genes_by_symbol(deletion_mat, symbols)
        subset.to_excel(os.path.join(output_dir, f"chr{chromosome}_deletion_BRCA2_PDS5B.xlsx"), index=True)
        print(f"Saved subset for genes: {symbols}")
    
    # Step 6: Compute co-deletion frequencies
    print("\n" + "=" * 60)
    print("Computing co-deletion frequencies...")
    print("=" * 60)
    
    freq_matrix, freq_long, counts_df = codeletion_calc.compute_codeletion_frequency(deletion_mat)
    
    # Get top pairs
    top_pairs = codeletion_calc.get_top_codeleted_pairs(freq_long, n=20)
    print("\nTop 20 co-deleted pairs:")
    print(top_pairs.to_string(index=False))
    
    # Step 7: Export results
    print("\n" + "=" * 60)
    print("Exporting results...")
    print("=" * 60)
    
    # Only save top pairs to avoid Excel size limits (max 1,048,576 rows)
    all_pairs = freq_long.sort_values("co_deletion_frequency", ascending=False)
    max_pairs_to_save = min(100000, len(all_pairs))  # Save top 100k pairs or less
    top_pairs_to_save = all_pairs.head(max_pairs_to_save)
    top_pairs_to_save.to_excel(os.path.join(output_dir, f"chr{chromosome}_codeletion_frequencies.xlsx"), index=False)
    print(f"Saved: chr{chromosome}_codeletion_frequencies.xlsx (top {max_pairs_to_save:,} pairs)")
    if len(all_pairs) > max_pairs_to_save:
        print(f"  Note: Showing top {max_pairs_to_save:,} of {len(all_pairs):,} total pairs (Excel size limit)")
    
    # For large chromosomes, skip full matrix exports (too large for Excel)
    n_genes = freq_matrix.shape[0]
    if n_genes > 1000:
        print(f"  Skipping full matrix exports (chr{chromosome} has {n_genes:,} genes - too large for Excel)")
        print(f"  Note: Conditional matrix and deletion frequencies will still be saved")
    else:
        freq_matrix.to_excel(os.path.join(output_dir, f"chr{chromosome}_codeletion_matrix.xlsx"), index=True)
        print(f"Saved: chr{chromosome}_codeletion_matrix.xlsx")
        
        counts_df.to_excel(os.path.join(output_dir, f"chr{chromosome}_codeletion_counts.xlsx"), index=True)
        print(f"Saved: chr{chromosome}_codeletion_counts.xlsx")
    
    # Step 8: Compute conditional probabilities
    print("\n" + "=" * 60)
    print("Computing conditional co-deletion probabilities...")
    print("=" * 60)
    
    conditional = codeletion_calc.compute_conditional_codeletion(counts_df)
    conditional.to_excel(os.path.join(output_dir, f"chr{chromosome}_codeletion_conditional_frequencies.xlsx"), index=True)
    print(f"Saved: chr{chromosome}_codeletion_conditional_frequencies.xlsx")
    
    print("\nConditional frequencies (first 5 genes):")
    print(conditional.iloc[:5, :5])
    
    # Compute individual deletion frequencies
    deletion_freqs = codeletion_calc.compute_deletion_frequencies(deletion_mat)
    deletion_freqs.to_excel(os.path.join(output_dir, f"chr{chromosome}_deletion_frequencies.xlsx"), index=True)
    print(f"Saved: chr{chromosome}_deletion_frequencies.xlsx")
    
    # Step 9: Generate visualizations
    print("\n" + "=" * 60)
    print("Generating visualizations...")
    print("=" * 60)
    
    # Extract cytobands from chr_genes (already sorted by chromosomal position)
    cytobands = chr_genes["cytoband"].tolist()
    
    codeletion_heatmap.plot_heatmap(
        conditional, 
        title=f"Chr{chromosome} Conditional Co-Deletion Matrix",
        output_path=os.path.join(output_dir, f"chr{chromosome}_conditional_codeletion_heatmap.html"),
        cytobands=cytobands,
        n_labels=20
    )
    print(f"Saved: chr{chromosome}_conditional_codeletion_heatmap.html")
    
    print("\n" + "=" * 60)
    print("Analysis complete!")
    print("=" * 60)
    print(f"\nAll results saved to: {output_dir}")


if __name__ == "__main__":
    main()
