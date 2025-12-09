# TCGA Co-Deletion Analysis Application

Multi-page Dash application for analyzing gene co-deletion patterns across TCGA PanCancer Atlas studies.

## Architecture Overview

This project follows a clean separation between ETL pipeline and visualization:

```
Cbioportal/
├── main.py                          # ETL pipeline (single study/chromosome)
├── batch_process.py                 # ETL pipeline (all studies/chromosomes)
├── app.py                           # Multi-page Dash application
├── data/
│   ├── cbioportal_client.py        # Low-level API wrapper
│   ├── queries.py                   # Domain-specific queries
│   ├── cache_utils.py               # Caching utilities
│   ├── processed_loader.py          # Load pre-processed data for Dash
│   ├── cached/                      # API response cache
│   └── processed/                   # Analysis outputs (Excel/CSV)
├── analysis/
│   └── codeletion_calc.py           # Statistical calculations
├── visualization/
│   └── codeletion_heatmap.py        # Plotly figure constructors
└── layouts/
    ├── home.py                      # Homepage layout
    ├── codeletion.py                # Co-deletion explorer page
    └── summary.py                   # Summary statistics page
```

## Workflow

### 1. Batch Processing: `batch_process.py` (All TCGA Studies) - **RECOMMENDED**

**Purpose:** Pre-compute co-deletions for **all chromosomes (1-22, X, Y)** across all 32 TCGA PanCancer Atlas studies

**Input:** `data/curated_data/TCGA_study_names.csv` (list of study IDs)

**Process:**
- Reads study list from CSV
- Processes each study for all 24 chromosomes (1-22, X, Y)
- Saves results to `data/processed/{study_id}/`
- Generates summary report
- Total analyses: 32 studies × 24 chromosomes = 768 analyses

**Generated Structure:**
```
data/processed/
├── prad_tcga_pan_can_atlas_2018/
│   ├── chr1_genes_metadata.xlsx
│   ├── chr1_codeletion_conditional_frequencies.xlsx
│   ├── chr1_codeletion_frequencies.xlsx
│   ├── chr2_genes_metadata.xlsx
│   ├── chr2_codeletion_conditional_frequencies.xlsx
│   ├── ...
│   ├── chr13_genes_metadata.xlsx
│   ├── chr13_codeletion_conditional_frequencies.xlsx
│   ├── ...
│   ├── chrX_genes_metadata.xlsx
│   └── chrY_genes_metadata.xlsx
├── brca_tcga_pan_can_atlas_2018/
│   └── (same structure)
├── ...
└── processing_summary.xlsx
```

**Run:**
```bash
./run_batch.sh
# Or directly:
python batch_process.py

# Test mode (chr13 only, 2 studies):
python batch_process.py --test
```

**Expected Time:** 
- Full run (all chromosomes, all studies): ~8-12 hours
- Test mode (chr13 only, 2 studies): ~5-10 minutes

### 1b. Single Study Pipeline: `main.py` (Optional)

**Purpose:** Fetch, process, and analyze data for a single study and chromosome

**Steps:**
1. Query cBioPortal API for CNA data
2. Build deletion matrix (samples × genes)
3. Compute co-deletion statistics
4. Export results to `data/processed/`

**Usage:**
```bash
python main.py [chromosome] [study_id]

# Examples:
python main.py                    # Default: chr13, PRAD
python main.py 17                 # Chr17, PRAD
python main.py 13 brca_tcga_pan_can_atlas_2018  # Chr13, BRCA
python main.py X prad_tcga_pan_can_atlas_2018   # ChrX, PRAD
```

**Generated Files (per chromosome):**
- `chr{N}_genes_metadata.xlsx` - Gene info with cytobands
- `chr{N}_codeletion_conditional_frequencies.xlsx` - P(i|j) matrix
- `chr{N}_codeletion_frequencies.xlsx` - Long-format pairs
- `chr{N}_codeletion_matrix.xlsx` - Symmetric frequency matrix
- `chr{N}_codeletion_counts.xlsx` - Raw counts
- `chr{N}_conditional_codeletion_heatmap.html` - Standalone visualization

**Note:** This is now optional - use `batch_process.py` to process all studies and chromosomes at once

### 2. Visualization: `app.py` - Multi-Page Dash Application

**Purpose:** Interactive web application with multiple pages for data exploration and analysis

**Application Structure:**
- **Homepage** (`/`) - Landing page with navigation
- **Co-Deletion Explorer** (`/codeletion`) - Interactive analysis page
- **Summary Statistics** (`/summary`) - Overview across studies and chromosomes

**Co-Deletion Explorer Features:**
- **Study selector** - Choose from all processed TCGA studies (32 studies)
- **Chromosome selector** - Choose from chromosomes 1-22, X, or Y
- **Individual gene deletion frequency scatter plot** - Shows how often each gene is deleted (hover for gene name)
- Interactive heatmap with zoom/pan
- Configurable colorscale (Viridis, YlOrRd, Blues, etc.)
- Adjustable axis labels (5-50 labels)
- Top co-deleted gene pairs bar plot
- Dataset statistics display (dynamically updates per chromosome)
- Export high-resolution images

**Summary Statistics Features:**
- **Deletion Frequency Distribution** - Genome-wide view of deletion patterns by cytoband
  - X-axis: Genes ordered by chromosome and cytoband position
  - Y-axis: Deletion frequency (%)
  - Color-coded by chromosome
  - Only displays genes with deletions (frequency > 0)
  - Hover for gene symbol, cytoband, and exact deletion frequency
- Filter by study and chromosome
- Comparative visualizations across studies and chromosomes
- Detailed statistics tables (coming soon)

**Data Source:** Loads pre-processed files from `data/processed/{study_id}/chr{N}_*.xlsx` or `.csv`

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

**`home.py`** - Homepage layout
- Hero section with application description
- Navigation cards to other pages
- Feature overview

**`codeletion.py`** - Co-deletion explorer layout
- Study and chromosome selectors
- Interactive heatmap visualization
- Deletion frequency scatter plot
- Top co-deleted pairs bar chart
- Dataset statistics display

**`summary.py`** - Summary statistics layout
- Multi-study/chromosome filters
- Distribution visualizations
- Comparative analysis charts
- Detailed statistics tables

### App Layer (`app.py`)

**Routing:**
- URL-based page navigation with `dcc.Location`
- Dynamic page loading based on pathname
- 404 page for invalid routes

**Co-Deletion Explorer Callbacks:**
1. `populate_study_dropdown()` - Loads available studies
2. `update_visualizations()` - Updates all three charts (heatmap, scatter, bar)
3. `update_stats()` - Displays dataset statistics per chromosome

**Summary Page Callbacks:**
1. `populate_summary_study_dropdown()` - Loads study filter options
2. `update_summary_stats()` - Updates statistics cards
3. `update_summary_distribution()` - Genome-wide deletion frequency by cytoband
   - Aggregates data across all selected studies/chromosomes
   - Filters out genes with no deletions
   - Orders genes by chromosomal position
4. `update_chromosome_comparison()` - Chromosome comparison chart (placeholder)
5. `update_study_comparison()` - Study comparison chart (placeholder)
6. `update_summary_table()` - Detailed statistics table (placeholder)

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

## Quick Start

### 1. Install Dependencies

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

### 2. Process All TCGA Studies and Chromosomes

```bash
# Run batch processing for all 32 studies × 24 chromosomes (~8-12 hours)
./run_batch.sh

# OR: Test mode (chr13 only, 2 studies, ~5-10 minutes)
python batch_process.py --test
```

This will generate data for all TCGA PanCancer Atlas studies across all chromosomes (1-22, X, Y) and save results to `data/processed/{study_id}/chr{N}_*.xlsx`.

**Note:** The full run processes 768 analyses (32 studies × 24 chromosomes). You may want to start with test mode or process a single chromosome first.

### 3. Launch Interactive Application

```bash
# Start Dash web application
./run_app.sh

# Open browser and navigate to:
# http://127.0.0.1:8050
```

### Alternative: Manual Commands

```bash
# Activate virtual environment
source .venv/bin/activate

# Process all studies
python batch_process.py

# Start Dash app
python app.py
```

## Features

✅ **Multi-page application** - Separate pages for exploration, statistics, and navigation  
✅ **Multi-chromosome support** - Analyze all chromosomes (1-22, X, Y)  
✅ **Multi-study comparison** - 32 TCGA PanCancer Atlas studies  
✅ **Interactive visualizations** - Dash-powered heatmaps and scatter plots  
✅ **Genome-wide deletion visualization** - See deletion patterns across all genes and cytobands  
✅ **Batch processing** - Automated analysis pipeline for 768 analyses  
✅ **Cytoband-ordered displays** - Genes sorted by chromosomal position  
✅ **Smart caching** - Gene-specific cache keys for accurate data retrieval  
✅ **Large dataset handling** - CSV format for chromosomes with >1000 genes  

## Recent Updates

### Genome-Wide Deletion Frequency Visualization (v2.1)
- Implemented deletion frequency distribution by cytoband in Summary Statistics page
- Displays all genes with deletions across selected studies and chromosomes
- Genes ordered by chromosomal position for intuitive genomic context
- Color-coded by chromosome with interactive hover information
- Filters dynamically apply to show specific studies or chromosomes

### Multi-Page Application (v2.0)
- Converted to multi-page architecture with URL routing
- Added dedicated homepage with navigation
- Separated co-deletion explorer and summary statistics into distinct pages
- All existing functionality preserved and enhanced

### Cache Bug Fix
- Fixed critical caching issue causing incorrect data for non-chr13 chromosomes
- Implemented MD5-hashed gene IDs in cache keys for unique identification
- All 24 chromosomes now show accurate deletion frequencies

### Stats Display Improvements
- Clarified statistics: "Max Deletion Freq (%)" instead of misleading "Total Deletions"
- Added "Genes with Deletions" count for better dataset understanding

## AWS Deployment

This application is ready for deployment to AWS Elastic Beanstalk. See **[AWS_DEPLOYMENT_GUIDE.md](AWS_DEPLOYMENT_GUIDE.md)** for complete instructions.

### Quick Deployment Overview

**Prerequisites:**
- AWS account configured
- Processed data generated (`python batch_process.py`)
- AWS CLI and EB CLI installed

**Key Files for AWS:**
- `application.py` - Elastic Beanstalk entry point (exposes WSGI server)
- `requirements.txt` - Python dependencies
- `.ebextensions/01_python.config` - EB configuration
- `upload_data_to_s3.sh` - Helper script to upload processed data to S3

**Recommended Deployment Strategy:**

Since processed data is ~6.1GB (too large for GitHub), use AWS S3:

```bash
# 1. Upload data to S3
./upload_data_to_s3.sh tcga-codeletion-data

# 2. Initialize Elastic Beanstalk
eb init -p python-3.11 tcga-codeletion-app

# 3. Create environment with S3 configuration
eb create tcga-codeletion-env
eb setenv USE_S3=true S3_BUCKET=tcga-codeletion-data S3_PREFIX=processed/

# 4. Deploy
eb deploy
eb open
```

**Note:** Full deployment guide includes S3 integration code, IAM configuration, and troubleshooting steps.

## Future Enhancements

- Complete remaining summary statistics visualizations:
  - Chromosome comparison bar chart
  - Study comparison chart
  - Detailed statistics data table
- Gene search/filter functionality in co-deletion explorer
- Download filtered datasets from UI
- Custom deletion threshold selection
- Network visualization of co-deletion clusters
- Multi-study overlay comparisons in co-deletion heatmaps
- Statistical significance testing for co-deletions
