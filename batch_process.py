"""
Batch processing script for computing chromosome 13 co-deletions across multiple TCGA studies.

This script reads study IDs from data/curated_data/TCGA_study_names.csv and processes
each study to generate pre-computed co-deletion matrices for the Dash application.
"""

import os
import sys
import pandas as pd
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from data import queries, cbioportal_client
from analysis import codeletion_calc
from visualization import codeletion_heatmap


def process_study(study_id, output_dir, chromosome="13"):
    """
    Process a single study to compute chromosome co-deletions.
    
    Args:
        study_id: Study identifier (e.g., 'prad_tcga_pan_can_atlas_2018')
        output_dir: Directory to save processed results
        chromosome: Chromosome number (default: "13")
        
    Returns:
        Dictionary with processing results and statistics
    """
    print(f"\n{'='*70}")
    print(f"Processing: {study_id}")
    print(f"{'='*70}")
    
    results = {
        'study_id': study_id,
        'success': False,
        'n_genes': 0,
        'n_samples': 0,
        'n_deletions': 0,
        'error': None
    }
    
    try:
        # Step 1: Get CNA profile and sample list
        print(f"[1/6] Fetching study metadata...")
        cna_profile_id = queries.get_cna_profile_id(study_id)
        sample_list_id = queries.get_cna_sample_list_id(study_id)
        print(f"  CNA profile: {cna_profile_id}")
        print(f"  Sample list: {sample_list_id}")
        
        # Step 2: Get chromosome genes
        print(f"[2/6] Fetching chromosome {chromosome} genes...")
        chr_genes = queries.get_chromosome_genes(chromosome)
        results['n_genes'] = len(chr_genes)
        print(f"  Found {len(chr_genes)} genes on chr{chromosome}")
        
        # Step 3: Fetch CNA data
        print(f"[3/6] Fetching CNA data...")
        cna_data = queries.fetch_cna_for_genes(cna_profile_id, sample_list_id, chr_genes)
        results['n_deletions'] = len(cna_data)
        print(f"  Fetched {len(cna_data)} CNA calls")
        
        # Step 4: Build deletion matrix
        print(f"[4/6] Building deletion matrix...")
        deletion_mat = queries.build_deletion_matrix(cna_data, chr_genes, deletion_cutoff=-1)
        results['n_samples'] = deletion_mat.shape[0]
        print(f"  Matrix shape: {deletion_mat.shape} (samples x genes)")
        
        # Skip if no samples or very few deletions
        if deletion_mat.shape[0] < 10:
            results['error'] = f"Too few samples: {deletion_mat.shape[0]}"
            print(f"  ⚠ Skipping: {results['error']}")
            return results
        
        # Step 5: Compute co-deletion statistics
        print(f"[5/6] Computing co-deletion statistics...")
        freq_matrix, freq_long, counts_df = codeletion_calc.compute_codeletion_frequency(deletion_mat)
        conditional = codeletion_calc.compute_conditional_codeletion(counts_df)
        deletion_freqs = codeletion_calc.compute_deletion_frequencies(deletion_mat)
        
        # Step 6: Export results
        print(f"[6/6] Exporting results...")
        study_output_dir = os.path.join(output_dir, study_id)
        os.makedirs(study_output_dir, exist_ok=True)
        
        # Save gene metadata
        chr_genes.to_excel(
            os.path.join(study_output_dir, f"chr{chromosome}_genes_metadata.xlsx"),
            index=False
        )
        
        # Save matrices
        conditional.to_excel(
            os.path.join(study_output_dir, f"chr{chromosome}_codeletion_conditional_frequencies.xlsx"),
            index=True
        )
        
        freq_matrix.to_excel(
            os.path.join(study_output_dir, f"chr{chromosome}_codeletion_matrix.xlsx"),
            index=True
        )
        
        counts_df.to_excel(
            os.path.join(study_output_dir, f"chr{chromosome}_codeletion_counts.xlsx"),
            index=True
        )
        
        freq_long.to_excel(
            os.path.join(study_output_dir, f"chr{chromosome}_codeletion_frequencies.xlsx"),
            index=False
        )
        
        deletion_freqs.to_excel(
            os.path.join(study_output_dir, f"chr{chromosome}_deletion_frequencies.xlsx"),
            index=True
        )
        
        # Generate standalone heatmap
        cytobands = chr_genes["cytoband"].tolist()
        codeletion_heatmap.plot_heatmap(
            conditional,
            title=f"Chr{chromosome} Conditional Co-Deletion: {study_id}",
            output_path=os.path.join(study_output_dir, f"chr{chromosome}_conditional_codeletion_heatmap.html"),
            cytobands=cytobands,
            n_labels=20
        )
        
        results['success'] = True
        print(f"  ✓ Successfully processed {study_id}")
        print(f"  ✓ Results saved to: {study_output_dir}")
        
    except Exception as e:
        results['error'] = str(e)
        print(f"  ✗ Error processing {study_id}: {e}")
    
    return results


def main():
    """
    Main batch processing workflow.
    """
    # Set up paths
    script_dir = os.path.dirname(__file__)
    
    # Allow command-line argument for test file
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        study_list_path = os.path.join(script_dir, "data", "curated_data", "test_studies.csv")
        print("** TEST MODE: Using test_studies.csv **\n")
    else:
        study_list_path = os.path.join(script_dir, "data", "curated_data", "TCGA_study_names.csv")
    
    output_dir = os.path.join(script_dir, "data", "processed")
    
    # Read study list
    print("="*70)
    print("TCGA Batch Co-Deletion Analysis")
    print("="*70)
    print(f"\nReading study list from: {study_list_path}")
    
    if not os.path.exists(study_list_path):
        print(f"Error: Study list not found at {study_list_path}")
        sys.exit(1)
    
    study_df = pd.read_csv(study_list_path)
    study_ids = study_df['TCGA_study'].tolist()
    
    print(f"Found {len(study_ids)} studies to process:")
    for i, study_id in enumerate(study_ids, 1):
        print(f"  {i:2d}. {study_id}")
    
    # Process each study
    results_list = []
    for i, study_id in enumerate(study_ids, 1):
        print(f"\n\n{'#'*70}")
        print(f"# Study {i}/{len(study_ids)}")
        print(f"{'#'*70}")
        
        result = process_study(study_id, output_dir, chromosome="13")
        results_list.append(result)
    
    # Summary
    print("\n\n" + "="*70)
    print("PROCESSING SUMMARY")
    print("="*70)
    
    successful = [r for r in results_list if r['success']]
    failed = [r for r in results_list if not r['success']]
    
    print(f"\nTotal studies processed: {len(study_ids)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    
    if successful:
        print("\n✓ Successfully processed studies:")
        for r in successful:
            print(f"  - {r['study_id']:45s} | {r['n_samples']:4d} samples | {r['n_genes']:4d} genes | {r['n_deletions']:6d} deletions")
    
    if failed:
        print("\n✗ Failed studies:")
        for r in failed:
            print(f"  - {r['study_id']:45s} | Error: {r['error']}")
    
    # Save summary report
    summary_df = pd.DataFrame(results_list)
    summary_path = os.path.join(output_dir, "processing_summary.xlsx")
    summary_df.to_excel(summary_path, index=False)
    print(f"\n✓ Summary report saved to: {summary_path}")
    
    print("\n" + "="*70)
    print("Batch processing complete!")
    print("="*70)


if __name__ == "__main__":
    main()
