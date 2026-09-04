import time

# In-memory dictionary to store cache objects
_cache_store = {}

def get_from_cache(key: str):
    """
    Retrieve cache object from the store if it exists.
    """
    return _cache_store.get(key)

def save_to_cache(key: str, cache_object: dict):
    """
    Save or update cache object in the store.
    """
    _cache_store[key] = cache_object

def delete_from_cache(key: str):
    """
    Remove entry from cache.
    """
    if key in _cache_store:
        del _cache_store[key]

def get_all_cache():
    """
    Return all cache entries.
    """
    return _cache_store
