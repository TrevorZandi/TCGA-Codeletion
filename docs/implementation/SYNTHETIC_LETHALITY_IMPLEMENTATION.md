# Synthetic Lethality Target Discovery - Implementation Summary

## Overview
Successfully integrated Harle et al. 2025 synthetic lethality data with TCGA co-deletion analysis to identify therapeutic opportunities.

## Files Created

### Core Analysis Module
- **`src/analysis/synthetic_lethality.py`** (425 lines)
  - `load_synthetic_lethal_data()`: Load and filter SL pairs from CSV
  - `calculate_hit_frequency()`: Count validation across 27 cell lines
  - `calculate_therapeutic_score()`: Score = del_freq × |GI| × ess_weight × context_weight
  - `aggregate_deletions_genome_wide()`: Load all 24 chromosomes for a study
  - `join_deletion_with_synthetic_lethality()`: Create bidirectional targeting opportunities
  - `compare_across_studies()`: Multi-study comparison

### Visualization Module
- **`src/visualization/target_discovery.py`** (301 lines)
  - `create_target_ranking_table()`: Sortable/filterable DataTable
  - `create_therapeutic_score_scatter()`: Deletion freq vs GI score plot
  - `create_target_gene_ranking_bar()`: Top targets by cumulative score
  - `create_study_comparison_heatmap()`: Cross-study heatmap

### Layout/UI
- **`src/layouts/target_discovery_tab.py`** (97 lines)
  - Controls: Study dropdown, FDR slider, min deletion freq slider, essentiality filter
  - Three sub-tabs: Opportunities table, scatter plot, target ranking
  - Info alerts explaining SL concept and data source

### Testing
- **`test_synthetic_lethality.py`** (140 lines)
  - Validates all core functions
  - Tests data loading, hit frequency calculation, deletion aggregation, and joining
  - Successfully finds 90 therapeutic opportunities in PRAD

## Files Modified

### Integration Points
1. **`src/layouts/codeletion.py`**: Added "Synthetic Lethality Targets" tab to main navigation
2. **`src/layouts/codeletion.py`**: Added Harle 2025 citation to footer with DOI link
3. **`src/app.py`**: Added target discovery tab routing in `display_tab_content()`
4. **`src/app.py`**: Added 2 new callbacks:
   - `populate_target_study_dropdown()`: Populate study selector
   - `update_target_discovery_viz()`: Main visualization callback (140 lines)
5. **`.github/copilot-instructions.md`**: Documented new architecture and data flow

## Key Features

### Data Integration
- **Cancer-type agnostic**: Assumes SL relationships generalize beyond 3 tested cancer types
- **Bidirectional opportunities**: Each pair (A,B) creates 2 targets (A deleted → target B, B deleted → target A)
- **Genome-wide aggregation**: Loads all 24 chromosomes automatically
- **Hit frequency tracking**: Shows validation in X/27 cell lines and which cancer types

### Scoring System
```python
therapeutic_score = deletion_freq × |GI_score| × essentiality_weight × context_weight

Essentiality weights:
- 2.0: Common essential (BAGEL2) - validated safe targets
- 1.5: Context-dependent (>50% DepMap lines) - broadly applicable
- 1.0: Baseline

Context weights:
- 0.5 + (hit_fraction × 1.5)
- Range: 0.5 (hit in 1/27 lines) to 2.0 (hit in 27/27 lines)
```

### User Interface
- **Study selection**: Choose any TCGA PanCancer Atlas study
- **FDR threshold**: Filter SL pairs by statistical significance (default 5%)
- **Min deletion frequency**: Only show deletions affecting ≥X% of patients (default 5%)
- **Essentiality filter**: Show all, essential only, or non-essential only
- **Three visualizations**:
  1. Sortable table with all metrics
  2. Scatter plot (deletion freq vs GI score, colored by essentiality)
  3. Bar chart of top target genes

## Test Results

Using `prad_tcga_pan_can_atlas_2018`:
- Loaded 3,707 SL pairs (FDR ≤ 0.05)
- 293 unique gene pairs
- 42,269 genes with deletion data
- **90 therapeutic opportunities found**

**Top 5 opportunities:**
1. INTS6 deleted (28.8%) → target INTS6L (Score: 0.903)
2. ASF1A deleted (22.8%) → target ASF1B (Score: 0.847)
3. PPP2CB deleted (13.9%) → target PPP2CA (Score: 0.593)
4. SLC25A37 deleted (20.9%) → target SLC25A28 (Score: 0.562)
5. CHMP1A deleted (23.2%) → target CHMP1B (Score: 0.507)

## Data Source Attribution

**Citation added to footer:**
> Synthetic lethality data: Harle et al. (2025). A compendium of synthetic lethal gene pairs defined by extensive combinatorial pan-cancer CRISPR screening. Genome Biology. https://doi.org/10.1186/s13059-025-03737-w

## Future Enhancements (Not Yet Implemented)

1. **Expression filtering**: Use TCGA RNA-seq to filter by target gene expression in tumor subpopulations
2. **Multi-study comparison page**: Dedicated page showing which targets work best in which cancers
3. **Network visualization**: Graph view of SL relationships
4. **Drug target mapping**: Link target genes to existing drugs/compounds
5. **Export functionality**: CSV download of ranked opportunities

## Technical Notes

- All processing happens in callbacks (no pre-computation required)
- Genome-wide deletion loading takes ~30 seconds per study
- SL data loaded once per session and cached in memory
- Graceful error handling with detailed error messages
- Works with both local and S3 data sources

## Testing

Run test suite:
```bash
source venv/bin/activate
python tests/test_synthetic_lethality.py
```

Launch app:
```bash
python src/app.py
```

Navigate to Co-Deletion Explorer → Synthetic Lethality Targets tab.
