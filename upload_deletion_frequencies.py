"""
Script to generate and upload missing deletion frequency files to S3.

This script processes all studies and chromosomes to generate individual gene
deletion frequency files that are missing from S3.
"""

import os
import sys
import boto3
import pandas as pd
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from data import queries, cbioportal_client
from analysis import codeletion_calc


def check_file_exists_s3(s3_client, bucket, key):
    """Check if a file exists in S3."""
    try:
        s3_client.head_object(Bucket=bucket, Key=key)
        return True
    except:
        return False


def upload_deletion_frequencies(study_id, chromosome, s3_bucket='tcga-codeletion-data', dry_run=False):
    """
    Generate and upload deletion frequency file for a study/chromosome.
    
    Args:
        study_id: Study identifier
        chromosome: Chromosome number
        s3_bucket: S3 bucket name
        dry_run: If True, don't actually upload
        
    Returns:
        True if successful, False otherwise
    """
    s3_key = f"processed/{study_id}/chr{chromosome}_deletion_frequencies.xlsx"
    
    # Check if file already exists
    s3 = boto3.client('s3')
    if check_file_exists_s3(s3, s3_bucket, s3_key):
        print(f"  ✓ Already exists: {s3_key}")
        return True
    
    try:
        print(f"  📥 Fetching data from cBioPortal...")
        
        # Get CNA profile and sample list
        cna_profile_id = queries.get_cna_profile_id(study_id)
        sample_list_id = queries.get_cna_sample_list_id(study_id)
        
        # Get chromosome genes
        chr_genes = queries.get_chromosome_genes(chromosome)
        print(f"     Found {len(chr_genes)} genes on chr{chromosome}")
        
        # Fetch CNA data
        cna_data = queries.fetch_cna_for_genes(cna_profile_id, sample_list_id, chr_genes)
        print(f"     Fetched {len(cna_data)} CNA calls")
        
        # Build deletion matrix
        deletion_mat = queries.build_deletion_matrix(cna_data, chr_genes, deletion_cutoff=-1)
        print(f"     Matrix shape: {deletion_mat.shape} (samples x genes)")
        
        # Calculate deletion frequencies
        deletion_freqs = codeletion_calc.compute_deletion_frequencies(deletion_mat)
        
        if dry_run:
            print(f"  [DRY RUN] Would upload: {s3_key}")
            print(f"     Deletion frequency range: {deletion_freqs.min():.4f} to {deletion_freqs.max():.4f}")
            return True
        
        # Save to temporary file
        temp_file = f"/tmp/chr{chromosome}_deletion_frequencies.xlsx"
        deletion_freqs.to_excel(temp_file, index=True)
        
        # Upload to S3
        s3.upload_file(temp_file, s3_bucket, s3_key)
        print(f"  ✓ Uploaded: {s3_key}")
        
        # Cleanup
        os.remove(temp_file)
        
        return True
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def main():
    """Main execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Upload deletion frequency files to S3')
    parser.add_argument('--bucket', default='tcga-codeletion-data', help='S3 bucket name')
    parser.add_argument('--dry-run', action='store_true', help='Dry run (do not upload)')
    parser.add_argument('--study', help='Process single study only')
    parser.add_argument('--chromosome', help='Process single chromosome only')
    parser.add_argument('--test', action='store_true', help='Test mode (chr13, 2 studies)')
    
    args = parser.parse_args()
    
    # Define chromosomes to process
    if args.chromosome:
        chromosomes = [args.chromosome]
    elif args.test:
        chromosomes = ['13']
    else:
        chromosomes = [str(i) for i in range(1, 23)] + ['X', 'Y']
    
    # Define studies to process
    if args.study:
        study_ids = [args.study]
    elif args.test:
        # Use test studies
        test_csv = os.path.join(os.path.dirname(__file__), "data", "curated_data", "test_studies.csv")
        study_df = pd.read_csv(test_csv)
        study_ids = study_df['TCGA_study'].tolist()
    else:
        # Use all studies
        study_csv = os.path.join(os.path.dirname(__file__), "data", "curated_data", "TCGA_study_names.csv")
        study_df = pd.read_csv(study_csv)
        study_ids = study_df['TCGA_study'].tolist()
    
    print("="*70)
    print("Upload Deletion Frequencies to S3")
    print("="*70)
    print(f"\nS3 Bucket: {args.bucket}")
    print(f"Dry Run: {args.dry_run}")
    print(f"Studies: {len(study_ids)}")
    print(f"Chromosomes: {', '.join(chromosomes)}")
    print(f"Total files to process: {len(study_ids) * len(chromosomes)}")
    print()
    
    # Process each study and chromosome
    results = {
        'success': 0,
        'failed': 0,
        'skipped': 0
    }
    
    total = len(study_ids) * len(chromosomes)
    count = 0
    
    for study_id in study_ids:
        print(f"\n{'='*70}")
        print(f"Study: {study_id}")
        print(f"{'='*70}")
        
        for chromosome in chromosomes:
            count += 1
            print(f"\n[{count}/{total}] Processing chr{chromosome}...")
            
            success = upload_deletion_frequencies(
                study_id, 
                chromosome, 
                s3_bucket=args.bucket,
                dry_run=args.dry_run
            )
            
            if success:
                results['success'] += 1
            else:
                results['failed'] += 1
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Total processed: {total}")
    print(f"  Success: {results['success']}")
    print(f"  Failed: {results['failed']}")
    print(f"  Skipped (already exist): {results['success'] - results['failed']}")
    print("="*70)


if __name__ == "__main__":
    main()
