# AI Agent Instructions for TCGA Co-Deletion Analysis

## Architecture Overview

This is a **two-phase ETL + visualization pipeline** for analyzing gene co-deletion patterns in TCGA cancer genomics data:

1. **ETL Phase** (`batch_process.py`, `main.py`): Fetch from cBioPortal API → compute co-deletion statistics → save to Excel/CSV
2. **Viz Phase** (`app.py`): Multi-page Dash web app loads pre-computed data for interactive exploration

**Critical separation**: ETL and visualization are completely independent. Never mix data processing logic into Dash callbacks.

## Data Flow & Key Components

```
cBioPortal API → cbioportal_client.py (cached) → queries.py (domain logic)
                                                       ↓
                                         codeletion_calc.py (statistics)
                                                       ↓
                                         batch_process.py (768 analyses)
                                                       ↓
                           data/processed/{study}/{chr}_*.xlsx (S3 or local)
                                                       ↓
                                    processed_loader.py (S3/local abstraction)
                                                       ↓
                              app.py (Dash) ← codeletion_heatmap.py (Plotly)

Harle 2025 SL data → synthetic_lethality.py → target_discovery.py (visualizations)
                            ↓
                    Join with TCGA deletions → Therapeutic opportunities
```

### Core Statistical Computation

**Conditional probabilities** are THE core metric (`analysis/codeletion_calc.py`):
- `P(A,B)` = Joint probability both genes deleted (from co-occurrence counts)
- `P(A|B)` = Conditional probability A deleted given B deleted = `count(A,B) / count(B,B)`
- The heatmap shows `P(A|B)`, NOT `P(A,B)` - this is asymmetric!
- Diagonal values are always 1.0 (a gene co-deletes with itself 100%)

### Synthetic Lethality Integration

**Therapeutic opportunity scoring** (`analysis/synthetic_lethality.py`):
- Formula: `therapeutic_score = deletion_freq × |GI_score| × essentiality_weight × context_weight`
- Essentiality weights: 2.0 (core essential/BAGEL2), 1.5 (>50% DepMap lines), 1.0 (baseline)
- Context weights: Based on validation breadth (hit_frequency across 27 cell lines)
- **Bidirectional**: Each SL pair creates 2 opportunities (A deleted → target B, B deleted → target A)

**Data source**: Harle et al. 2025 - 472 gene pairs tested in 27 cell lines (8 melanoma, 10 NSCLC, 9 pancreatic)
- Most SL relationships (>50%) are context-dependent
- Cancer-type agnostic approach: assumes SL relationships generalize beyond tested cell lines

### Data Storage: Dual Mode (Local vs S3)

Environment variables control storage (`data/processed_loader.py`):
- `USE_S3=true` → Load from S3 bucket (AWS deployment)
- `USE_S3=false` or unset → Load from local `data/processed/` directory

**File naming pattern**: `data/processed/{study_id}/chr{N}_{type}.xlsx`
- Types: `genes_metadata`, `codeletion_conditional_frequencies`, `codeletion_frequencies`, `deletion_frequencies`
- Chromosomes 1-22, X, Y (24 total per study)
- 32 TCGA studies = 768 total analyses

**Large chromosomes use CSV**: If >1000 genes, conditional matrix saved as `.csv` not `.xlsx` (Excel size limit)

## Development Workflows

### Adding New Visualizations to Dash App

1. Create Plotly figure constructor in `visualization/codeletion_heatmap.py`:
   - Function signature: `create_X_figure(data, **kwargs) -> go.Figure`
   - Return pure Plotly Figure object, NO file I/O
   - Use existing data from `processed_loader.py` functions

2. Add layout component in `layouts/{page}.py`:
   - Use `dcc.Graph(id='my-graph-id')` for Plotly charts
   - Wrap in `dcc.Loading()` for loading states
   - Bootstrap components: `dbc.Card`, `dbc.Row`, `dbc.Col`

3. Create callback in `app.py`:
   - Pattern: `@app.callback(Output('graph-id', 'figure'), [Input(...)])`
   - Load data via `processed_loader.load_X()` functions
   - Call visualization function with loaded data
   - Return Figure object directly

**Critical**: Never perform heavy computation in callbacks - data is pre-computed in batch processing

### Running the Full Pipeline

```bash
# 1. Batch process all studies (8-12 hours, creates 768 files)
python batch_process.py

# 2. Test mode (chr13 only, 2 studies, ~5 min)
python batch_process.py --test

# 3. Single study/chromosome (for debugging)
python main.py 13 prad_tcga_pan_can_atlas_2018

# 4. Launch Dash app (local mode)
python app.py  # Opens on http://127.0.0.1:8050

# 5. Upload metadata to S3 (after updating gene positions)
./run_update_metadata.sh

# 6. Upload all processed data to S3 (for AWS deployment)
./upload_data_to_s3.sh tcga-codeletion-data

# 7. Test S3 connection (before deploying)
python test_s3_connection.py
```

### Troubleshooting Common Issues

**Problem**: Heatmap shows wrong data for selected chromosome
- **Cause**: Cache key missing gene list hash (pre-2024 bug)
- **Fix**: Clear cache: `rm -rf data/cached/` and reprocess with `python main.py`
- **Verify**: Check that `data/cached/cna_data_*` files have 8-char hash suffix

**Problem**: Excel file size error when processing large chromosomes
- **Cause**: Excel has 1,048,576 row limit; chromosomes with >1000 genes exceed this
- **Fix**: Code automatically uses CSV for large chromosomes (see `batch_process.py:105`)
- **Verify**: Check `data/processed/{study}/chr1_*.csv` exists (chr1 is largest)

**Problem**: Dash callback exception on page load
- **Cause**: Component ID referenced before layout rendered
- **Fix**: Set `suppress_callback_exceptions=True` in app initialization (already done in `app.py:94`)

**Problem**: S3 data not loading in deployed app
- **Cause**: IAM role missing `s3:GetObject` permission or wrong bucket/prefix
- **Fix**: Update IAM role and verify environment variables:
  ```bash
  eb ssh
  echo $USE_S3  # Should be "true"
  echo $S3_BUCKET  # Should be bucket name
  python -c "from data.processed_loader import load_conditional_matrix; print('OK')"
  ```

**Problem**: Deletion frequencies sum to >100%
- **Cause**: This is CORRECT behavior - frequencies are per-gene (not mutually exclusive)
- **Explanation**: If 50% of samples have gene A deleted and 50% have gene B deleted, both show 50% frequency

**Problem**: Conditional matrix diagonal not 1.0
- **Cause**: Gene has zero deletions across all samples (division by zero)
- **Fix**: Filter genes with zero deletions before computing conditional: `deletion_mat.loc[:, deletion_mat.sum() > 0]`

### AWS Deployment Pattern

See `AWS_DEPLOYMENT_GUIDE.md` for complete details. Key points:

1. **Upload processed data to S3 first** (~6GB, too large for GitHub):
   ```bash
   ./upload_data_to_s3.sh tcga-codeletion-data
   ```

2. **Deploy with environment variables**:
   ```bash
   eb create tcga-codeletion-env
   eb setenv USE_S3=true S3_BUCKET=tcga-codeletion-data
   eb deploy
   ```

3. **Entry point**: `application.py` (not `app.py`) - exposes WSGI server for Elastic Beanstalk

4. **IAM requirements**: EC2 instance needs `s3:GetObject` permission on the data bucket

## Project-Specific Conventions

### Gene Naming Format
Genes stored as `"SYMBOL (EntrezID)"` format (e.g., `"TP53 (7157)"`). This appears in:
- DataFrame column names (deletion matrices)
- Index values (conditional matrices)  
- Gene metadata `hugoGeneSymbol` field

When creating gene lookups, match this exact format or extract symbol with `.split(' ')[0]`

### Cytoband Sorting
Genes sorted by chromosomal position using `start` field (genomic base pair position), NOT alphabetically. This is critical for:
- Heatmap axis ordering (visual clustering of co-located genes)
- Deletion frequency scatter plots (left-to-right = telomere to centromere)
- Summary page distribution charts

Implementation: `queries.get_chromosome_genes()` sorts by `start` field from cBioPortal API

### Caching Strategy

**API responses cached** in `data/cached/` with MD5-hashed filenames:
- Key includes: endpoint + parameters + **gene list hash** (critical!)
- Cache bug history: Originally missing gene list in key → chr13 data served for all chromosomes
- Always include full context in cache keys when dealing with gene-specific queries

**Processed results** in `data/processed/` or S3 (NOT cached - these are final outputs)

### Multi-Page Dash Routing

URL-based navigation with `dcc.Location`:
- `/` → `layouts.home.create_home_layout()`
- `/codeletion` → `layouts.codeletion.create_codeletion_layout()`  
- `/summary` → `layouts.summary.create_summary_layout()`

Callback pattern in `app.py`:
```python
@app.callback(Output('page-content', 'children'), Input('url', 'pathname'))
def display_page(pathname):
    if pathname == '/': return create_home_layout()
    elif pathname == '/codeletion': return create_codeletion_layout()
    # ...
```

Each page has separate callbacks for interactivity - callbacks scoped to component IDs in that page's layout

### Dash Callback Patterns

**Study/chromosome selectors** (populate on page load):
```python
@app.callback(Output('study-dropdown', 'options'), Input('study-dropdown', 'id'))
def populate_study_dropdown(_):
    studies = processed_loader.list_available_studies()
    return get_study_options_with_names(studies)  # Fetches human-readable names from API
```

**Multi-output visualizations** (all 3 charts updated together):
```python
@app.callback(
    [Output('heatmap-graph', 'figure'),
     Output('scatter-graph', 'figure'),
     Output('bar-graph', 'figure')],
    [Input('study-dropdown', 'value'),
     Input('chromosome-dropdown', 'value')]
)
def update_visualizations(study, chr):
    # Load data once
    conditional_mat = processed_loader.load_conditional_matrix(chr, study)
    deletion_freqs = processed_loader.load_deletion_frequencies(chr, study)
    # Generate all figures
    return (
        codeletion_heatmap.create_heatmap_figure(conditional_mat),
        codeletion_heatmap.create_scatter_figure(deletion_freqs),
        codeletion_heatmap.create_bar_figure(conditional_mat)
    )
```

**Tab-based content switching** (use `active_tab` input):
```python
@app.callback(
    Output('tab-content', 'children'),
    Input('visualization-tabs', 'active_tab')
)
def render_tab_content(active_tab):
    if active_tab == 'tab-heatmap': return create_heatmap_tab()
    elif active_tab == 'tab-scatter': return create_scatter_tab()
    # ...
```

### Common Callback Pitfalls

1. **Don't return dash components with state** - Return data, not `dcc.Graph(figure=fig)` in callbacks
2. **Suppress callback exceptions** - Set `suppress_callback_exceptions=True` for multi-page apps (components not in DOM until page loads)
3. **Handle missing data gracefully** - Return empty figures, not `None`, to prevent Dash errors
4. **Use triggering context carefully** - For multi-input callbacks, `callback_context.triggered` identifies which input fired

### Table Implementation (Dash DataTable)

Recent pattern for gene pair tables (`visualization/codeletion_heatmap.py`):
- Store **numeric values** in data, format with `'format': {'specifier': '.2%'}` for percentages
- This enables proper numeric sorting (100% > 99%, not alphanumeric "100%" < "99%")
- Use `page_action='native'` to paginate large datasets (filter/sort across ALL rows, not just displayed)
- Column types: `'numeric'` for sortable numbers, `'text'` for genes

Example:
```python
columns=[
    {'name': 'Gene A', 'id': 'Gene A', 'type': 'text'},
    {'name': 'Distance (bp)', 'id': 'Distance (bp)', 'type': 'numeric', 'format': {'specifier': ',.0f'}},
    {'name': 'P(A|B)', 'id': 'P(A|B)', 'type': 'numeric', 'format': {'specifier': '.2%'}}
]
```

### Genomic Distance Calculation

Gene metadata now includes `start` and `end` positions (base pairs). Distance between pairs:
```python
distance_bp = abs(gene_positions[gene_i]['start'] - gene_positions[gene_j]['start'])
```

This is **start-to-start distance**, not gap distance. Same-chromosome pairs only (no inter-chromosomal).

## Common Pitfalls

1. **Don't compute statistics in Dash callbacks** - All heavy lifting done in batch_process.py
2. **Check file format (CSV vs Excel)** - Large chromosomes use CSV, most use Excel
3. **Always pass chromosome parameter** - Default is chr13, but app supports all 24
4. **Match gene name format exactly** - `"SYMBOL (ENTREZ)"` not just `"SYMBOL"`
5. **Use conditional matrix for heatmaps** - NOT the symmetric joint probability matrix
6. **Filter out zero-deletion genes** - Avoid cluttering visualizations with non-informative genes
7. **S3 vs local paths** - Use `processed_loader.py` functions, never hardcode paths

## Testing & Debugging

### Test Data & Quick Commands
- **Test data**: `data/curated_data/test_studies.csv` (PRAD, BRCA only)
- **Quick test**: `python batch_process.py --test` (chr13 only, 2 studies, ~5 min)
- **Single chromosome test**: `python main.py 13 prad_tcga_pan_can_atlas_2018`
- **Check processed outputs**: Verify files exist in `data/processed/{study}/chr{N}_*.xlsx`
- **Local Dash testing**: `python app.py` (auto-uses local files if `USE_S3` not set)
- **AWS local testing**: `export USE_S3=false && python app.py` (explicitly use local files)
- **S3 debugging**: Check IAM permissions and bucket/prefix environment variables

### Debugging Data Issues

**Verify cache integrity** (if seeing wrong chromosome data):
```bash
# Check if cache key includes gene hash
ls -la data/cached/ | grep "genes_ncbi_detailed\|cna_data"
# Should see filenames like: cna_data_prad_gistic_abcd1234.pkl (8-char hash at end)
```

**Inspect deletion matrix shape**:
```python
from data import queries, processed_loader
deletion_mat = queries.build_deletion_matrix(cna_data, chr_genes)
print(f"Shape: {deletion_mat.shape}")  # (n_samples, n_genes)
print(f"Total deletions: {deletion_mat.sum().sum()}")
print(f"Genes with deletions: {(deletion_mat.sum(axis=0) > 0).sum()}")
```

**Validate conditional matrix properties**:
```python
# Diagonal should be all 1.0 (gene always co-deletes with itself)
conditional = processed_loader.load_conditional_matrix(chr, study)
assert (conditional.values.diagonal() == 1.0).all(), "Diagonal not all 1.0!"
# Matrix should be asymmetric (P(A|B) ≠ P(B|A))
assert not np.allclose(conditional, conditional.T), "Matrix should be asymmetric!"
```

**Check file format mismatch**:
```python
# Large chromosomes use CSV, small use Excel
import os
study_dir = f"data/processed/{study_id}"
for f in os.listdir(study_dir):
    if 'conditional' in f:
        print(f"{f}: {os.path.getsize(os.path.join(study_dir, f)) / 1024:.1f} KB")
```

## External Dependencies & Integration

- **cBioPortal API**: `https://www.cbioportal.org/api` - Swagger docs in `documentation/Cbioportal_api_doc.json`
- **TCGA Data**: PanCancer Atlas 2018 studies (32 studies) - citation required in footer
- **AWS Services**: S3 (data storage), Elastic Beanstalk (app hosting), IAM (permissions)
- **Dash/Plotly**: v2.x for web framework, Bootstrap theme for UI components

## Code Organization Patterns

### Module Responsibilities
- **`data/`**: All external data access (API, cache, file loading)
  - `cbioportal_client.py`: Raw API calls with automatic pickle caching
  - `queries.py`: Domain logic layer (combines API calls, filters data)
  - `cache_utils.py`: Simple pickle-based cache (no TTL, manual refresh flag)
  - `processed_loader.py`: Dual-mode loader (S3 or local filesystem)
- **`analysis/`**: Pure functions for statistical computation (no I/O)
- **`visualization/`**: Pure Plotly figure constructors (no file I/O)
- **`layouts/`**: Dash component trees (no logic, only UI structure)
- **`app.py`**: Callbacks orchestrate data loading → computation → visualization

### File Naming Conventions
All processed files follow strict naming: `chr{N}_{type}.{ext}`
- `{N}`: 1-22, X, Y
- `{type}`: `genes_metadata`, `codeletion_conditional_frequencies`, `codeletion_frequencies`, `deletion_frequencies`
- `{ext}`: `.xlsx` (default) or `.csv` (if >1000 genes)

### Error Handling Philosophy
- ETL phase: Fail fast with informative errors (data quality issues block processing)
- Dash callbacks: Graceful degradation (return empty figures on missing data)
- Cache misses: Transparent fallback to API (user never sees cache layer)

## Performance Considerations

### Batch Processing Strategy
`batch_process.py` is optimized for long-running execution:
- Process 768 analyses (32 studies × 24 chromosomes) in ~8-12 hours
- No parallelization (cBioPortal API rate limits, cache contention)
- Skip studies with <10 samples (insufficient statistical power)
- Use `--test` flag for development (chr13 only, 2 studies, ~5 min)

### Dash App Optimization
- **Zero computation in callbacks**: All statistics pre-computed in batch processing
- **Conditional loading**: Only load requested chromosome data (not all 24 at once)
- **CSV fallback**: Large chromosomes (>1000 genes) use CSV to avoid Excel size limits
- **Client-side filtering**: DataTable uses `page_action='native'` for browser-side pagination

## Recent Changes & Migration Notes

- **Synthetic lethality feature (Dec 2025)**: New tab integrating Harle 2025 data with TCGA deletions for target discovery
  - Module: `analysis/synthetic_lethality.py` with genome-wide deletion aggregation
  - Visualizations: `visualization/target_discovery.py` (table, scatter, bar charts)
  - Tab: `layouts/target_discovery_tab.py` in Co-Deletion Explorer
  - Citation added to footer with DOI link
- **Genomic distance feature**: Added `Distance (bp)` column to gene pairs table (requires updated metadata in S3)
- **Table improvements**: Numeric sorting, filter across all rows, conditional probabilities instead of joint
- **Footer citations**: TCGA Research Network citation and Trevor A. Zandi credit on all pages
- **Metadata updates**: Script `update_gene_metadata.py` regenerates files with genomic positions
- **Cache bug fix (2024)**: Original implementation lacked gene list hash in cache keys → chr13 data served for all chromosomes. Now uses MD5 hash of sorted gene IDs in cache filenames.
