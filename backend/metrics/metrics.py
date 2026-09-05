"""Lightweight in-process metrics suitable for demos and benchmarks."""
from dataclasses import dataclass, field
from time import time


EVENT_COSTS = {"view": 1.0, "cart": 5.0, "purchase": 10.0}


@dataclass
class Metrics:
    hits: int = 0
    misses: int = 0
    total_latency_ms: float = 0.0
    backend_cost: float = 0.0
    requests: int = 0
    history: list[dict] = field(default_factory=list)
    cost_events: list[dict] = field(default_factory=list)
    cost_saved: float = 0.0

    def record(self, hit: bool, latency_ms: float, cost: float = 0.0,
               prediction_score: float | None = None,
               training_samples: int = 0, key: str | None = None,
               event_type: str = "view", requested_cost: float | None = None) -> None:
        self.requests += 1
        self.hits += int(hit)
        self.misses += int(not hit)
        self.total_latency_ms += latency_ms
        self.backend_cost += cost
        normalized_event = event_type.lower()
        nominal_cost = EVENT_COSTS.get(normalized_event, requested_cost if requested_cost is not None else cost)
        if hit:
            self.cost_saved += nominal_cost
        self.cost_events.append({
            "timestamp": time(), "key": key, "event_type": normalized_event,
            "cache_hit": hit, "retrieval_cost": cost,
            "cumulative_cost": self.backend_cost,
            "cost_avoided": nominal_cost if hit else 0.0,
        })
        self.cost_events = self.cost_events[-500:]
        self.history.append({
            "timestamp": time(),
            "request": self.requests,
            "hit_rate": self.hits / self.requests,
            "latency_ms": latency_ms,
            "cost": cost,
            "prediction_score": prediction_score,
            "training_samples": training_samples,
            "event_type": normalized_event,
            "cache_hit": hit,
            "retrieval_cost": cost,
            "cumulative_cost": self.backend_cost,
        })
        # Keep enough points for a useful dashboard without unbounded growth.
        self.history = self.history[-500:]

    def snapshot(self) -> dict[str, float]:
        return {"hits": self.hits, "misses": self.misses,
            "hit_rate": self.hits / self.requests if self.requests else 0.0,
                "average_latency_ms": self.total_latency_ms / self.requests if self.requests else 0.0,
                "cost": self.backend_cost, "requests": self.requests,
                "avg_latency_ms": self.total_latency_ms / self.requests if self.requests else 0.0,
                "cost_saved": self.cost_saved,
                "backend_calls_avoided": self.hits}

    def time_series(self) -> list[dict]:
        """Return request-level points for live dashboard charts."""
        return self.history.copy()

    def cost_breakdown(self) -> dict:
        by_event = {}
        for event_type, unit_cost in EVENT_COSTS.items():
            events = [event for event in self.cost_events if event["event_type"] == event_type]
            misses = [event for event in events if not event["cache_hit"]]
            by_event[event_type] = {
                "count": len(events), "unit_cost": unit_cost,
                "misses": len(misses), "subtotal": sum(event["retrieval_cost"] for event in misses),
            }
        return {
            "total_backend_cost": self.backend_cost,
            "cost_saved": self.cost_saved,
            "total_requests": self.requests,
            "cache_hits": self.hits,
            "cache_misses": self.misses,
            "backend_calls_avoided": self.hits,
            "by_event_type": by_event,
            "recent_requests": self.cost_events[-50:],
        }
