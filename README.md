# Co-Deletion Analysis Application

## Architecture Overview

This project follows a clean separation between ETL pipeline and visualization:

```
Cbioportal/
├── main.py                          # ETL pipeline (run first)
├── app.py                           # Dash application (run second)
├── data/
│   ├── cbioportal_client.py        # Low-level API wrapper
│   ├── queries.py                   # Domain-specific queries
│   ├── cache_utils.py               # Caching utilities
│   ├── processed_loader.py          # Load pre-processed data for Dash
│   ├── cached/                      # API response cache
│   └── processed/                   # Analysis outputs (Excel, HTML)
├── analysis/
│   └── codeletion_calc.py           # Statistical calculations
├── visualization/
│   └── codeletion_heatmap.py        # Plotly figure constructors
└── layouts/
    └── layout.py                    # Dash layout components
```

## Workflow

### 1. ETL Pipeline: `main.py` (Single Study)

**Purpose:** Fetch, process, and analyze data for PRAD study only

**Steps:**
1. Query cBioPortal API for CNA data
2. Build deletion matrix (samples × genes)
3. Compute co-deletion statistics
4. Export results to `data/processed/`

**Generated Files:**
- `chr13_genes_metadata.xlsx` - Gene info with cytobands
- `chr13_codeletion_conditional_frequencies.xlsx` - P(i|j) matrix
- `chr13_codeletion_frequencies.xlsx` - Long-format pairs
- `chr13_codeletion_matrix.xlsx` - Symmetric frequency matrix
- `chr13_codeletion_counts.xlsx` - Raw counts
- `chr13_conditional_codeletion_heatmap.html` - Standalone visualization

**Run:**
```bash
python main.py
```

### 1b. Batch Processing: `batch_process.py` (All TCGA Studies)

**Purpose:** Pre-compute chr13 co-deletions for all 32 TCGA PanCancer Atlas studies

**Input:** `data/curated_data/TCGA_study_names.csv` (list of study IDs)

**Process:**
- Reads study list from CSV
- Processes each study independently
- Saves results to `data/processed/{study_id}/`
- Generates summary report

**Generated Structure:**
```
data/processed/
├── prad_tcga_pan_can_atlas_2018/
│   ├── chr13_genes_metadata.xlsx
│   ├── chr13_codeletion_conditional_frequencies.xlsx
│   ├── chr13_codeletion_frequencies.xlsx
│   └── ...
├── brca_tcga_pan_can_atlas_2018/
│   └── ...
├── ...
└── processing_summary.xlsx
```

**Run:**
```bash
python batch_process.py
# Or use convenience script:
./run_batch.sh
```

**Expected Time:** ~30-60 minutes depending on API caching

### 2. Visualization: `app.py`

**Purpose:** Interactive Dash web application

**Features:**
- **Study selector** - Choose from all processed TCGA studies
- **Individual gene deletion frequency scatter plot** - Shows how often each gene is deleted (hover for gene name)
- Interactive heatmap with zoom/pan
- Configurable colorscale (Viridis, YlOrRd, Blues, etc.)
- Adjustable axis labels (5-50 labels)
- Top co-deleted gene pairs bar plot
- Dataset statistics display
- Export high-resolution images

**Data Source:** Loads pre-processed files from `data/processed/{study_id}/`

**Run:**
```bash
python app.py
```
Then open: http://127.0.0.1:8050

**Note:** Run `batch_process.py` first to generate data for multiple studies

## Key Components

### Data Layer (`data/`)

**`processed_loader.py`** - Loads pre-computed matrices for Dash
- `load_conditional_matrix()` - P(i|j) probabilities
- `load_frequency_matrix()` - Symmetric frequencies
- `load_codeletion_pairs()` - Long-format data
- `load_gene_metadata()` - Cytoband information

**`cbioportal_client.py`** - Low-level API wrapper
- Mirrors Swagger endpoints
- Automatic caching
- Returns raw JSON

**`queries.py`** - Domain-specific queries
- Combines multiple API calls
- Filters and transforms data
- Sorts genes by chromosomal position

### Analysis Layer (`analysis/`)

**`codeletion_calc.py`** - Statistical computations
- Co-deletion frequency matrix
- Conditional probabilities P(i|j)
- Top co-deleted pairs extraction

### Visualization Layer (`visualization/`)

**`codeletion_heatmap.py`** - Plotly figure constructors
- `create_heatmap_figure()` - Dash-compatible (no file I/O)
- `plot_heatmap()` - Standalone with HTML export
- `create_top_pairs_figure()` - Bar plot constructor

### Layout Layer (`layouts/`)

**`layout.py`** - Dash UI components
- Bootstrap-styled layout
- Interactive controls
- Statistics cards
- Responsive grid

### App Layer (`app.py`)

**Callbacks:**
1. `update_heatmap()` - Responds to colorscale/labels changes
2. `update_top_pairs()` - Updates bar plot for N pairs
3. `update_stats()` - Displays dataset statistics

## Design Principles

✅ **Separation of Concerns:**
- ETL (main.py) independent of visualization (app.py)
- Data processing separate from plotting

✅ **No File I/O in Visualization:**
- Dash uses pure Plotly constructors
- Figures generated in-memory

✅ **Caching Strategy:**
- API responses cached to `data/cached/`
- Processed results in `data/processed/`

✅ **Dash-Ready:**
- All visualizations return Plotly Figure objects
- Bootstrap components for professional UI
- Callbacks for interactivity

## Usage Example

### Using .venv Python (Recommended)

```bash
# Step 1: Activate virtual environment
source .venv/bin/activate

# Step 2: Run ETL pipeline
python main.py

# Step 3: Start Dash app
python app.py

# Step 4: Open browser
# Navigate to http://127.0.0.1:8050
```

### Using Convenience Scripts

```bash
# Step 1: Run ETL pipeline
./run_main.sh

# Step 2: Start Dash app
./run_app.sh

# Step 3: Open browser
# Navigate to http://127.0.0.1:8050
```

## Future Enhancements

- Multi-chromosome support (dropdowns for chr1-22, X, Y)
- Multi-study comparison (PRAD, BRCA, etc.)
- Gene search/filter functionality
- Download filtered datasets
- Custom threshold selection
- Network visualization of co-deletion clusters
