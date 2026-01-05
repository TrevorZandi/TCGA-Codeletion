#!/usr/bin/env python
"""
Test S3 connectivity and data loading for AWS deployment.

This script verifies:
1. AWS credentials are configured
2. S3 bucket is accessible
3. Processed data can be loaded from S3
"""

import os
import sys

# Set environment variables to use S3
os.environ['USE_S3'] = 'true'
os.environ['S3_BUCKET'] = 'tcga-codeletion-data'
os.environ['S3_PREFIX'] = 'processed/'

# Now import the data loader (after setting env vars)
from src.data import processed_loader

def test_s3_connection():
    """Test basic S3 connectivity."""
    print("=" * 60)
    print("TCGA Co-Deletion S3 Connection Test")
    print("=" * 60)
    print()
    
    print("Configuration:")
    print(f"  USE_S3: {processed_loader.USE_S3}")
    print(f"  S3_BUCKET: {processed_loader.S3_BUCKET}")
    print(f"  S3_PREFIX: {processed_loader.S3_PREFIX}")
    print()
    
    # Test 1: List available studies
    print("Test 1: Listing available studies from S3...")
    try:
        studies = processed_loader.list_available_studies()
        print(f"✓ Found {len(studies)} studies")
        if studies:
            print(f"  First 5 studies: {studies[:5]}")
    except Exception as e:
        print(f"✗ Failed to list studies: {e}")
        return False
    
    print()
    
    if not studies:
        print("✗ No studies found in S3")
        return False
    
    # Test 2: Load gene metadata
    print("Test 2: Loading gene metadata from S3...")
    try:
        test_study = studies[0]
        metadata = processed_loader.load_gene_metadata("13", test_study)
        print(f"✓ Loaded metadata for chr13 from {test_study}")
        print(f"  Shape: {metadata.shape}")
        print(f"  Columns: {list(metadata.columns)}")
    except Exception as e:
        print(f"✗ Failed to load metadata: {e}")
        return False
    
    print()
    
    # Test 3: Load deletion frequencies (with fallback)
    print("Test 3: Loading deletion frequencies from S3...")
    try:
        del_freqs = processed_loader.load_deletion_frequencies("13", test_study)
        print(f"✓ Loaded deletion frequencies for chr13")
        print(f"  Number of genes: {len(del_freqs)}")
        print(f"  Max deletion frequency: {del_freqs.max():.2%}")
        print(f"  Genes with deletions: {(del_freqs > 0).sum()}")
    except Exception as e:
        print(f"✗ Failed to load deletion frequencies: {e}")
        return False
    
    print()
    
    # Test 3b: Load co-deletion pairs
    print("Test 3b: Loading co-deletion pairs from S3...")
    try:
        pairs = processed_loader.load_codeletion_pairs("13", test_study)
        print(f"✓ Loaded co-deletion pairs for chr13")
        print(f"  Number of pairs: {len(pairs)}")
    except Exception as e:
        print(f"✗ Failed to load co-deletion pairs: {e}")
        return False
    
    print()
    
    # Test 4: Load conditional matrix
    print("Test 4: Loading conditional matrix from S3...")
    try:
        cond_matrix = processed_loader.load_conditional_matrix("13", test_study)
        print(f"✓ Loaded conditional matrix for chr13")
        print(f"  Shape: {cond_matrix.shape}")
    except Exception as e:
        print(f"✗ Failed to load conditional matrix: {e}")
        return False
    
    print()
    print("=" * 60)
    print("✓ All S3 tests passed!")
    print("=" * 60)
    print()
    print("Your application is ready for AWS deployment.")
    print()
    
    return True


if __name__ == "__main__":
    try:
        success = test_s3_connection()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
