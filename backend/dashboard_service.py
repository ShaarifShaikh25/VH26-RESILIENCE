"""Shared application service for the FastAPI and Streamlit monitoring views."""
from time import perf_counter
import logging
from pathlib import Path

from backend.cache.cache_manager import AdaptiveCacheManager
from backend.metrics.logger import recent_decisions
from backend.metrics.metrics import Metrics
from backend.workloads.backend_simulator import fetch_data
from backend.workloads.kaggle_loader import download_dataset, generate_requests, load_events
from backend.workloads.workload_generator import generate_workload

logger = logging.getLogger("adaptive_cache.service")


class DashboardService:
    """Run real cache requests and expose dashboard-friendly observations."""

    def __init__(self, algorithm: str = "adaptive", capacity: int = 100) -> None:
        self.capacity = capacity
        self.select_algorithm(algorithm)

    def select_algorithm(self, algorithm: str) -> None:
        """Switch policy and reset its isolated cache and metrics session."""
        self.cache = AdaptiveCacheManager(algorithm, self.capacity)
        self.metrics = Metrics()

    def request(self, key: str, workload: str = "steady") -> dict:
        """Execute one cache request using the real manager and backend simulator."""
        self.cache.set_workload(workload)
        started = perf_counter()
        value = self.cache.get(key)
        hit, cost = value is not None, 0.0
        if not hit:
            value, cost = fetch_data(key)
            self.cache.put(key, value, cost)
        event_type = value.get("event", "view") if isinstance(value, dict) else "view"
        latency_ms = (perf_counter() - started) * 1000
        self.metrics.record(
            hit, latency_ms, cost, self.cache.last_prediction_score,
            self.cache.learning_metrics().get("training_samples", 0),
            key=key, event_type=event_type, requested_cost=cost,
        )
        return {"key": key, "status": "HIT" if hit else "MISS", "data": value,
                "latency_ms": latency_ms, "cost": cost, "algorithm": self.cache.algorithm}

    def simulate_workload(self, workload: str, requests: int = 50) -> dict:
        """Replay one generated workload through the selected cache policy."""
        for key in generate_workload(workload, requests):
            self.request(key, workload)
        return self.overview()

    def request_event(self, key: str, value: dict, cost: float) -> dict:
        """Process one already-materialized request from an external stream."""
        started = perf_counter()
        cached = self.cache.get(key)
        hit = cached is not None
        if not hit:
            self.cache.put(key, value, cost)
        latency_ms = (perf_counter() - started) * 1000
        self.metrics.record(
            hit, latency_ms, 0.0 if hit else cost, self.cache.last_prediction_score,
            self.cache.learning_metrics().get("training_samples", 0),
            key=key, event_type=value.get("event", "view"), requested_cost=cost,
        )
        return {"key": key, "status": "HIT" if hit else "MISS",
                "latency_ms": latency_ms, "cost": 0.0 if hit else cost}

    def simulate_kaggle(self, requests: int = 500, csv_path: str | None = None) -> dict:
        """Replay chronological Kaggle events through the active cache."""
        resolved_csv = Path(csv_path) if csv_path else download_dataset()
        events = load_events(csv_path=resolved_csv, max_rows=requests)
        replayed = 0
        samples = []
        for key, value, cost, _ in generate_requests(events):
            self.request_event(key, value, cost)
            replayed += 1
            if len(samples) < 5:
                sample = {
                    "product_id": value.get("product_id"),
                    "event_type": value.get("event"),
                    "timestamp": value.get("timestamp"),
                    "cache_key": key,
                }
                for field in ("user_id", "category_id"):
                    if field in value:
                        sample[field] = value[field]
                samples.append(sample)
        logger.info("Kaggle events replayed: %d; cache manager processed: %d", replayed, replayed)
        return {
            **self.overview(),
            "source": "Kaggle",
            "csv_path": str(resolved_csv.resolve()),
            "rows_loaded": len(events),
            "events_replayed": replayed,
            "sample_events": samples,
            "pipeline": "DashboardService.request_event -> AdaptiveCacheManager.get/put",
        }

    def overview(self) -> dict:
        """Return the summary metrics displayed in the system overview."""
        return {"algorithm": self.cache.algorithm.upper(), **self.metrics.snapshot(),
            **self.cache.learning_metrics()}

    def cache_state(self) -> list[dict]:
        return self.cache.cache_state()

    def metric_history(self) -> list[dict]:
        return self.metrics.time_series()

    def cost_breakdown(self) -> dict:
        return self.metrics.cost_breakdown()

    def decision_logs(self, limit: int = 50) -> list[dict]:
        return recent_decisions(limit)
