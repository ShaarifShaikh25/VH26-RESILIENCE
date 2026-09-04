"""Scoring model used by the adaptive eviction policy."""
from time import time
from backend.cache.cache_object import CacheObject


class ScoringEngine:
    def __init__(self, weights: dict[str, float]) -> None:
        self.weights = weights.copy()

    def adjust_for_workload(self, workload: str) -> None:
        """Favor frequency in steady traffic and recency during spikes."""
        presets = {
            "steady": {"frequency": .45, "recency": .25, "cost": .20, "size": .10},
            "spike": {"frequency": .20, "recency": .50, "cost": .20, "size": .10},
            "gradual": {"frequency": .30, "recency": .35, "cost": .25, "size": .10},
        }
        self.weights = presets.get(workload, self.weights)

    def score(self, item: CacheObject) -> float:
        age = max(time() - item.last_accessed, 0.001)
        # Higher score means more valuable to retain.
        return (self.weights["frequency"] * min(item.frequency / 10, 1)
                + self.weights["recency"] * (1 / (1 + age))
                + self.weights["cost"] * min(item.cost / 100, 1)
                + self.weights["size"] * (1 / max(item.size, 1)))
