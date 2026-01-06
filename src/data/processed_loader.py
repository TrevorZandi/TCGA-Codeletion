"""
Data loader for processed co-deletion analysis results.

This module provides functions to load pre-computed co-deletion matrices
and statistics from the data/processed directory or AWS S3 for visualization in Dash.

Supports both local file system and AWS S3 storage based on environment variables:
- USE_S3: Set to 'true' to use S3 storage
- S3_BUCKET: Name of the S3 bucket (default: 'tcga-codeletion-data')
- S3_PREFIX: Prefix path in S3 bucket (default: 'processed/')
"""

import os
import pandas as pd
from io import BytesIO

# Configuration from environment variables
USE_S3 = os.environ.get('USE_S3', 'false').lower() == 'true'
S3_BUCKET = os.environ.get('S3_BUCKET', 'tcga-codeletion-data')
S3_PREFIX = os.environ.get('S3_PREFIX', 'processed/')

# Initialize S3 client only if needed
_s3_client = None

def _get_s3_client():
    """
    Get or create S3 client with connection pooling and optimized retry logic.
    Uses lazy initialization and reuses client across requests.
    """
    global _s3_client
    if _s3_client is None:
        import boto3
        from botocore.config import Config
        
        # Enable connection pooling and adaptive retries for better performance
        config = Config(
            max_pool_connections=10,  # Allow up to 10 concurrent connections
            retries={
                'max_attempts': 3,
                'mode': 'adaptive'  # Automatic exponential backoff
            },
            connect_timeout=5,  # 5s to establish connection
            read_timeout=30     # 30s to read response
        )
        _s3_client = boto3.client('s3', config=config)
    return _s3_client


def load_from_s3(s3_key):
    """
    Load file from S3 bucket.
    
    Args:
        s3_key: S3 object key (path within bucket)
        
    Returns:
        BytesIO object containing file data
    """
    s3 = _get_s3_client()
    try:
        obj = s3.get_object(Bucket=S3_BUCKET, Key=s3_key)
        return BytesIO(obj['Body'].read())
    except Exception as e:
        raise FileNotFoundError(f"Failed to load from S3: s3://{S3_BUCKET}/{s3_key} - {str(e)}")


def get_processed_dir(study_id=None):
    """
    Get the path to the processed data directory.
    
    Args:
        study_id: Optional study ID for study-specific subdirectory
    
    Returns:
        Absolute path to data/processed/ or data/processed/{study_id}/
        Or S3 key prefix if USE_S3 is True
    """
    if USE_S3:
        # Return S3 key prefix
        if study_id is not None:
            return f"{S3_PREFIX}{study_id}/"
        return S3_PREFIX
    else:
        # Return local file path
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
    csv_filename = f"chr{chromosome}_codeletion_conditional_frequencies.csv"
    xlsx_filename = f"chr{chromosome}_codeletion_conditional_frequencies.xlsx"
    
    if USE_S3:
        # Try CSV first, then Excel from S3
        csv_key = processed_dir + csv_filename
        xlsx_key = processed_dir + xlsx_filename
        
        s3 = _get_s3_client()
        try:
            # Check if CSV exists in S3
            s3.head_object(Bucket=S3_BUCKET, Key=csv_key)
            data = load_from_s3(csv_key)
            return pd.read_csv(data, index_col=0)
        except:
            try:
                # Fall back to Excel
                data = load_from_s3(xlsx_key)
                return pd.read_excel(data, index_col=0)
            except:
                raise FileNotFoundError(
                    f"Conditional matrix not found in S3: {csv_key} or {xlsx_key}"
                )
    else:
        # Load from local filesystem
        csv_filepath = os.path.join(processed_dir, csv_filename)
        xlsx_filepath = os.path.join(processed_dir, xlsx_filename)
        
        if os.path.exists(csv_filepath):
            return pd.read_csv(csv_filepath, index_col=0)
        elif os.path.exists(xlsx_filepath):
            return pd.read_excel(xlsx_filepath, index_col=0)
        else:
            raise FileNotFoundError(
                f"Conditional matrix not found: {xlsx_filepath} or {csv_filepath}"
            )


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
    
    if USE_S3:
        s3_key = processed_dir + filename
        data = load_from_s3(s3_key)
        return pd.read_excel(data, index_col=0)
    else:
        filepath = os.path.join(processed_dir, filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Frequency matrix not found: {filepath}")
        return pd.read_excel(filepath, index_col=0)


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
    
    if USE_S3:
        s3_key = processed_dir + filename
        data = load_from_s3(s3_key)
        return pd.read_excel(data)
    else:
        filepath = os.path.join(processed_dir, filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Co-deletion pairs not found: {filepath}")
        return pd.read_excel(filepath)


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
    
    if USE_S3:
        s3_key = processed_dir + filename
        data = load_from_s3(s3_key)
        return pd.read_excel(data)
    else:
        filepath = os.path.join(processed_dir, filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(
                f"Gene metadata not found: {filepath}. "
                "Run batch_process.py to generate processed data for all studies."
            )
        return pd.read_excel(filepath)


def load_deletion_frequencies(chromosome="13", study_id="prad_tcga_pan_can_atlas_2018"):
    """
    Load individual gene deletion frequencies.
    
    If deletion_frequencies.xlsx doesn't exist, this will fetch fresh data from
    cBioPortal and calculate deletion frequencies directly.
    
    Args:
        chromosome: Chromosome number (default: "13")
        study_id: Full study identifier (default: "prad_tcga_pan_can_atlas_2018")
        
    Returns:
        Series with deletion frequency for each gene
    """
    processed_dir = get_processed_dir(study_id)
    filename = f"chr{chromosome}_deletion_frequencies.xlsx"
    
    try:
        if USE_S3:
            s3_key = processed_dir + filename
            data = load_from_s3(s3_key)
            df = pd.read_excel(data, index_col=0)
        else:
            filepath = os.path.join(processed_dir, filename)
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"Deletion frequencies not found: {filepath}")
            df = pd.read_excel(filepath, index_col=0)
        
        # Return as Series
        return df.iloc[:, 0] if df.shape[1] == 1 else df.squeeze()
        
    except (FileNotFoundError, Exception):
        # Fallback: Calculate from cBioPortal API
        # Import here to avoid circular dependencies
        from . import queries
        
        try:
            print(f"Calculating deletion frequencies for chr{chromosome} in {study_id} from cBioPortal...")
            
            # Get CNA profile and sample list
            cna_profile_id = queries.get_cna_profile_id(study_id)
            sample_list_id = queries.get_cna_sample_list_id(study_id)
            
            # Get chromosome genes
            chr_genes = queries.get_chromosome_genes(chromosome)
            
            # Fetch CNA data
            cna_data = queries.fetch_cna_for_genes(cna_profile_id, sample_list_id, chr_genes)
            
            # Build deletion matrix
            deletion_mat = queries.build_deletion_matrix(cna_data, chr_genes, deletion_cutoff=-1)
            
            # Calculate deletion frequencies (mean across samples)
            deletion_freqs = deletion_mat.mean(axis=0).sort_values(ascending=False)
            deletion_freqs.name = 'deletion_frequency'
            
            return deletion_freqs
            
        except Exception as e:
            raise FileNotFoundError(
                f"Could not load or calculate deletion frequencies for chr{chromosome}, {study_id}: {e}"
            )


def list_available_studies():
    """
    List all available processed studies.
    
    Returns:
        List of study IDs that have been processed
    """
    processed_dir = get_processed_dir()
    
    if USE_S3:
        # List study directories from S3
        s3 = _get_s3_client()
        try:
            # List objects with the prefix and delimiter to get "folders"
            result = s3.list_objects_v2(
                Bucket=S3_BUCKET,
                Prefix=processed_dir,
                Delimiter='/'
            )
            
            if 'CommonPrefixes' not in result:
                return []
            
            # Extract study names from prefixes
            studies = []
            for prefix in result['CommonPrefixes']:
                # Remove the base prefix and trailing slash
                study_id = prefix['Prefix'].replace(processed_dir, '').rstrip('/')
                if study_id:
                    studies.append(study_id)
            
            return sorted(studies)
        except Exception as e:
            print(f"Warning: Failed to list studies from S3: {e}")
            return []
    else:
        # List from local filesystem
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
