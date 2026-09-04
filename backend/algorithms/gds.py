"""GreedyDual-Size cache policy: score = (cost / size) + L."""
import json
from backend.algorithms.base import BaseCache
from backend.cache.cache_object import CacheObject


class GDSCache(BaseCache):
    def __init__(self, capacity: int) -> None:
        super().__init__(capacity)
        self.L = 0.0
        self.scores: dict[str, float] = {}

    def _gds_score(self, item: CacheObject) -> float:
        return item.cost / max(item.size, 1) + self.L

    def put(self, key, value, cost=None) -> str | None:
        if key in self.items:
            item = self.items[key]
            item.value = value
            item.cost = 0.0 if cost is None else float(cost)
            item.size = max(len(json.dumps(value, default=str)), 1)
            item.touch()                          # preserve frequency, update last_accessed
            self.scores[key] = self._gds_score(item)
            return None
        victim = self.evict() if len(self.items) >= self.capacity else None
        item = self._cache_object(key, value, cost)
        self.items[key] = item
        self.scores[key] = self._gds_score(item)
        return victim

    def evict(self) -> str | None:
        if not self.items:
            return None
        victim = min(self.scores, key=self.scores.get)
        self.L = self.scores.pop(victim)          # L advances to evicted item's score
        del self.items[victim]
        return victim
