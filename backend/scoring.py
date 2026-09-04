import time

def calculate_score(cache_object: dict) -> float:
    """
    Calculate an adaptive score (0-100) for a cache object.
    
    Formula Breakdown:
    - Base Score: Starts at 40.0 so new items aren't immediately evicted.
    - Frequency Bonus: Up to 30.0 points (+5 per access after the first).
    - Recency Penalty: Up to -30.0 points (loses 1 point per second of age).
    - Cost Bonus: Up to 20.0 points (higher cost = higher score to keep it).
    - Size Penalty: Up to -20.0 points (larger size = penalized).
    """
    frequency = cache_object.get("frequency", 1)
    last_access = cache_object.get("last_access", time.time())
    size = cache_object.get("size", 1.0)
    retrieval_cost = cache_object.get("retrieval_cost", 10.0)
    
    # 1. Base Score
    base_score = 50.0
    
    # 2. Frequency Bonus (Max 30)
    freq_bonus = min(30.0, (frequency - 1) * 5.0)
    
    # 3. Recency Penalty (Max 30, loses 1 point every 10 seconds)
    time_elapsed = max(0.0, time.time() - last_access)
    recency_penalty = min(30.0, time_elapsed / 10.0)
    
    # 4. Retrieval Cost Bonus (Max 20, assuming max expected cost ~100)
    cost_bonus = min(20.0, (retrieval_cost / 100.0) * 20.0)
    
    # 5. Size Penalty (Max 20, assuming max expected size ~500)
    size_penalty = min(20.0, (size / 500.0) * 20.0)
    
    # Final Score
    score = base_score + freq_bonus - recency_penalty + cost_bonus - size_penalty
    
    # Clamp score between 0 and 100
    return max(0.0, min(100.0, score))
