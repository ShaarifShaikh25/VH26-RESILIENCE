"""Adaptive cache policy using the configured multi-factor scorer."""
import json

from backend.algorithms.base import BaseCache
from backend.cache.cache_object import CacheObject


class AdaptiveCache(BaseCache):
    """Keep the entries with the highest dynamically computed score."""

    algorithm_name = "ADAPTIVE"

    def __init__(self, capacity: int, scorer=None) -> None:
        super().__init__(capacity)
        self.scorer = scorer
        self.last_evicted_score: float | None = None

    def get(self, key):
        return super().get(key)

    def set_scorer(self, scorer) -> None:
        self.scorer = scorer

    def _score(self, item: CacheObject) -> float:
        if self.scorer is None:
            raise RuntimeError("AdaptiveCache requires a scoring engine")
        return self.scorer.score(item)

    def put(self, key, value, cost=None) -> str | None:
        if key in self.items:
            item = self.items[key]
            item.value = value
            item.cost = 0.0 if cost is None else float(cost)
            item.touch()
            item.size = self._value_size(value)
            return

        self.items[key] = self._cache_object(key, value, cost)
        return self.evict() if len(self.items) > self.capacity else None

    def evict(self) -> str | None:
        if not self.items:
            return None
        victim = min(self.items.values(), key=self._score)
        self.last_evicted_score = self._score(victim)
        del self.items[victim.key]
        return victim.key
