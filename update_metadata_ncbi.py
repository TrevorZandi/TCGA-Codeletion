#!/usr/bin/env python3
"""
Update all gene metadata files with NCBI genomic coordinates.
Regenerates chr{N}_genes_metadata.xlsx for all studies and uploads to S3.
"""

import pandas as pd
import boto3
from io import BytesIO
from data import queries
import time
import os

# Configuration
S3_BUCKET = os.environ.get('S3_BUCKET', 'tcga-codeletion-data')
S3_PREFIX = 'processed/'

# Studies to process
STUDIES = [
    'acc_tcga_pan_can_atlas_2018',
    'blca_tcga_pan_can_atlas_2018',
    'brca_tcga_pan_can_atlas_2018',
    'cesc_tcga_pan_can_atlas_2018',
    'chol_tcga_pan_can_atlas_2018',
    'coadread_tcga_pan_can_atlas_2018',
    'dlbc_tcga_pan_can_atlas_2018',
    'esca_tcga_pan_can_atlas_2018',
    'gbm_tcga_pan_can_atlas_2018',
    'hnsc_tcga_pan_can_atlas_2018',
    'kich_tcga_pan_can_atlas_2018',
    'kirc_tcga_pan_can_atlas_2018',
    'kirp_tcga_pan_can_atlas_2018',
    'laml_tcga_pan_can_atlas_2018',
    'lgg_tcga_pan_can_atlas_2018',
    'lihc_tcga_pan_can_atlas_2018',
    'luad_tcga_pan_can_atlas_2018',
    'lusc_tcga_pan_can_atlas_2018',
    'meso_tcga_pan_can_atlas_2018',
    'ov_tcga_pan_can_atlas_2018',
    'paad_tcga_pan_can_atlas_2018',
    'pcpg_tcga_pan_can_atlas_2018',
    'prad_tcga_pan_can_atlas_2018',
    'sarc_tcga_pan_can_atlas_2018',
    'skcm_tcga_pan_can_atlas_2018',
    'stad_tcga_pan_can_atlas_2018',
    'tgct_tcga_pan_can_atlas_2018',
    'thca_tcga_pan_can_atlas_2018',
    'thym_tcga_pan_can_atlas_2018',
    'ucec_tcga_pan_can_atlas_2018',
    'ucs_tcga_pan_can_atlas_2018',
    'uvm_tcga_pan_can_atlas_2018'
]

CHROMOSOMES = [str(i) for i in range(1, 23)] + ['X', 'Y']

def upload_to_s3(df, study_id, chromosome):
    """Upload metadata DataFrame to S3 as Excel file."""
    s3 = boto3.client('s3')
    
    # Convert to Excel in memory
    buffer = BytesIO()
    df.to_excel(buffer, index=False, engine='openpyxl')
    buffer.seek(0)
    
    # Upload to S3
    key = f'{S3_PREFIX}{study_id}/chr{chromosome}_genes_metadata.xlsx'
    s3.put_object(
        Bucket=S3_BUCKET,
        Key=key,
        Body=buffer.getvalue(),
        ContentType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    
    return key

def main():
    print(f'Updating gene metadata for {len(STUDIES)} studies × {len(CHROMOSOMES)} chromosomes = {len(STUDIES) * len(CHROMOSOMES)} files')
    print(f'Target: S3 bucket {S3_BUCKET}\n')
    
    total_files = 0
    total_genes = 0
    start_time = time.time()
    
    for i, study_id in enumerate(STUDIES, 1):
        print(f'\n[{i}/{len(STUDIES)}] Processing {study_id}...')
        
        for chromosome in CHROMOSOMES:
            try:
                # Fetch gene metadata with NCBI coordinates
                # Uses caching, so subsequent chromosomes across studies are fast
                genes_df = queries.get_chromosome_genes(chromosome, refresh=False)
                
                # Upload to S3
                key = upload_to_s3(genes_df, study_id, chromosome)
                
                total_files += 1
                total_genes += len(genes_df)
                
                print(f'  chr{chromosome}: {len(genes_df):4} genes → s3://{S3_BUCKET}/{key}')
                
            except Exception as e:
                print(f'  chr{chromosome}: ERROR - {e}')
        
        # Brief pause between studies
        if i < len(STUDIES):
            time.sleep(0.5)
    
    elapsed = time.time() - start_time
    print(f'\n✓ Complete! Uploaded {total_files} files ({total_genes:,} total gene entries) in {elapsed:.1f}s')
    print(f'  Average: {elapsed/total_files:.2f}s per file')

if __name__ == '__main__':
    main()
