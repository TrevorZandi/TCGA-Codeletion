# TCGA Co-Deletion Analysis Application

Multi-page Dash application for analyzing gene co-deletion patterns and identifying synthetic lethality therapeutic opportunities across TCGA PanCancer Atlas studies.

## Architecture Overview

This project follows a clean separation between ETL pipeline and visualization:

```
TCGA-Codeletion/
├── src/                             # Main application code
│   ├── app.py                       # Multi-page Dash application
│   ├── application.py               # AWS WSGI entry point
│   ├── main.py                      # ETL pipeline (single study/chromosome)
│   ├── batch_process.py             # ETL pipeline (all studies/chromosomes)
│   ├── data/
│   │   ├── cbioportal_client.py    # Low-level API wrapper
│   │   ├── queries.py               # Domain-specific queries
│   │   ├── cache_utils.py           # Caching utilities
│   │   └── processed_loader.py      # Load pre-processed data for Dash
│   ├── analysis/
│   │   ├── codeletion_calc.py       # Statistical calculations
│   │   └── synthetic_lethality.py   # SL data integration and analysis
│   ├── visualization/
│   │   ├── codeletion_heatmap.py    # Plotly figure constructors
│   │   └── target_discovery.py      # SL visualization constructors
│   └── layouts/
│       ├── home.py                  # Homepage layout
│       ├── codeletion.py            # Co-deletion explorer page
│       ├── summary.py               # Summary statistics page
│       └── target_discovery_tab.py  # Synthetic lethality tab
├── data/
│   ├── cached/                      # API response cache
│   ├── processed/                   # Analysis outputs (Excel/CSV)
│   └── curated_data/                # Study lists and reference data
├── scripts/                         # Utility and deployment scripts
│   ├── run_app.sh                   # Launch Dash application
│   ├── run_batch.sh                 # Run batch processing
│   ├── update_gene_metadata.py      # Update gene metadata
│   └── upload_data_to_s3.sh         # Deploy data to AWS S3
├── tests/                           # Test and debug scripts
├── docs/                            # Documentation (see docs/README.md)
│   ├── deployment/                  # AWS deployment guides
│   ├── implementation/              # Feature implementation docs
│   ├── api/                         # cBioPortal API documentation
│   └── references/                  # Research papers and datasets
└── application.py                   # Symlink to src/application.py (AWS EB)
```

## Workflow

### 1. Batch Processing: `src/batch_process.py` (All TCGA Studies) - **RECOMMENDED**

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
./scripts/run_batch.sh
# Or directly:
python src/batch_process.py

# Test mode (chr13 only, 2 studies):
python src/batch_process.py --test
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
python src/main.py [chromosome] [study_id]

# Examples:
python src/main.py                    # Default: chr13, PRAD
python src/main.py 17                 # Chr17, PRAD
python src/main.py 13 brca_tcga_pan_can_atlas_2018  # Chr13, BRCA
python src/main.py X prad_tcga_pan_can_atlas_2018   # ChrX, PRAD
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
- **Multiple analysis tabs:**
  - **Co-Deletion Analysis** - Interactive heatmap with zoom/pan, configurable colorscale, adjustable axis labels
  - **Deletion Frequencies** - Scatter plot showing individual gene deletion frequencies
  - **Top Pairs** - Bar chart of most frequently co-deleted gene pairs
  - **Synthetic Lethality Targets** - Therapeutic opportunity discovery (see below)
- Dataset statistics display (dynamically updates per chromosome)
- Export high-resolution images

**Synthetic Lethality Targets Tab:** 🆕
Identifies therapeutic opportunities by integrating TCGA deletion data with experimentally validated synthetic lethal gene pairs from Harle et al. 2025.

**Key Features:**
- **Therapeutic Opportunity Table** - Sortable/filterable list of deletion-SL target pairs
  - Deleted gene (lost in cancer)
  - Target gene (synthetic lethal partner to inhibit)
  - Deletion frequency in selected study
  - GI score (genetic interaction strength, more negative = stronger SL)
  - FDR (statistical significance)
  - Target essentiality (BAGEL2 common essential flag)
  - DepMap dependency (number of cell lines dependent on target)
  - Validation breadth (tested in 27 cell lines across 3 cancer types)

- **GI Score Scatter Plot** - Deletion frequency vs synthetic lethality strength
  - X-axis: How often the gene is deleted in the study
  - Y-axis: GI score (strength of synthetic lethality)
  - Color-coded by target essentiality (green = core essential/safer targets)
  - Bubble size proportional to deletion frequency
  - Hover for detailed information including validation across cancer types

- **Top Targets Bar Chart** - Genes with strongest average synthetic lethal interactions
  - Ranked by average absolute GI score
  - Shows number of distinct SL opportunities per target
  - Color-coded by essentiality status

**Interactive Filters:**
- FDR threshold (0.001 - 0.1, default 0.05)
- Minimum deletion frequency (1% - 50%, default 5%)
- Essentiality filter (All / Essential only / Non-essential only)

**Data Source:** 
Harle A, et al. (2025). "A compendium of synthetic lethal gene pairs defined by extensive combinatorial pan-cancer CRISPR screening." *Genome Biology*. DOI: [10.1186/s13059-025-03737-w](https://doi.org/10.1186/s13059-025-03737-w)
- 472 gene pairs tested across 27 cell lines (8 melanoma, 10 NSCLC, 9 pancreatic)
- Quantitative GI scores with FDR significance
- Essentiality annotations from BAGEL2 and DepMap

**Use Case:** For a given TCGA study, identify which synthetic lethal targets are most relevant based on:
1. Deletion frequency in patient samples (clinical relevance)
2. Strength of synthetic lethality (biological effect size)
3. Target safety profile (essentiality status)
4. Validation robustness (consistency across cell lines and cancer types)

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
./scripts/run_app.sh
# Or directly:
python src/app.py
```
Then open: http://127.0.0.1:8050

**Note:** Run `src/batch_process.py` first to generate data for multiple studies
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

### Analysis Layer (`src/analysis/`)

**`codeletion_calc.py`** - Statistical computations
- Co-deletion frequency matrix
- Conditional probabilities P(i|j)
- Top co-deleted pairs extraction

**`synthetic_lethality.py`** - Synthetic lethality integration 🆕
- `load_synthetic_lethal_data()` - Load and filter Harle 2025 dataset from S3/local
- `calculate_hit_frequency()` - Aggregate validation across 27 cell lines
- `aggregate_deletions_genome_wide()` - Load deletion data across all 24 chromosomes
- `join_deletion_with_synthetic_lethality()` - Create bidirectional therapeutic opportunities
  - For each SL pair (A, B): if A deleted → target B, if B deleted → target A
  - Filters by minimum deletion frequency threshold
  - Annotates with essentiality and validation data
- `compare_across_studies()` - Multi-study comparison of opportunities

### Visualization Layer (`src/visualization/`)

**`codeletion_heatmap.py`** - Plotly figure constructors
- `create_heatmap_figure()` - Dash-compatible (no file I/O)
- `plot_heatmap()` - Standalone with HTML export
- `create_top_pairs_figure()` - Bar plot constructor

**`target_discovery.py`** - Synthetic lethality visualizations 🆕
- `create_target_ranking_table()` - Interactive DataTable with sort/filter
  - Displays deletion-target pairs with all metadata
  - Numeric formatting for percentages and scientific notation
  - Essentiality highlighting
- `create_gi_score_scatter()` - Deletion frequency vs GI score scatter plot
  - Color-coded by target essentiality
  - Custom hover text with full opportunity details
  - Direct `go.Scatter` implementation for accurate positioning
- `create_target_gene_ranking_bar()` - Top targets by average GI score
  - Aggregates opportunities per target gene
  - Shows average strength of synthetic lethality
- `create_study_comparison_heatmap()` - Cross-study comparison matrix (future enhancement)

### Layout Layer (`src/layouts/`)

**`home.py`** - Homepage layout
- Hero section with application description
- Navigation cards to other pages
- Feature overview

**`codeletion.py`** - Co-deletion explorer layout
- Study and chromosome selectors
- Interactive heatmap visualization
- Deletion frequency scatter plot
- Top co-deleted pairs bar chart
- Synthetic lethality targets tab 🆕
- Dataset statistics display

**`target_discovery_tab.py`** - Synthetic lethality tab layout 🆕
- Filter controls (FDR threshold, min deletion freq, essentiality)
- Three visualization sub-tabs (table, scatter, bar chart)
- Information alert explaining synthetic lethality concept
- Harle et al. 2025 citation with DOI link

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

**Synthetic Lethality Callbacks:** 🆕
1. `populate_target_study_dropdown()` - Loads available studies for SL analysis
2. `update_target_discovery_viz()` - Main callback for SL tab
   - Loads Harle 2025 dataset with FDR filtering
   - Aggregates genome-wide deletions (all 24 chromosomes)
   - Joins to create therapeutic opportunities
   - Applies essentiality and deletion frequency filters
   - Routes to appropriate visualization (table/scatter/bar)
   - Handles empty results with informative messages

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
./scripts/run_batch.sh

# OR: Test mode (chr13 only, 2 studies, ~5-10 minutes)
python src/batch_process.py --test
```

This will generate data for all TCGA PanCancer Atlas studies across all chromosomes (1-22, X, Y) and save results to `data/processed/{study_id}/chr{N}_*.xlsx`.

**Note:** The full run processes 768 analyses (32 studies × 24 chromosomes). You may want to start with test mode or process a single chromosome first.

### 3. Launch Interactive Application

```bash
# Start Dash web application
./scripts/run_app.sh

# Open browser and navigate to:
# http://127.0.0.1:8050
```

### Alternative: Manual Commands

```bash
# Activate virtual environment
source .venv/bin/activate

# Process all studies
python src/batch_process.py

# Start Dash app
python src/app.py
```

## Features

✅ **Multi-page application** - Separate pages for exploration, statistics, and navigation  
✅ **Multi-chromosome support** - Analyze all chromosomes (1-22, X, Y)  
✅ **Multi-study comparison** - 32 TCGA PanCancer Atlas studies  
✅ **Interactive visualizations** - Dash-powered heatmaps and scatter plots  
✅ **Synthetic lethality integration** 🆕 - Identify therapeutic opportunities from deletion data  
✅ **Genome-wide deletion visualization** - See deletion patterns across all genes and cytobands  
✅ **Batch processing** - Automated analysis pipeline for 768 analyses  
✅ **Cytoband-ordered displays** - Genes sorted by chromosomal position  
✅ **Smart caching** - Gene-specific cache keys for accurate data retrieval  
✅ **Large dataset handling** - CSV format for chromosomes with >1000 genes  
✅ **S3 data integration** - Load processed data and SL dataset from AWS S3  

## Recent Updates

### Synthetic Lethality Target Discovery (v3.0) 🆕
**December 2025**
- Integrated Harle et al. 2025 synthetic lethality dataset (472 gene pairs, 27 cell lines)
- New "Synthetic Lethality Targets" tab in Co-Deletion Explorer
- Genome-wide deletion aggregation across all 24 chromosomes
- Bidirectional opportunity creation (A deleted → target B, B deleted → target A)
- Interactive filtering by FDR, deletion frequency, and target essentiality
- Three visualization modes:
  - Sortable/filterable opportunity table
  - Deletion frequency vs GI score scatter plot
  - Top targets ranked by average GI score
- S3 integration for SL dataset (proper data/code separation)
- Essentiality annotations from BAGEL2 and DepMap (1086 cell lines)
- Validation metadata across 3 cancer types (melanoma, NSCLC, pancreatic)

**Key insight:** Enables translational research by connecting TCGA genomic deletions with experimentally validated drug target opportunities.

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

This application is ready for deployment to AWS Elastic Beanstalk. See **[docs/deployment/AWS_DEPLOYMENT_GUIDE.md](docs/deployment/AWS_DEPLOYMENT_GUIDE.md)** for complete instructions.

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
./scripts/upload_data_to_s3.sh tcga-codeletion-data

# 2. Initialize Elastic Beanstalk
eb init -p python-3.14 tcga-codeletion-app

# 3. Create environment with S3 configuration
eb create tcga-codeletion-env
eb setenv USE_S3=true S3_BUCKET=tcga-codeletion-data S3_PREFIX=processed/

# 4. Deploy
eb deploy
eb open
```

**Note:** Full deployment guide includes S3 integration code, IAM configuration, and troubleshooting steps.

## Future Enhancements

### Co-Deletion Analysis
- Gene search/filter functionality in co-deletion explorer
- Download filtered datasets from UI
- Custom deletion threshold selection
- Network visualization of co-deletion clusters
- Multi-study overlay comparisons in co-deletion heatmaps
- Statistical significance testing for co-deletions

### Synthetic Lethality
- Custom therapeutic scoring system (user-defined weights for deletion freq, GI score, essentiality)
- Multi-study comparison heatmap for cross-cancer analysis
- Integration with drug databases (DrugBank, ChEMBL) for existing inhibitors
- Expression data integration (TCGA RNA-Seq) for target validation
- Patient stratification: which patients would benefit most from each target
- Network analysis: identify master regulators in SL networks
- Clinical trial matching based on deletion profiles

### Summary Statistics
- Complete remaining summary statistics visualizations:
  - Chromosome comparison bar chart
  - Study comparison chart
  - Detailed statistics data table
- Genome-wide synthetic lethality opportunity heatmap

## Citations

**TCGA Data:**
The Cancer Genome Atlas Research Network. (2013-2018). TCGA Pan-Cancer Atlas. [https://www.cell.com/pb-assets/consortium/pancanceratlas/pancani3/index.html](https://www.cell.com/pb-assets/consortium/pancanceratlas/pancani3/index.html)

**Synthetic Lethality Data:**
Harle A, Alpsoy A, Rauscher B, et al. (2025). A compendium of synthetic lethal gene pairs defined by extensive combinatorial pan-cancer CRISPR screening. *Genome Biology*, 26, Article 14. DOI: [10.1186/s13059-025-03737-w](https://doi.org/10.1186/s13059-025-03737-w)

**cBioPortal API:**
Cerami E, Gao J, Dogrusoz U, et al. (2012). The cBio Cancer Genomics Portal: An Open Platform for Exploring Multidimensional Cancer Genomics Data. *Cancer Discovery*, 2(5), 401-404.
