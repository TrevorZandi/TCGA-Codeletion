"""
Data loader for processed co-deletion analysis results.

This module provides functions to load pre-computed co-deletion matrices
and statistics from the data/processed directory for visualization in Dash.
"""

import os
import pandas as pd


def get_processed_dir(study_id=None):
    """
    Get the path to the processed data directory.
    
    Args:
        study_id: Optional study ID for study-specific subdirectory
    
    Returns:
        Absolute path to data/processed/ or data/processed/{study_id}/
    """
    module_dir = os.path.dirname(__file__)
    processed_dir = os.path.join(module_dir, "processed")
    
    if study_id is not None:
        return os.path.join(processed_dir, study_id)
    
    return processed_dir


def load_conditional_matrix(chromosome="13", study_id="prad_tcga_pan_can_atlas_2018"):
    """
    Load conditional co-deletion probability matrix.
    
    Args:
        chromosome: Chromosome number (default: "13")
        study_id: Full study identifier (default: "prad_tcga_pan_can_atlas_2018")
        
    Returns:
        DataFrame with conditional probabilities P(i|j)
    """
    processed_dir = get_processed_dir(study_id)
    filename = f"chr{chromosome}_codeletion_conditional_frequencies.xlsx"
    filepath = os.path.join(processed_dir, filename)
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Conditional matrix not found: {filepath}")
    
    df = pd.read_excel(filepath, index_col=0)
    return df


def load_frequency_matrix(chromosome="13", study_id="prad_tcga_pan_can_atlas_2018"):
    """
    Load co-deletion frequency matrix (symmetric).
    
    Args:
        chromosome: Chromosome number (default: "13")
        study_id: Full study identifier (default: "prad_tcga_pan_can_atlas_2018")
        
    Returns:
        DataFrame with co-deletion frequencies
    """
    processed_dir = get_processed_dir(study_id)
    filename = f"chr{chromosome}_codeletion_matrix.xlsx"
    filepath = os.path.join(processed_dir, filename)
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Frequency matrix not found: {filepath}")
    
    df = pd.read_excel(filepath, index_col=0)
    return df


def load_codeletion_pairs(chromosome="13", study_id="prad_tcga_pan_can_atlas_2018"):
    """
    Load long-format co-deletion frequency data.
    
    Args:
        chromosome: Chromosome number (default: "13")
        study_id: Full study identifier (default: "prad_tcga_pan_can_atlas_2018")
        
    Returns:
        DataFrame with columns: gene_i, gene_j, co_deletion_frequency
    """
    processed_dir = get_processed_dir(study_id)
    filename = f"chr{chromosome}_codeletion_frequencies.xlsx"
    filepath = os.path.join(processed_dir, filename)
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Co-deletion pairs not found: {filepath}")
    
    df = pd.read_excel(filepath)
    return df


def load_deletion_matrix(chromosome="13", study="prad"):
    """
    Load binary deletion matrix (samples x genes).
    
    Args:
        chromosome: Chromosome number (default: "13")
        study: Study identifier (default: "prad")
        
    Returns:
        DataFrame with samples as rows, genes as columns, 0/1 values
    """
    processed_dir = get_processed_dir()
    # This file is not currently saved by main.py, but could be added
    filename = f"chr{chromosome}_deletion_matrix.xlsx"
    filepath = os.path.join(processed_dir, filename)
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"Deletion matrix not found: {filepath}. "
            "Run main.py to generate processed data."
        )
    
    df = pd.read_excel(filepath, index_col=0)
    return df


def get_dataset_stats(conditional_matrix):
    """
    Extract dataset statistics from conditional matrix.
    
    Args:
        conditional_matrix: DataFrame with conditional probabilities
        
    Returns:
        Dictionary with keys: n_genes, n_samples, n_deletions
    """
    n_genes = conditional_matrix.shape[0]
    
    # Calculate approximate statistics
    # Note: For exact stats, we'd need the original deletion matrix
    stats = {
        'n_genes': n_genes,
        'n_samples': None,  # Would need deletion matrix
        'n_deletions': None  # Would need deletion matrix
    }
    
    return stats


def get_cytobands_from_genes(conditional_matrix):
    """
    Extract cytoband information from gene column names.
    
    Args:
        conditional_matrix: DataFrame with gene columns formatted as "SYMBOL (ENTREZ)"
        
    Returns:
        List of gene symbols (cytobands would need to be loaded separately)
    """
    # Gene columns are formatted as "SYMBOL (ENTREZ)"
    gene_symbols = [col.split(' ')[0] for col in conditional_matrix.columns]
    return gene_symbols


def load_gene_metadata(chromosome="13", study_id="prad_tcga_pan_can_atlas_2018"):
    """
    Load gene metadata including cytobands.
    
    Args:
        chromosome: Chromosome number (default: "13")
        study_id: Full study identifier (default: "prad_tcga_pan_can_atlas_2018")
        
    Returns:
        DataFrame with columns: entrezGeneId, hugoGeneSymbol, cytoband
    """
    processed_dir = get_processed_dir(study_id)
    filename = f"chr{chromosome}_genes_metadata.xlsx"
    filepath = os.path.join(processed_dir, filename)
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"Gene metadata not found: {filepath}. "
            "Run batch_process.py to generate processed data for all studies."
        )
    
    df = pd.read_excel(filepath)
    return df


def load_deletion_frequencies(chromosome="13", study_id="prad_tcga_pan_can_atlas_2018"):
    """
    Load individual gene deletion frequencies.
    
    Args:
        chromosome: Chromosome number (default: "13")
        study_id: Full study identifier (default: "prad_tcga_pan_can_atlas_2018")
        
    Returns:
        Series with deletion frequency for each gene
    """
    processed_dir = get_processed_dir(study_id)
    filename = f"chr{chromosome}_deletion_frequencies.xlsx"
    filepath = os.path.join(processed_dir, filename)
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Deletion frequencies not found: {filepath}")
    
    df = pd.read_excel(filepath, index_col=0)
    # Return as Series
    return df.iloc[:, 0] if df.shape[1] == 1 else df.squeeze()


def list_available_studies():
    """
    List all available processed studies.
    
    Returns:
        List of study IDs that have been processed
    """
    processed_dir = get_processed_dir()
    
    if not os.path.exists(processed_dir):
        return []
    
    # Get all subdirectories (each represents a study)
    studies = [d for d in os.listdir(processed_dir) 
               if os.path.isdir(os.path.join(processed_dir, d))]
    
    return sorted(studies)


def list_available_analyses():
    """
    List all available processed analysis files.
    
    Returns:
        Dictionary with analysis types and available files
    """
    processed_dir = get_processed_dir()
    
    if not os.path.exists(processed_dir):
        return {}
    
    files = os.listdir(processed_dir)
    
    analyses = {
        'conditional_matrices': [f for f in files if 'conditional' in f and f.endswith('.xlsx')],
        'frequency_matrices': [f for f in files if 'codeletion_matrix' in f and f.endswith('.xlsx')],
        'pair_frequencies': [f for f in files if 'codeletion_frequencies' in f and f.endswith('.xlsx')],
        'other': [f for f in files if f.endswith(('.xlsx', '.html'))]
    }
    
    return analyses
