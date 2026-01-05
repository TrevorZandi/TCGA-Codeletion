import os
import pandas as pd
import pickle

CACHE_DIR = os.path.join(os.path.dirname(__file__), "cached")

def load_from_cache(filename: str):
    """
    Load data from cache. Returns the data in its original format.
    """
    path = os.path.join(CACHE_DIR, filename)
    if os.path.exists(path):
        with open(path, 'rb') as f:
            return pickle.load(f)
    return None

def save_to_cache(data, filename: str):
    """
    Save data to cache. Stores the data as-is.
    """
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = os.path.join(CACHE_DIR, filename)
    with open(path, 'wb') as f:
        pickle.dump(data, f)
