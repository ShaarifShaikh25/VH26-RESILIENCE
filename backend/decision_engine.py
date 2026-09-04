# Decision Thresholds
THRESHOLD_HIGH = 70.0
THRESHOLD_LOW = 30.0

def make_decision(cache_object: dict) -> str:
    """
    Decides the fate of a cache object based on its score:
    - KEEP: Score is high, it's very valuable to keep.
    - EVICT: Score is low, it's not worth keeping (e.g., rarely used, large size).
    - REFRESH: Score is intermediate, extend its TTL or keep it tentatively.
    """
    score = cache_object.get("score", 0.0)
    
    if score > THRESHOLD_HIGH:
        return "KEEP"
    elif score < THRESHOLD_LOW:
        return "EVICT"
    else:
        return "REFRESH"
