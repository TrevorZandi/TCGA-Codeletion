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
```

### Core Statistical Computation

**Conditional probabilities** are THE core metric (`analysis/codeletion_calc.py`):
- `P(A,B)` = Joint probability both genes deleted (from co-occurrence counts)
- `P(A|B)` = Conditional probability A deleted given B deleted = `count(A,B) / count(B,B)`
- The heatmap shows `P(A|B)`, NOT `P(A,B)` - this is asymmetric!
- Diagonal values are always 1.0 (a gene co-deletes with itself 100%)

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

# 4. Launch Dash app
python app.py  # Opens on http://127.0.0.1:8050

# 5. Upload metadata to S3 (after updating gene positions)
./run_update_metadata.sh
```

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

- **Test data**: `data/curated_data/test_studies.csv` (PRAD, BRCA only)
- **Quick test**: `python batch_process.py --test` (chr13 only, 2 studies)
- **Check processed outputs**: Verify files exist in `data/processed/{study}/chr{N}_*.xlsx`
- **AWS local testing**: `export USE_S3=false && python app.py` (uses local files)
- **S3 debugging**: Check IAM permissions and bucket/prefix environment variables

## External Dependencies & Integration

- **cBioPortal API**: `https://www.cbioportal.org/api` - Swagger docs in `documentation/Cbioportal_api_doc.json`
- **TCGA Data**: PanCancer Atlas 2018 studies (32 studies) - citation required in footer
- **AWS Services**: S3 (data storage), Elastic Beanstalk (app hosting), IAM (permissions)
- **Dash/Plotly**: v2.x for web framework, Bootstrap theme for UI components

## Recent Changes

- **Genomic distance feature**: Added `Distance (bp)` column to gene pairs table (requires updated metadata in S3)
- **Table improvements**: Numeric sorting, filter across all rows, conditional probabilities instead of joint
- **Footer citations**: TCGA Research Network citation and Trevor A. Zandi credit on all pages
- **Metadata updates**: Script `update_gene_metadata.py` regenerates files with genomic positions
