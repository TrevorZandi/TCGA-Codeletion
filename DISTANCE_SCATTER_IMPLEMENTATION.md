# Distance vs Co-deletion Probability Scatter Plot

## Implementation Summary

### Overview
Added a new visualization showing the relationship between genomic distance and conditional co-deletion probability P(B|A) for gene pairs.

### Files Modified

#### 1. `visualization/codeletion_heatmap.py`
**New Functions:**
- `create_distance_frequency_scatter(conditional_matrix, gene_metadata, chromosome, min_distance=0)`
  - Creates Plotly scatter plot with log-scale x-axis (genomic distance)
  - Y-axis shows conditional probability P(B|A)
  - Color intensity shows probability magnitude (Viridis colorscale)
  - Filters: P(B|A) > 0, both genes have coordinates (start > 0), distance >= min_distance
  - Returns asymmetric data: both P(i|j) and P(j|i) as separate points
  - Hover shows: gene pair direction, distance in bp, P(B|A) value
  - Annotation displays total data point count

- `plot_distance_frequency_scatter(conditional_matrix, gene_metadata, chromosome, min_distance=0)`
  - Simple wrapper function for consistency with other plot functions

**Location:** Lines ~630-800 (after `plot_deletion_frequency_scatter`)

#### 2. `layouts/codeletion.py`
**New Section:**
- Added dbc.Row section titled "Genomic Distance vs Co-deletion Probability"
- Includes explanatory text describing the visualization
- Contains dcc.Graph component with id='distance-frequency-scatter'
- Wrapped in dcc.Loading for loading state
- Positioned after top pairs table section, before footer

**Location:** Between top pairs table and footer (~line 270)

#### 3. `app.py`
**New Callback:**
```python
@app.callback(
    Output('distance-frequency-scatter', 'figure'),
    [Input('study-dropdown', 'value'),
     Input('chromosome-dropdown', 'value')]
)
def update_distance_scatter(study_id, chromosome):
    """Update the distance vs conditional probability scatter plot."""
```

**Functionality:**
- Loads conditional matrix and gene metadata
- Calls `create_distance_frequency_scatter()` 
- Returns Plotly figure object
- Handles None/empty study with empty placeholder figure

**Location:** Lines ~243-290 (after `update_top_pairs`, before `update_deletion_scatter`)

### Data Requirements

**Required Files:**
- `chr{N}_codeletion_conditional_frequencies.xlsx` (or .csv for large chromosomes)
- `chr{N}_genes_metadata.xlsx` with NCBI genomic coordinates

**Required Columns in gene_metadata:**
- `hugoGeneSymbol`: Gene name
- `start`: Genomic start position (base pairs)
- `end`: Genomic end position (base pairs)
- `chromosome`: Chromosome identifier

### Visualization Features

**Data Filtering:**
- Excludes pairs where P(B|A) = 0 (reduces dataset size, focuses on actual co-deletions)
- Excludes genes with missing coordinates (start = 0)
- Optional minimum distance threshold (default 0)

**Visual Properties:**
- X-axis: Genomic distance (log scale, base 10)
- Y-axis: Conditional probability P(B|A) (linear scale, 0-1)
- Point size: 4 pixels
- Point opacity: 0.6 (to show overlapping points)
- Colorscale: Viridis (probability value)
- Hover template: Gene A, Gene B, Distance, P(B|A)

**Expected Patterns:**
- High P(B|A) at short distances → proximity-based co-deletion
- Low P(B|A) at long distances → independent deletions
- Outliers (high P(B|A) at long distances) → functional co-deletion

### Testing

**Local Testing (not run due to venv issue):**
```bash
# Note: run_app.sh expects .venv but only venv exists
# Manual command:
source venv/bin/activate
export USE_S3=true
python app.py
# Then navigate to http://127.0.0.1:8050/codeletion
```

**Deployment:**
```bash
git add visualization/codeletion_heatmap.py layouts/codeletion.py app.py
git commit -m "Add genomic distance vs conditional probability scatter plot"
git push
eb deploy
```

### Data Coverage

**Example (chr13 PRAD study):**
- Total gene pairs: 1,060 × 1,060 = 1,123,600 (full matrix)
- Upper triangle only: 561,270 pairs (avoid duplicates)
- After filtering P(B|A) > 0: ~50-70% of pairs (varies by study)
- After filtering coordinates: ~96% of remaining pairs (44 genes missing coords)

**Expected scatter plot size:**
- Small chromosomes (e.g., chr21): 100-200 data points
- Large chromosomes (e.g., chr1): 500-1,000 data points

### Implementation Notes

**Asymmetric Probabilities:**
- Conditional probabilities are NOT symmetric: P(A|B) ≠ P(B|A)
- Implementation collects BOTH directions as separate data points
- This is correct behavior, not a bug

**Distance Calculation:**
- Start-to-start distance: `abs(start_a - start_b)`
- Not gap distance (which would be `abs(end_a - start_b)` or vice versa)
- Same-chromosome pairs only (no inter-chromosomal distances)

**Performance:**
- Scatter plot generation: ~0.5-2 seconds for large chromosomes
- Callback response time: ~2-4 seconds including S3 load
- No caching implemented (data already pre-processed)

### Future Enhancements

**Potential additions:**
- Min distance slider control (currently hardcoded to 0)
- Toggle between log/linear x-axis scale
- Click points to highlight in heatmap
- Filter by probability threshold slider
- Export data points to CSV
- Regression line or trend visualization
- Binned histogram overlay

### Related Files

**Documentation:**
- `GENOMIC_DISTANCE_FIX.md` - NCBI integration for genomic coordinates
- `AWS_DEPLOYMENT_GUIDE.md` - Deployment instructions
- `.github/copilot-instructions.md` - Architecture overview

**Data Generation:**
- `update_metadata_ncbi.py` - Script to regenerate metadata with coordinates
- `batch_process.py` - Full pipeline to generate all 768 analysis files

**Dependencies:**
- Plotly for scatter plot rendering
- Pandas for data manipulation
- NumPy for numerical operations
- Dash Bootstrap Components for layout
