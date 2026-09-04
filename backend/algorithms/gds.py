"""GreedyDual-Size cache policy: score = (cost / size) + L."""
import json
from backend.algorithms.base import BaseCache
from backend.cache.cache_object import CacheObject


class GDSCache(BaseCache):
    algorithm_name = "GDS"

    def __init__(self, capacity: int) -> None:
        super().__init__(capacity)
        self.L = 0.0
        self.scores: dict[str, float] = {}
        self.last_evicted_score: float | None = None

    def _gds_score(self, item: CacheObject) -> float:
        return item.cost / max(item.size, 1) + self.L

    def put(self, key, value, cost=None) -> str | None:
        if key in self.items:
            item = self.items[key]
            item.value = value
            item.cost = 0.0 if cost is None else float(cost)
            item.size = self._value_size(value)
            item.touch()                          # preserve frequency, update last_accessed
            self.scores[key] = self._gds_score(item)
            return None
        item = self._cache_object(key, value, cost)
        self.items[key] = item
        self.scores[key] = self._gds_score(item)
        return self.evict() if len(self.items) > self.capacity else None

    def evict(self) -> str | None:
        if not self.items:
            return None
        victim = min(self.scores, key=self.scores.get)
        self.last_evicted_score = self.scores.pop(victim)
        self.L = self.last_evicted_score          # L advances to evicted item's score
        del self.items[victim]
        return victim
