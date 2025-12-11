"""
Higher-level project-specific queries for cBioPortal data.

This module provides domain-specific queries that combine and filter
raw API data to produce meaningful datasets for analysis.
"""

import pandas as pd
from . import cbioportal_client as client


def get_study_id(study_id=None):
    """
    Get a study ID (defaults to PRAD PanCancer Atlas).
    
    Args:
        study_id: Optional study ID to return (default: PRAD)
        
    Returns:
        Study ID string
    """
    if study_id is None:
        # Default to PRAD for backward compatibility
        return "prad_tcga_pan_can_atlas_2018"
    return study_id


def get_cna_profile_id(study_id, refresh=False):
    """
    Get the CNA molecular profile ID for a study, preferring GISTIC/discrete profiles.
    
    Args:
        study_id: Study identifier
        refresh: Force refresh from API
        
    Returns:
        Molecular profile ID string
    """
    profiles = client.get_molecular_profiles(study_id, refresh=refresh)
    
    cna_profiles = [
        p for p in profiles
        if p.get("molecularAlterationType") == "COPY_NUMBER_ALTERATION"
    ]
    
    if not cna_profiles:
        raise ValueError("No CNA profiles found.")
    
    # Heuristic: prefer GISTIC / discrete profile
    for p in cna_profiles:
        name = (p.get("name") or "").lower() + " " + (p.get("description") or "").lower()
        if "gistic" in name or "discrete" in name:
            return p["molecularProfileId"]
    
    # Fallback to first CNA profile
    return cna_profiles[0]["molecularProfileId"]


def get_cna_sample_list_id(study_id, refresh=False):
    """
    Get the CNA sample list ID for a study.
    
    Args:
        study_id: Study identifier
        refresh: Force refresh from API
        
    Returns:
        Sample list ID string
    """
    lists_ = client.get_sample_lists(study_id, refresh=refresh)
    
    # Prefer all_cases_with_cna if present
    for sl in lists_:
        if sl.get("category") == "all_cases_with_cna":
            return sl["sampleListId"]
    
    # Fallback: any sample list mentioning cna
    for sl in lists_:
        if "cna" in (sl.get("sampleListId", "") + sl.get("name", "")).lower():
            return sl["sampleListId"]
    
    # Absolute fallback: all cases
    for sl in lists_:
        if sl.get("category") == "all_cases_in_study":
            return sl["sampleListId"]
    
    raise ValueError("No suitable sample list for CNA found.")


def get_chromosome_genes(chromosome, genome="hg19", refresh=False):
    """
    Get all genes on a specific chromosome with genomic positions.
    
    Args:
        chromosome: Chromosome number or name (e.g., "13", "X")
        genome: Reference genome (default: hg19)
        refresh: Force refresh from API
        
    Returns:
        DataFrame with entrezGeneId, hugoGeneSymbol, cytoband, start, end columns
    """
    genes = client.get_genes_by_genome(genome, refresh=refresh)
    
    # Filter by chromosome
    chr_genes = [g for g in genes if g.get("chromosome") == str(chromosome)]
    
    # Build DataFrame with genomic positions
    df = pd.DataFrame(chr_genes)[["entrezGeneId", "hugoGeneSymbol", "cytoband", "start", "end"]]
    df = df.drop_duplicates("entrezGeneId")
    
    # Sort by chromosomal position using start position
    df = df.sort_values("start").reset_index(drop=True)
    
    return df


def get_chr13_genes(refresh=False):
    """
    Get all genes on chromosome 13 (project-specific convenience function).
    
    Args:
        refresh: Force refresh from API
        
    Returns:
        DataFrame with entrezGeneId and hugoGeneSymbol columns
    """
    return get_chromosome_genes("13", refresh=refresh)


def fetch_cna_for_genes(molecular_profile_id, sample_list_id, gene_df, refresh=False):
    """
    Fetch CNA data for a set of genes.
    
    Args:
        molecular_profile_id: Molecular profile identifier
        sample_list_id: Sample list identifier
        gene_df: DataFrame with 'entrezGeneId' column
        refresh: Force refresh from API
        
    Returns:
        List of CNA data dicts
    """
    entrez_ids = gene_df["entrezGeneId"].tolist()
    return client.fetch_discrete_copy_number(
        molecular_profile_id, 
        sample_list_id, 
        entrez_ids, 
        refresh=refresh
    )


def build_deletion_matrix(cna_data, gene_map, deletion_cutoff=-1):
    """
    Build a binary deletion matrix from CNA data.
    
    Args:
        cna_data: List of DiscreteCopyNumberData dicts
        gene_map: DataFrame with columns ['entrezGeneId', 'hugoGeneSymbol']
        deletion_cutoff: Treat alteration <= this as deleted (default: -1)
        
    Returns:
        DataFrame with samples as rows, genes as columns (with HUGO symbols),
        and 0/1 values indicating deletion status
    """
    df = pd.DataFrame(cna_data)
    
    # Keep only relevant columns
    df = df[["sampleId", "entrezGeneId", "alteration"]]
    
    # Binary deletion flag
    df["deleted"] = df["alteration"] <= deletion_cutoff
    
    # Pivot to samples x genes (Entrez)
    mat = df.pivot_table(
        index="sampleId",
        columns="entrezGeneId",
        values="deleted",
        aggfunc="max",  # if multiple rows, any deletion counts
        fill_value=False
    )
    
    # Ensure all genes appear in chromosomal order (by position, not sorted ID)
    # gene_map is already sorted by chromosomal position from get_chromosome_genes
    mat = mat.reindex(columns=gene_map["entrezGeneId"].tolist(), fill_value=False)
    
    # Rename columns to HUGO symbols
    entrez_to_hugo = dict(zip(gene_map["entrezGeneId"], gene_map["hugoGeneSymbol"]))
    mat.columns = [f"{entrez_to_hugo[gid]} ({gid})" for gid in mat.columns]
    
    # Convert to int (0/1)
    mat = mat.astype(int)
    
    return mat


def select_genes_by_symbol(matrix, symbols):
    """
    Select columns from deletion matrix by gene symbols.
    
    Args:
        matrix: DataFrame with columns formatted as "SYMBOL (ENTREZ)"
        symbols: List or set of gene symbols to select
        
    Returns:
        DataFrame with only the selected gene columns
    """
    symbols = set(symbols)
    return matrix[[c for c in matrix.columns if c.split(" ")[0] in symbols]]
