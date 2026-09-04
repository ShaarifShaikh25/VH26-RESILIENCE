"""FastAPI entry point for the Adaptive Cache Management System."""
from time import perf_counter
from fastapi import FastAPI, HTTPException, Query
from backend.cache.cache_manager import AdaptiveCacheManager
from backend.config import settings
from backend.metrics.metrics import Metrics
from backend.workloads.backend_simulator import fetch_data

app = FastAPI(title="Adaptive Cache Management System", version="1.0.0")
cache = AdaptiveCacheManager()
metrics = Metrics()


@app.get("/data/{key}")
def get_data(key: str, workload: str = Query("steady", pattern="^(steady|spike|gradual)$")) -> dict:
    """Fetch a value from cache or simulated backend and populate the cache."""
    cache.set_workload(workload)
    started = perf_counter()
    value = cache.get(key)
    hit, cost = value is not None, 0.0
    if not hit:
        value, cost = fetch_data(key)
        cache.put(key, value, cost)
    latency_ms = (perf_counter() - started) * 1000
    metrics.record(hit, latency_ms, cost)
    return {"data": value, "cache_hit": hit, "latency_ms": round(latency_ms, 3),
            "algorithm": cache.algorithm}


@app.get("/metrics")
def get_metrics() -> dict:
    """Expose in-process cache metrics for a dashboard or quick inspection."""
    return metrics.snapshot()


@app.post("/algorithm/{algorithm}")
def switch_algorithm(algorithm: str) -> dict:
    """Switch policy; cache contents are intentionally reset for fair behavior."""
    global cache
    try:
        cache = AdaptiveCacheManager(algorithm)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"algorithm": cache.algorithm, "message": "Cache policy switched"}
