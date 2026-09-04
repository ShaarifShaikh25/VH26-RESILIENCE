"""FastAPI entry point exposing cache data and dashboard observability APIs."""
from fastapi import FastAPI, HTTPException, Query

from backend.dashboard_service import DashboardService
from backend.benchmark.compare import run_comparison
from backend.metrics.logger import recent_decisions

app = FastAPI(title="Adaptive Cache Management System", version="1.0.0")
system = DashboardService()


@app.get("/data/{key}")
def get_data(key: str, workload: str = Query("steady", pattern="^(steady|spike|gradual)$")) -> dict:
    """Fetch a value from cache or the simulated backend."""
    return system.request(key, workload)


@app.get("/metrics")
def get_metrics() -> dict:
    """Return hit rate, average latency, total cost, and request count."""
    return system.overview()


@app.get("/metrics/history")
def get_metric_history() -> list[dict]:
    """Return per-request measurements for live charts."""
    return system.metric_history()


@app.get("/cache/state")
def get_cache_state() -> list[dict]:
    """Return all current cache keys and their metadata."""
    return system.cache_state()


@app.get("/decisions")
def get_decisions(limit: int = Query(50, ge=1, le=200)) -> list[dict]:
    """Return recent HIT, MISS, KEEP, EVICT, and REFRESH decisions."""
    return recent_decisions(limit)


@app.post("/algorithm/{algorithm}")
def switch_algorithm(algorithm: str) -> dict:
    """Switch algorithm and reset the isolated runtime session."""
    try:
        system.select_algorithm(algorithm)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return system.overview()


@app.post("/simulate/{workload}")
def simulate_workload(workload: str, requests: int = Query(50, ge=1, le=500)) -> dict:
    """Generate traffic through the active cache for dashboards and demos."""
    if workload not in {"steady", "spike", "gradual"}:
        raise HTTPException(status_code=400, detail="Unknown workload")
    return system.simulate_workload(workload, requests)


@app.post("/benchmark/{workload}")
def benchmark_workload(
    workload: str,
    requests: int = Query(50, ge=1, le=500),
    capacity: int = Query(5, ge=1, le=500),
) -> list[dict]:
    """Compare all cache policies through the backend benchmark service."""
    if workload not in {"steady", "spike", "gradual"}:
        raise HTTPException(status_code=400, detail="Unknown workload")
    return run_comparison(workload, requests, capacity)
