# TCGA Co-Deletion Analysis - AI Agent Guide

## Core Architecture

**Two-phase pipeline**: ETL generates pre-computed statistics → Dash app visualizes them. **Never mix computation into Dash callbacks.**

### Data Flow
```
cBioPortal API → src/data/cbioportal_client.py (pickle cache) → src/data/queries.py → src/analysis/codeletion_calc.py
                                                                           ↓
                                                       src/batch_process.py (768 analyses)
                                                                           ↓
                                          data/processed/{study}/chr{N}_*.xlsx (S3/local)
                                                                           ↓
                                              src/data/processed_loader.py → src/app.py (Dash + Plotly)
```

### Critical Concepts

**Conditional probability P(A|B)** is the core metric:
- `P(A|B) = count(A,B) / count(B,B)` - probability gene A deleted GIVEN gene B deleted
- **Asymmetric**: P(A|B) ≠ P(B|A) - heatmap rows ≠ columns
- Diagonal always 1.0 (gene co-deletes with itself 100%)
- Implemented in `src/analysis/codeletion_calc.py:compute_conditional_codeletion()`

**Synthetic lethality scoring** (`src/analysis/synthetic_lethality.py`):
- `score = deletion_freq × |GI_score| × essentiality_weight × context_weight`
- Bidirectional: each SL pair creates 2 opportunities (A→B, B→A)
- Data: Harle 2025 (472 pairs, 27 cell lines)

**Storage modes** controlled by env vars:
- `USE_S3=true` → S3 bucket (AWS deployment)
- `USE_S3=false` → local `data/processed/` (development)

**File naming**: `data/processed/{study_id}/chr{N}_{type}.{xlsx|csv}`
- Types: `genes_metadata`, `codeletion_conditional_frequencies`, `codeletion_frequencies`, `deletion_frequencies`
- 24 chromosomes (1-22, X, Y) × 32 studies = 768 total files
- Large chromosomes (>1000 genes) use CSV not Excel

## Essential Commands

```bash
# Development workflow
python src/batch_process.py --test           # Process chr13 only (~5 min)
python src/main.py 13 prad_tcga_pan_can_atlas_2018  # Single chromosome
python src/app.py                            # Launch Dash (http://127.0.0.1:8050)

# Full pipeline (8-12 hours)
python src/batch_process.py                  # All 768 analyses

# AWS deployment
./scripts/upload_data_to_s3.sh tcga-codeletion-data  # Upload ~6GB processed data
eb create tcga-codeletion-env
eb setenv USE_S3=true S3_BUCKET=tcga-codeletion-data
eb deploy                                # Entry: application.py (WSGI)
```

## Adding Visualizations (Dash)

1. **Create figure constructor** in `src/visualization/`:
   ```python
   def create_X_figure(data, **kwargs) -> go.Figure:
       # Return pure Plotly Figure, NO file I/O
   ```

2. **Add layout** in `src/layouts/{page}.py`:
   ```python
   dcc.Graph(id='my-graph')  # Wrapped in dcc.Loading()
   ```

3. **Create callback** in `src/app.py`:
   ```python
   @app.callback(Output('my-graph', 'figure'), Input('dropdown', 'value'))
   def update_graph(selection):
       data = processed_loader.load_X(selection)  # Load pre-computed
       return create_X_figure(data)  # Return Figure directly
   ```

**Critical**: Callbacks only orchestrate - no computation, just load → visualize.

## Project Conventions

### Gene Format & Sorting
- **Gene naming**: `"SYMBOL (EntrezID)"` everywhere (e.g., `"TP53 (7157)"`) - extract symbol with `.split(' ')[0]`
- **Gene ordering**: By `start` position (bp), NOT alphabetically - critical for heatmap/scatter visual clustering
- **Genomic distance**: `abs(start_A - start_B)` - start-to-start, same chromosome only

### Caching (data/cached/)
- MD5-hashed filenames: `cna_data_{study}_{gene_hash}.pkl`
- Key includes: endpoint + params + **gene list hash** (critical!)
- **Bug history**: Missing gene hash caused chr13 served for all (fixed 2024)

### Dash Multi-Page Pattern
URL routing with `dcc.Location` + `suppress_callback_exceptions=True`:
```python
@app.callback(Output('page-content', 'children'), Input('url', 'pathname'))
def display_page(pathname):
    if pathname == '/': return create_home_layout()
    elif pathname == '/codeletion': return create_codeletion_layout()
```

### Dash Callback Tips
- **Multi-output**: Load data once, return tuple of figures
- **Dropdowns**: Use component `id` as trigger to populate on page load
- **DataTables**: Store numeric values, format for display - enables proper sorting
  ```python
  {'name': 'P(A|B)', 'id': 'P(A|B)', 'type': 'numeric', 'format': {'specifier': '.2%'}}
  ```
- **Tab switching**: Use `Input('tabs', 'active_tab')` to render content conditionally

## Common Pitfalls

1. **Don't compute statistics in Dash callbacks** - All heavy lifting done in batch_process.py
2. **Check file format (CSV vs Excel)** - Large chromosomes use CSV, most use Excel
3. **Always pass chromosome parameter** - Default is chr13, but app supports all 24
4. **Match gene name format exactly** - `"SYMBOL (ENTREZ)"` not just `"SYMBOL"`
5. **Use conditional matrix for heatmaps** - NOT the symmetric joint probability matrix
6. **Filter out zero-deletion genes** - Avoid cluttering visualizations with non-informative genes
7. **S3 vs local paths** - Use `processed_loader.py` functions, never hardcode paths

## Troubleshooting

**Wrong chromosome data**: Clear cache `rm -rf data/cached/` - verify files have 8-char hash suffix  
**Excel size error**: Large chromosomes auto-use CSV (>1000 genes)  
**S3 not loading**: Check IAM `s3:GetObject` permission and `USE_S3=true` env var  
**Conditional matrix validation**:
```python
conditional = processed_loader.load_conditional_matrix(chr, study)
assert (conditional.values.diagonal() == 1.0).all()  # Self co-deletion = 100%
assert not np.allclose(conditional, conditional.T)    # Asymmetric
```

## Code Organization

**Module boundaries** (strict separation of concerns):
- `src/data/` - All I/O: API (`cbioportal_client.py`), cache (`cache_utils.py`), file loading (`processed_loader.py`)
- `src/analysis/` - Pure computation functions (no I/O)
- `src/visualization/` - Pure Plotly constructors (no I/O)
- `src/layouts/` - Dash UI trees (no logic)
- `src/app.py` - Callbacks orchestrate: load → compute → visualize
- `scripts/` - Utility scripts for deployment and maintenance
- `tests/` - Test and debug scripts
- `docs/` - Organized documentation (deployment, implementation, api, references)

**File naming**: `chr{N}_{type}.{xlsx|csv}` where N=1-22,X,Y and type=[genes_metadata, codeletion_conditional_frequencies, codeletion_frequencies, deletion_frequencies]

**Error handling**: ETL fails fast, Dash callbacks degrade gracefully (return empty figures)

**External dependencies**: cBioPortal API (Swagger in `docs/api/`), TCGA PanCancer Atlas 2018 (32 studies), AWS S3/EB/IAM, Dash/Plotly v2.x

## Performance & Recent Changes

**Batch processing**: 768 analyses in 8-12 hours (no parallelization due to API limits), skip studies <10 samples

**Dash optimization**: Zero computation in callbacks (all pre-computed), lazy load per chromosome, CSV for large files

**Recent features**:
- Synthetic lethality tab (Dec 2025): `src/analysis/synthetic_lethality.py` joins Harle 2025 data with TCGA deletions
- Genomic distance in gene pairs table (start-to-start bp)
- DataTable numeric sorting with `page_action='native'`
- Cache bug fix (2024): Gene list hash now in cache keys (prevents chr13 served for all)
- Cache bug fix (2024): Gene list hash now in cache keys (prevents chr13 served for all)
