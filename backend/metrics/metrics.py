"""Lightweight in-process metrics suitable for demos and benchmarks."""
from dataclasses import dataclass, field


@dataclass
class Metrics:
    hits: int = 0
    misses: int = 0
    total_latency_ms: float = 0.0
    backend_cost: float = 0.0
    requests: int = 0

    def record(self, hit: bool, latency_ms: float, cost: float = 0.0) -> None:
        self.requests += 1
        self.hits += int(hit)
        self.misses += int(not hit)
        self.total_latency_ms += latency_ms
        self.backend_cost += cost

    def snapshot(self) -> dict[str, float]:
        return {"hit_rate": self.hits / self.requests if self.requests else 0.0,
                "average_latency_ms": self.total_latency_ms / self.requests if self.requests else 0.0,
                "cost": self.backend_cost, "requests": self.requests}
