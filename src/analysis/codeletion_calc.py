"""
Co-deletion frequency calculations and analysis.

This module provides functions to compute co-deletion frequencies
and conditional probabilities from binary deletion matrices.
"""

import numpy as np
import pandas as pd


def compute_codeletion_frequency(mat):
    """
    Compute co-deletion frequencies for all gene pairs.
    
    Args:
        mat: DataFrame samples x genes (0/1 deletion)
        
    Returns:
        Tuple of (freq_matrix, long_table, counts_matrix):
        - freq_matrix: DataFrame with co-deletion frequencies (genes x genes)
        - long_table: DataFrame with upper-triangle pairs in long format
        - counts_matrix: DataFrame with raw co-deletion counts (genes x genes)
    """
    # Number of samples
    n = mat.shape[0]
    
    # Convert to numpy for speed
    X = mat.values  # shape (n_samples, n_genes)
    
    # Co-deletion counts via matrix multiplication
    # (X^T * X)[i,j] = # samples where both i and j are 1
    counts = X.T @ X   # shape (n_genes, n_genes)
    
    freq = counts / float(n)
    
    genes = mat.columns
    freq_df = pd.DataFrame(freq, index=genes, columns=genes)
    counts_df = pd.DataFrame(counts, index=genes, columns=genes)
    
    # Long-form table of upper-triangle pairs
    long = (
        freq_df.where(np.triu(np.ones(freq_df.shape, dtype=bool), k=1))
               .stack()
               .rename("co_deletion_frequency")
               .reset_index()
               .rename(columns={"level_0": "gene_i", "level_1": "gene_j"})
    )
    
    return freq_df, long, counts_df


def compute_conditional_codeletion(counts_df):
    """
    Compute conditional co-deletion probabilities P(i | j).
    
    Given a gene j is deleted, what is the probability that gene i is also deleted?
    
    Args:
        counts_df: DataFrame with co-deletion counts (genes x genes)
        
    Returns:
        DataFrame with conditional probabilities P(i | j) = count(i,j) / count(j,j)
    """
    conditional = counts_df / counts_df.values.diagonal()
    return conditional


def get_top_codeleted_pairs(long_table, n=20):
    """
    Get the top N co-deleted gene pairs.
    
    Args:
        long_table: Long-format DataFrame with co-deletion frequencies
        n: Number of top pairs to return
        
    Returns:
        DataFrame with top N pairs sorted by co_deletion_frequency
    """
    return long_table.sort_values("co_deletion_frequency", ascending=False).head(n)


def compute_deletion_frequencies(mat):
    """
    Compute individual gene deletion frequencies.
    
    Args:
        mat: DataFrame samples x genes (0/1 deletion)
        
    Returns:
        Series with deletion frequency for each gene
    """
    return mat.mean(axis=0).sort_values(ascending=False)
