"""FastAPI entry point exposing cache data and dashboard observability APIs."""
import logging

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse

from backend.dashboard_service import DashboardService
from backend.benchmark.compare import run_comparison
from backend.metrics.logger import recent_decisions

logger = logging.getLogger("adaptive_cache.api")

app = FastAPI(title="Adaptive Cache Management System", version="1.0.0")
system = DashboardService()
logger.info("Registered FastAPI route: GET /simulate/kaggle")


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


@app.get("/metrics/cost")
def get_cost_breakdown() -> dict:
    """Return request-level simulated backend cost accounting."""
    return system.cost_breakdown()


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


@app.get("/simulate/kaggle")
def simulate_kaggle(
    requests: int = Query(50, ge=1, le=10000),
    csv_path: str | None = Query(None),
) -> dict:
    """Replay chronological Kaggle e-commerce events through the active cache."""
    try:
        return system.simulate_kaggle(requests, csv_path)
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        logger.warning("Kaggle simulation unavailable: %s", exc)
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "message": "Kaggle dataset is not configured",
                "setup_required": [
                    "Place kaggle.json in ~/.kaggle or set KAGGLE_CONFIG_DIR",
                    "Install the Kaggle client with: pip install kaggle",
                    "Or pass csv_path to an existing Kaggle CSV",
                ],
                "detail": str(exc),
            },
        )


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
