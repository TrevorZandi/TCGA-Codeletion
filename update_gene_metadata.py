#!/usr/bin/env python3
"""
Update gene metadata files to include genomic start/end positions.

This script regenerates the gene metadata files with start/end positions
and uploads them to S3, without re-running the full analysis pipeline.
"""

import os
import sys
import pandas as pd
import boto3
from io import BytesIO

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from data import queries

# Configuration
S3_BUCKET = "tcga-codeletion-data"
CHROMOSOMES = [str(i) for i in range(1, 23)] + ['X', 'Y']

# Load study list
studies_df = pd.read_csv("data/curated_data/TCGA_study_names.csv")
STUDIES = studies_df["TCGA_study"].tolist()


def upload_metadata_to_s3(study_id, chromosome, metadata_df):
    """Upload gene metadata to S3."""
    s3_client = boto3.client('s3')
    
    # Convert DataFrame to Excel in memory
    excel_buffer = BytesIO()
    metadata_df.to_excel(excel_buffer, index=False)
    excel_buffer.seek(0)
    
    # Upload to S3
    s3_key = f"processed/{study_id}/chr{chromosome}_genes_metadata.xlsx"
    s3_client.put_object(
        Bucket=S3_BUCKET,
        Key=s3_key,
        Body=excel_buffer.getvalue(),
        ContentType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    
    print(f"  ✓ Uploaded to s3://{S3_BUCKET}/{s3_key}")


def main():
    """Update gene metadata for all studies and chromosomes."""
    print(f"Updating gene metadata with genomic positions...")
    print(f"Studies: {len(STUDIES)}")
    print(f"Chromosomes: {len(CHROMOSOMES)}")
    print(f"Total files to update: {len(STUDIES) * len(CHROMOSOMES)}")
    print()
    
    total_updated = 0
    
    for study_idx, study_id in enumerate(STUDIES, 1):
        print(f"[{study_idx}/{len(STUDIES)}] Processing {study_id}...")
        
        for chr_idx, chromosome in enumerate(CHROMOSOMES, 1):
            try:
                # Fetch gene metadata with positions
                metadata_df = queries.get_chromosome_genes(
                    chromosome=chromosome,
                    genome="hg19",
                    refresh=False
                )
                
                # Upload to S3
                upload_metadata_to_s3(study_id, chromosome, metadata_df)
                total_updated += 1
                
                # Progress indicator
                if chr_idx % 6 == 0:
                    print(f"  Progress: {chr_idx}/{len(CHROMOSOMES)} chromosomes")
                    
            except Exception as e:
                print(f"  ✗ Error processing chr{chromosome}: {e}")
                continue
        
        print()
    
    print(f"\n{'='*60}")
    print(f"Update complete!")
    print(f"Total files updated: {total_updated}/{len(STUDIES) * len(CHROMOSOMES)}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
