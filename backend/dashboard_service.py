"""Shared application service for the FastAPI and Streamlit monitoring views."""
from time import perf_counter

from backend.cache.cache_manager import AdaptiveCacheManager
from backend.metrics.logger import recent_decisions
from backend.metrics.metrics import Metrics
from backend.workloads.backend_simulator import fetch_data
from backend.workloads.workload_generator import generate_workload


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
        latency_ms = (perf_counter() - started) * 1000
        self.metrics.record(hit, latency_ms, cost)
        return {"key": key, "status": "HIT" if hit else "MISS", "data": value,
                "latency_ms": latency_ms, "cost": cost, "algorithm": self.cache.algorithm}

    def simulate_workload(self, workload: str, requests: int = 50) -> dict:
        """Replay one generated workload through the selected cache policy."""
        for key in generate_workload(workload, requests):
            self.request(key, workload)
        return self.overview()

    def overview(self) -> dict:
        """Return the summary metrics displayed in the system overview."""
        return {"algorithm": self.cache.algorithm.upper(), **self.metrics.snapshot()}

    def cache_state(self) -> list[dict]:
        return self.cache.cache_state()

    def metric_history(self) -> list[dict]:
        return self.metrics.time_series()

    def decision_logs(self, limit: int = 50) -> list[dict]:
        return recent_decisions(limit)
