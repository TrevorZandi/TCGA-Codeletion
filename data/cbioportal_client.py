"""
Low-level cBioPortal API client.

This module provides direct access to cBioPortal API endpoints with caching.
It mirrors Swagger endpoints with minimal processing and no domain-specific logic.
"""

import os
import requests
import pandas as pd
from .cache_utils import load_from_cache, save_to_cache

BASE = "https://www.cbioportal.org/api"
HEADERS = {
    "Accept": "application/json"
    # If you end up needing an auth token: "Authorization": "Bearer <TOKEN>"
}


def get_studies(keyword=None, refresh=False):
    """
    Fetch all studies or search by keyword.
    
    Args:
        keyword: Optional search keyword
        refresh: Force refresh from API
        
    Returns:
        List of study dicts from API
    """
    cache_key = f"studies_{keyword or 'all'}.pkl"
    
    if not refresh:
        cached = load_from_cache(cache_key)
        if cached is not None:
            return cached
    
    params = {"keyword": keyword} if keyword else {}
    r = requests.get(f"{BASE}/studies", params=params, headers=HEADERS)
    r.raise_for_status()
    studies = r.json()
    
    save_to_cache(studies, cache_key)
    return studies


def get_molecular_profiles(study_id, refresh=False):
    """
    Fetch molecular profiles for a study.
    
    Args:
        study_id: Study identifier
        refresh: Force refresh from API
        
    Returns:
        List of molecular profile dicts
    """
    cache_file = f"molecular_profiles_{study_id}.pkl"
    
    if not refresh:
        cached = load_from_cache(cache_file)
        if cached is not None:
            return cached
    
    r = requests.get(f"{BASE}/studies/{study_id}/molecular-profiles", headers=HEADERS)
    r.raise_for_status()
    profiles = r.json()
    
    save_to_cache(profiles, cache_file)
    return profiles


def get_sample_lists(study_id, refresh=False):
    """
    Fetch sample lists for a study.
    
    Args:
        study_id: Study identifier
        refresh: Force refresh from API
        
    Returns:
        List of sample list dicts
    """
    cache_file = f"sample_lists_{study_id}.pkl"
    
    if not refresh:
        cached = load_from_cache(cache_file)
        if cached is not None:
            return cached
    
    r = requests.get(f"{BASE}/studies/{study_id}/sample-lists", headers=HEADERS)
    r.raise_for_status()
    lists_ = r.json()
    
    save_to_cache(lists_, cache_file)
    return lists_


def get_genes_by_genome(genome="hg19", refresh=False):
    """
    Fetch all genes for a reference genome.
    
    Args:
        genome: Reference genome (default: hg19)
        refresh: Force refresh from API
        
    Returns:
        List of gene dicts
    """
    cache_file = f"all_genes_{genome}.pkl"
    
    if not refresh:
        cached = load_from_cache(cache_file)
        if cached is not None:
            return cached
    
    r = requests.get(f"{BASE}/reference-genome-genes/{genome}", headers=HEADERS)
    r.raise_for_status()
    genes = r.json()
    
    save_to_cache(genes, cache_file)
    return genes


def fetch_discrete_copy_number(molecular_profile_id, sample_list_id, entrez_ids, refresh=False):
    """
    Fetch discrete copy number alterations.
    
    Args:
        molecular_profile_id: Molecular profile identifier
        sample_list_id: Sample list identifier
        entrez_ids: List of Entrez gene IDs
        refresh: Force refresh from API
        
    Returns:
        List of discrete copy number data dicts
    """
    cache_file = f"cna_data_{molecular_profile_id}_{sample_list_id}.pkl"
    
    if not refresh:
        cached = load_from_cache(cache_file)
        if cached is not None:
            return cached
    
    url = f"{BASE}/molecular-profiles/{molecular_profile_id}/discrete-copy-number/fetch"
    body = {
        "sampleListId": sample_list_id,
        "entrezGeneIds": list(map(int, entrez_ids))
    }
    r = requests.post(url, json=body, headers=HEADERS)
    r = requests.post(url, json=body, headers=HEADERS)
    r.raise_for_status()
    cna_data = r.json()
    
    save_to_cache(cna_data, cache_file)
    return cna_data