"""
Test script for synthetic lethality integration.

Tests the core functions to ensure proper data loading and joining.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.analysis import synthetic_lethality

def test_load_sl_data():
    """Test loading synthetic lethality data."""
    print("Testing load_synthetic_lethal_data()...")
    
    sl_data = synthetic_lethality.load_synthetic_lethal_data(fdr_threshold=0.05)
    
    print(f"✓ Loaded {len(sl_data)} SL pairs")
    print(f"  Columns: {list(sl_data.columns)}")
    print(f"  Sample gene pairs: {sl_data['sorted_gene_pair'].head(3).tolist()}")
    
    return sl_data


def test_hit_frequency(sl_data):
    """Test hit frequency calculation."""
    print("\nTesting calculate_hit_frequency()...")
    
    hit_freq = synthetic_lethality.calculate_hit_frequency(sl_data)
    
    print(f"✓ Calculated hit frequency for {len(hit_freq)} unique gene pairs")
    print(f"  Columns: {list(hit_freq.columns)}")
    
    # Show top validated pairs
    top_pairs = hit_freq.nlargest(3, 'hit_count')
    print(f"  Most validated pairs:")
    for _, row in top_pairs.iterrows():
        print(f"    {row['sorted_gene_pair']}: {row['hit_count']}/27 lines ({row['cancer_types_validated']})")
    
    return hit_freq


def test_aggregate_deletions():
    """Test genome-wide deletion aggregation."""
    print("\nTesting aggregate_deletions_genome_wide()...")
    
    study_id = "prad_tcga_pan_can_atlas_2018"
    
    try:
        deletions = synthetic_lethality.aggregate_deletions_genome_wide(study_id)
        
        print(f"✓ Aggregated deletions for {study_id}")
        print(f"  Total genes: {len(deletions)}")
        print(f"  Chromosomes: {sorted(deletions['chromosome'].unique())}")
        print(f"  Sample genes with deletions:")
        
        # Show genes with highest deletion frequency
        top_del = deletions.nlargest(5, 'deletion_frequency')
        for _, row in top_del.iterrows():
            print(f"    {row['gene']} (chr{row['chromosome']}): {row['deletion_frequency']:.1%}")
        
        return deletions
    
    except FileNotFoundError as e:
        print(f"⚠ Warning: Could not load deletion data: {e}")
        print(f"  Run batch_process.py first to generate processed data")
        return None


def test_join_deletions_sl(deletions, sl_data, hit_freq):
    """Test joining deletions with SL data."""
    if deletions is None:
        print("\nSkipping join test (no deletion data)")
        return
    
    print("\nTesting join_deletion_with_synthetic_lethality()...")
    
    opportunities = synthetic_lethality.join_deletion_with_synthetic_lethality(
        deletion_df=deletions,
        sl_data=sl_data,
        hit_frequency_df=hit_freq,
        min_deletion_freq=0.05
    )
    
    print(f"✓ Found {len(opportunities)} therapeutic opportunities")
    
    if len(opportunities) > 0:
        print(f"  Columns: {list(opportunities.columns)}")
        print(f"\n  Top 5 opportunities:")
        top_opps = opportunities.head(5)
        for _, row in top_opps.iterrows():
            print(f"    {row['deleted_gene']} deleted → target {row['target_gene']}")
            print(f"      Del: {row['deletion_frequency']:.1%} | GI: {row['gi_score']:.3f} | Score: {row['therapeutic_score']:.3f}")
            if 'hit_count' in row:
                print(f"      Validated in: {int(row['hit_count'])}/27 lines ({row['cancer_types_validated']})")


def main():
    """Run all tests."""
    print("=" * 70)
    print("TCGA Co-Deletion: Synthetic Lethality Integration Test")
    print("=" * 70)
    
    # Test 1: Load SL data
    sl_data = test_load_sl_data()
    
    # Test 2: Calculate hit frequency
    hit_freq = test_hit_frequency(sl_data)
    
    # Test 3: Aggregate deletions
    deletions = test_aggregate_deletions()
    
    # Test 4: Join deletions with SL
    test_join_deletions_sl(deletions, sl_data, hit_freq)
    
    print("\n" + "=" * 70)
    print("Tests completed!")
    print("=" * 70)


if __name__ == '__main__':
    main()
