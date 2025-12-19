"""
Debug script to test scatter plot data accuracy
"""
import pandas as pd
from analysis import synthetic_lethality as sl

# Load SL data
sl_data = sl.load_synthetic_lethal_data(fdr_threshold=0.05)
hit_freq = sl.calculate_hit_frequency(sl_data)

# Load PRAD deletions
deletions = sl.aggregate_deletions_genome_wide('prad_tcga_pan_can_atlas_2018')

# Join
opportunities = sl.join_deletion_with_synthetic_lethality(
    deletion_df=deletions,
    sl_data=sl_data,
    hit_frequency_df=hit_freq,
    min_deletion_freq=0.05
)

# Check ASF1A/ASF1B pair
asf_pairs = opportunities[
    ((opportunities['deleted_gene'] == 'ASF1A') & (opportunities['target_gene'] == 'ASF1B')) |
    ((opportunities['deleted_gene'] == 'ASF1B') & (opportunities['target_gene'] == 'ASF1A'))
]

print("ASF1A/ASF1B opportunities:")
print(asf_pairs[['deleted_gene', 'target_gene', 'deletion_frequency', 'gi_score', 'fdr']])

# Check what the raw SL data shows
asf_sl = sl_data[
    ((sl_data['targetA'] == 'ASF1A') & (sl_data['targetB'] == 'ASF1B')) |
    ((sl_data['targetA'] == 'ASF1B') & (sl_data['targetB'] == 'ASF1A'))
]

print("\nRaw SL data for ASF1A/ASF1B:")
print(asf_sl[['targetA', 'targetB', 'mean_norm_gi', 'fdr', 'cell_line_label']].head(10))
