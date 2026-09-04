"""FastAPI entry point for the Adaptive Cache Management System."""
from time import perf_counter
from fastapi import FastAPI, HTTPException, Query
from backend.cache.cache_manager import AdaptiveCacheManager
from backend.config import settings
from backend.metrics.metrics import Metrics
from backend.workloads.backend_simulator import BackendSimulator

app = FastAPI(title="Adaptive Cache Management System", version="1.0.0")
cache = AdaptiveCacheManager()
metrics = Metrics()
simulator = BackendSimulator()


@app.get("/data/{key}")
def get_data(key: str, workload: str = Query("steady", pattern="^(steady|spike|gradual)$")) -> dict:
    """Fetch a value from cache or simulated backend and populate the cache."""
    cache.set_workload(workload)
    started = perf_counter()
    
    value = cache.get(key)
    hit = value is not None
    cost = 0.0
    
    if hit:
        metrics.record_hit()
    else:
        # BackendSimulator fetch expects an int for its logic (key % 5 == 0)
        try:
            int_key = int(key)
        except ValueError:
            int_key = sum(ord(c) for c in key)
            
        value, latency, cost = simulator.fetch(int_key)
        cache.put(key, value, cost)
        
    latency_ms = (perf_counter() - started) * 1000
    metrics.record_request(latency_ms, cost)
    
    # Member 1 feature: return score and decision
    score = None
    decision = None
    if hasattr(cache.policy, "items"):
        item = cache.policy.items.get(key)
        if item:
            if cache.algorithm == "adaptive":
                score = cache.scorer.score(item)
            decision = cache.decide(key)

    return {
        "status": "HIT" if hit else "MISS",
        "key": key,
        "data": value,
        "cache_hit": hit,
        "latency_ms": round(latency_ms, 3),
        "algorithm": cache.algorithm,
        "score": score,
        "decision": decision
    }


@app.get("/metrics")
def get_metrics() -> dict:
    """Expose in-process cache metrics for a dashboard or quick inspection."""
    return metrics.results()


@app.get("/stats")
def get_stats() -> dict:
    """Backward compatibility for Member 1 stats endpoint."""
    res = metrics.results()
    return {
        "hits": metrics.hits,
        "misses": metrics.total_requests - metrics.hits,
        "hit_rate": res.get("hit_rate", 0),
        "avg_latency": res.get("avg_latency", 0)
    }


@app.get("/cache/{key}/metadata")
def get_cache_metadata(key: str) -> dict:
    """Returns the full metadata object for a specific cache key."""
    if hasattr(cache.policy, "items"):
        item = cache.policy.items.get(key)
        if item:
            return {
                "key": item.key,
                "value": item.value,
                "size": item.size,
                "cost": item.cost,
                "frequency": item.frequency,
                "created_at": item.created_at,
                "last_accessed": item.last_accessed,
                "score": cache.scorer.score(item) if cache.algorithm == "adaptive" else None,
                "decision": cache.decide(key)
            }
    return {"error": "Key not found in cache"}


@app.get("/cache/all")
def get_all_cache_summary() -> dict:
    """Returns a summary of all cache entries, highlighting their scores and decisions."""
    summary = {}
    if hasattr(cache.policy, "items"):
        for k, item in cache.policy.items.items():
            summary[k] = {
                "score": cache.scorer.score(item) if cache.algorithm == "adaptive" else None,
                "decision": cache.decide(k),
                "frequency": item.frequency
            }
    return summary


@app.post("/cache/cleanup")
def cleanup_cache() -> dict:
    """
    Background/periodic cleanup mechanism.
    Evaluates all cache entries, recalculates their score/decision (since time has passed),
    and removes the ones that result in 'evict'.
    """
    keys_to_evict = []
    if cache.algorithm == "adaptive" and hasattr(cache.policy, "items"):
        for key, item in list(cache.policy.items.items()):
            if cache.decide(key) == "evict":
                keys_to_evict.append(key)
                
        for key in keys_to_evict:
            del cache.policy.items[key]
            cache.redis.delete(key)
            
    return {
        "message": "Cleanup complete",
        "evicted_keys": keys_to_evict,
        "total_evicted": len(keys_to_evict)
    }


@app.post("/algorithm/{algorithm}")
def switch_algorithm(algorithm: str) -> dict:
    """Switch policy; cache contents are intentionally reset for fair behavior."""
    global cache
    try:
        cache = AdaptiveCacheManager(algorithm)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"algorithm": cache.algorithm, "message": "Cache policy switched"}
