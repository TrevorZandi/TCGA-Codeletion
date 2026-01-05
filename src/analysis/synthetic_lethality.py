"""
Synthetic lethality analysis and integration with TCGA deletion data.

This module provides functions to:
1. Load and filter synthetic lethality data from Harle 2025 study
2. Calculate therapeutic opportunity scores
3. Join SL data with TCGA deletion frequencies
4. Aggregate deletion data genome-wide

Based on: Harle et al. 2025 - "A compendium of synthetic lethal gene pairs 
defined by extensive combinatorial pan-cancer CRISPR screening"
Genome Biology. https://doi.org/10.1186/s13059-025-03737-w
"""

import os
import pandas as pd
import numpy as np
from typing import Optional, Dict, List, Tuple
from io import BytesIO

# Module directory for relative paths
MODULE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(os.path.dirname(MODULE_DIR), 'documentation')

# S3 configuration
USE_S3 = os.environ.get('USE_S3', 'false').lower() == 'true'
S3_BUCKET = os.environ.get('S3_BUCKET', 'tcga-codeletion-data')
S3_SL_KEY = 'synthetic_lethality/SyntheticLethalData_Harle_2025.csv'


def load_synthetic_lethal_data(
    fdr_threshold: float = 0.05,
    min_gi_score: Optional[float] = None,
    source_types: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Load and filter synthetic lethality data from Harle 2025 study.
    
    Loads from S3 if USE_S3=true, otherwise from local documentation/ folder.
    
    Args:
        fdr_threshold: Maximum FDR to include (default 0.05 = 5%)
        min_gi_score: Minimum absolute genetic interaction score (default None = no filter)
        source_types: List of sgRNA group types to include. Options:
                     ['Paralog', 'Project Achilles/MASHUP', 'CRISPR/RNA-Seq']
                     (default None = include all)
    
    Returns:
        DataFrame with columns:
        - sorted_gene_pair: "GeneA|GeneB" format
        - targetA, targetB: Individual gene symbols
        - mean_norm_gi: Genetic interaction score (negative = synthetic lethal)
        - fdr: False discovery rate
        - cancer_type: Melanoma, NSCLC, or Pancreas
        - cell_line_label: Cell line identifier
        - targetA/B__is_common_essential_bagel2: Common essential flags
        - targetA/B__n_depmap_dependent_cell_lines: "N/1086" format
        - sgrna_group.x: Data source type
    """
    # Load data from S3 or local
    if USE_S3:
        import boto3
        s3 = boto3.client('s3')
        try:
            obj = s3.get_object(Bucket=S3_BUCKET, Key=S3_SL_KEY)
            df = pd.read_csv(BytesIO(obj['Body'].read()))
        except Exception as e:
            raise FileNotFoundError(
                f"Failed to load synthetic lethality data from S3: "
                f"s3://{S3_BUCKET}/{S3_SL_KEY} - {str(e)}"
            )
    else:
        csv_path = os.path.join(DATA_DIR, 'SyntheticLethalData_Harle_2025.csv')
        if not os.path.exists(csv_path):
            raise FileNotFoundError(
                f"Synthetic lethality data not found at: {csv_path}\n"
                f"Expected file: SyntheticLethalData_Harle_2025.csv\n"
                f"Please ensure the data file exists in the documentation/ folder."
            )
        df = pd.read_csv(csv_path)
    
    # Apply filters
    filtered = df[df['fdr'] <= fdr_threshold].copy()
    
    if min_gi_score is not None:
        filtered = filtered[filtered['mean_norm_gi'].abs() >= min_gi_score]
    
    if source_types is not None:
        filtered = filtered[filtered['sgrna_group.x'].isin(source_types)]
    
    return filtered


def parse_depmap_count(depmap_str: str) -> Tuple[int, int]:
    """
    Parse DepMap dependency count from "N/1086" format.
    
    Args:
        depmap_str: String like "749/1086"
    
    Returns:
        Tuple of (dependent_lines, total_lines)
    """
    if pd.isna(depmap_str):
        return (0, 1086)
    
    try:
        parts = str(depmap_str).split('/')
        return (int(parts[0]), int(parts[1]))
    except:
        return (0, 1086)


def calculate_hit_frequency(sl_data: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate how many cell lines each SL pair was validated in.
    
    Args:
        sl_data: Synthetic lethality DataFrame from load_synthetic_lethal_data()
    
    Returns:
        DataFrame with columns:
        - sorted_gene_pair: "GeneA|GeneB"
        - hit_count: Number of cell lines (out of 27) showing SL
        - hit_fraction: Fraction of cell lines (0-1)
        - cancer_types_validated: Comma-separated list of cancer types
        - cell_lines_validated: Comma-separated list of cell line labels
    """
    # Group by gene pair
    grouped = sl_data.groupby('sorted_gene_pair').agg({
        'cell_line_label': lambda x: ','.join(sorted(set(x))),
        'cancer_type': lambda x: ','.join(sorted(set(x)))
    }).reset_index()
    
    # Count unique cell lines
    grouped['hit_count'] = grouped['cell_line_label'].apply(lambda x: len(x.split(',')))
    grouped['hit_fraction'] = grouped['hit_count'] / 27.0
    
    # Rename for clarity
    grouped.rename(columns={
        'cell_line_label': 'cell_lines_validated',
        'cancer_type': 'cancer_types_validated'
    }, inplace=True)
    
    return grouped


def calculate_therapeutic_score(
    del_freq: float,
    gi_score: float,
    is_essential_bagel2: bool,
    depmap_dependent_count: int,
    hit_frequency: Optional[float] = None
) -> float:
    """
    Calculate therapeutic opportunity score for a SL gene pair.
    
    Formula: del_freq × |gi_score| × essentiality_weight × context_weight
    
    Essentiality weights:
    - 2.0: Common essential (BAGEL2) - validated in knockout mice
    - 1.5: Context-dependent (>50% DepMap lines) - broader applicability
    - 1.0: Baseline
    
    Context weights (optional, requires hit_frequency):
    - Based on validation breadth: 0.5 + (hit_freq) × 1.5
    - Range: 0.5 (rare) to 2.0 (universal)
    
    Args:
        del_freq: Deletion frequency (0-1) for the deleted gene
        gi_score: Genetic interaction score (negative = SL)
        is_essential_bagel2: Whether target is common essential
        depmap_dependent_count: Number of cell lines dependent on target (out of 1086)
        hit_frequency: Optional - fraction of 27 cell lines showing SL (0-1)
    
    Returns:
        Therapeutic score (higher = better opportunity)
    """
    # Essentiality weight
    if is_essential_bagel2:
        ess_weight = 2.0  # Validated safe targets
    elif depmap_dependent_count / 1086 > 0.5:
        ess_weight = 1.5  # Broadly relevant
    else:
        ess_weight = 1.0
    
    # Context weight (how consistently validated)
    if hit_frequency is not None:
        context_weight = 0.5 + (hit_frequency * 1.5)
    else:
        context_weight = 1.0
    
    # Final score
    score = del_freq * abs(gi_score) * ess_weight * context_weight
    
    return score


def aggregate_deletions_genome_wide(
    study_id: str,
    chromosomes: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Load and aggregate deletion frequencies across all chromosomes for a study.
    
    Args:
        study_id: TCGA study identifier (e.g., 'prad_tcga_pan_can_atlas_2018')
        chromosomes: List of chromosomes to include (default: all 1-22, X, Y)
    
    Returns:
        DataFrame with columns:
        - gene: Gene symbol (e.g., "TP53")
        - entrez_id: Entrez gene ID
        - chromosome: Chromosome location
        - deletion_frequency: Fraction of samples with deletion (0-1)
    """
    from data import processed_loader
    
    if chromosomes is None:
        chromosomes = [str(i) for i in range(1, 23)] + ['X', 'Y']
    
    all_deletions = []
    
    for chr_num in chromosomes:
        try:
            # Load deletion frequencies for this chromosome
            del_freq_series = processed_loader.load_deletion_frequencies(chr_num, study_id)
            
            # Convert Series to DataFrame format
            for gene_name, freq in del_freq_series.items():
                # Extract symbol from "SYMBOL (ENTREZ)" format
                if ' (' in gene_name:
                    symbol = gene_name.split(' (')[0]
                    entrez_str = gene_name.split('(')[1].rstrip(')')
                    try:
                        entrez_id = int(entrez_str)
                    except:
                        entrez_id = None
                else:
                    symbol = gene_name
                    entrez_id = None
                
                all_deletions.append({
                    'gene': symbol,
                    'entrez_id': entrez_id,
                    'chromosome': chr_num,
                    'deletion_frequency': freq
                })
        
        except FileNotFoundError:
            # Chromosome data not available for this study
            continue
    
    return pd.DataFrame(all_deletions)


def join_deletion_with_synthetic_lethality(
    deletion_df: pd.DataFrame,
    sl_data: pd.DataFrame,
    hit_frequency_df: Optional[pd.DataFrame] = None,
    min_deletion_freq: float = 0.05
) -> pd.DataFrame:
    """
    Join TCGA deletion data with synthetic lethality pairs.
    
    Creates bidirectional opportunities:
    - If A is deleted, target B
    - If B is deleted, target A
    
    Args:
        deletion_df: Output from aggregate_deletions_genome_wide()
        sl_data: Output from load_synthetic_lethal_data()
        hit_frequency_df: Optional output from calculate_hit_frequency()
        min_deletion_freq: Minimum deletion frequency to include (default 0.05 = 5%)
    
    Returns:
        DataFrame with columns:
        - deleted_gene: The gene that is deleted in cancer
        - target_gene: The gene to inhibit (SL partner)
        - deletion_frequency: Frequency of deleted_gene deletion
        - gi_score: Genetic interaction score
        - fdr: False discovery rate
        - target_is_common_essential: BAGEL2 flag for target
        - target_depmap_dependent_lines: Number of lines dependent on target
        - hit_count: Number of cell lines validated (if hit_frequency_df provided)
        - cancer_types_validated: Cancer types where validated
    """
    # Filter deletions by minimum frequency
    deletion_df = deletion_df[deletion_df['deletion_frequency'] >= min_deletion_freq].copy()
    
    # Get representative row per gene pair (average across cell lines)
    sl_summary = sl_data.groupby('sorted_gene_pair').agg({
        'targetA': 'first',
        'targetB': 'first',
        'mean_norm_gi': 'mean',
        'fdr': 'min',  # Most significant FDR
        'targetA__is_common_essential_bagel2': 'first',
        'targetB__is_common_essential_bagel2': 'first',
        'targetA__n_depmap_dependent_cell_lines': 'first',
        'targetB__n_depmap_dependent_cell_lines': 'first'
    }).reset_index()
    
    # Parse DepMap counts
    sl_summary['targetA_depmap_count'] = sl_summary['targetA__n_depmap_dependent_cell_lines'].apply(
        lambda x: parse_depmap_count(x)[0]
    )
    sl_summary['targetB_depmap_count'] = sl_summary['targetB__n_depmap_dependent_cell_lines'].apply(
        lambda x: parse_depmap_count(x)[0]
    )
    
    # Merge with hit frequency if provided
    if hit_frequency_df is not None:
        sl_summary = sl_summary.merge(hit_frequency_df, on='sorted_gene_pair', how='left')
    
    opportunities = []
    
    # Create bidirectional opportunities
    for _, sl_row in sl_summary.iterrows():
        gene_a = sl_row['targetA']
        gene_b = sl_row['targetB']
        
        # Opportunity 1: A is deleted → target B
        a_deletions = deletion_df[deletion_df['gene'] == gene_a]
        if not a_deletions.empty:
            del_freq_a = a_deletions.iloc[0]['deletion_frequency']
            
            opp = {
                'deleted_gene': gene_a,
                'target_gene': gene_b,
                'deletion_frequency': del_freq_a,
                'gi_score': sl_row['mean_norm_gi'],
                'fdr': sl_row['fdr'],
                'target_is_common_essential': bool(sl_row['targetB__is_common_essential_bagel2']),
                'target_depmap_dependent_lines': sl_row['targetB_depmap_count']
            }
            
            if hit_frequency_df is not None:
                opp['hit_count'] = sl_row.get('hit_count', 0)
                opp['hit_fraction'] = sl_row.get('hit_fraction', 0.0)
                opp['cancer_types_validated'] = sl_row.get('cancer_types_validated', '')
            
            opportunities.append(opp)
        
        # Opportunity 2: B is deleted → target A
        b_deletions = deletion_df[deletion_df['gene'] == gene_b]
        if not b_deletions.empty:
            del_freq_b = b_deletions.iloc[0]['deletion_frequency']
            
            opp = {
                'deleted_gene': gene_b,
                'target_gene': gene_a,
                'deletion_frequency': del_freq_b,
                'gi_score': sl_row['mean_norm_gi'],
                'fdr': sl_row['fdr'],
                'target_is_common_essential': bool(sl_row['targetA__is_common_essential_bagel2']),
                'target_depmap_dependent_lines': sl_row['targetA_depmap_count']
            }
            
            if hit_frequency_df is not None:
                opp['hit_count'] = sl_row.get('hit_count', 0)
                opp['hit_fraction'] = sl_row.get('hit_fraction', 0.0)
                opp['cancer_types_validated'] = sl_row.get('cancer_types_validated', '')
            
            opportunities.append(opp)
    
    result_df = pd.DataFrame(opportunities)
    
    # Sort by deletion frequency (descending), then by absolute GI score (descending)
    if not result_df.empty:
        result_df = result_df.sort_values(
            ['deletion_frequency', 'gi_score'],
            ascending=[False, True]  # True for gi_score because it's negative (more negative = stronger)
        ).reset_index(drop=True)
    
    return result_df


def compare_across_studies(
    study_ids: List[str],
    fdr_threshold: float = 0.05,
    min_deletion_freq: float = 0.05
) -> pd.DataFrame:
    """
    Compare therapeutic opportunities across multiple TCGA studies.
    
    Args:
        study_ids: List of TCGA study identifiers
        fdr_threshold: FDR cutoff for SL data
        min_deletion_freq: Minimum deletion frequency threshold
    
    Returns:
        DataFrame with columns from join_deletion_with_synthetic_lethality()
        plus 'study_id' and 'study_name' columns
    """
    from data.cbioportal_client import get_studies
    
    # Load SL data once
    sl_data = load_synthetic_lethal_data(fdr_threshold=fdr_threshold)
    hit_freq_df = calculate_hit_frequency(sl_data)
    
    # Get study names
    all_studies = get_studies()
    study_name_map = {s['studyId']: s['name'] for s in all_studies}
    
    all_opportunities = []
    
    for study_id in study_ids:
        try:
            # Load genome-wide deletions
            deletions = aggregate_deletions_genome_wide(study_id)
            
            # Join with SL data
            opportunities = join_deletion_with_synthetic_lethality(
                deletion_df=deletions,
                sl_data=sl_data,
                hit_frequency_df=hit_freq_df,
                min_deletion_freq=min_deletion_freq
            )
            
            # Add study info
            opportunities['study_id'] = study_id
            opportunities['study_name'] = study_name_map.get(study_id, study_id)
            
            all_opportunities.append(opportunities)
        
        except Exception as e:
            print(f"Warning: Failed to process {study_id}: {str(e)}")
            continue
    
    if all_opportunities:
        result = pd.concat(all_opportunities, ignore_index=True)
        return result.sort_values(['deletion_frequency', 'gi_score'], ascending=[False, True])
    else:
        return pd.DataFrame()
