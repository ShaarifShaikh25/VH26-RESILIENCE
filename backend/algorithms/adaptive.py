"""Adaptive cache policy using the configured multi-factor scorer."""
import json
import random

from backend.algorithms.base import BaseCache
from backend.cache.cache_object import CacheObject


class AdaptiveCache(BaseCache):
    """Keep the entries with the highest dynamically computed score."""

    algorithm_name = "ADAPTIVE"

    def __init__(self, capacity: int, scorer=None) -> None:
        super().__init__(capacity)
        self.scorer = scorer
        self.last_evicted_score: float | None = None
        self.last_evicted_retention_score: float | None = None
        self.last_eviction_mode: str | None = None
        self.last_eviction_metadata: dict = {}
        self.exploration_rate = 0.20
        self.exploration_count = 0
        self.exploitation_count = 0

    def get(self, key):
        return super().get(key)

    def set_scorer(self, scorer) -> None:
        self.scorer = scorer

    def _score(self, item: CacheObject) -> float:
        if self.scorer is None:
            raise RuntimeError("AdaptiveCache requires a scoring engine")
        return self.scorer.score(item)

    @property
    def warmup_phase(self) -> bool:
        return self.scorer is None or self.scorer.training_samples < 100

    def _retention_score(self, item: CacheObject) -> float:
        return self._score(item) * max(item.cost, 0.01) / max(item.size, 1)

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
        candidates = list(self.items.values())
        if self.warmup_phase:
            self.last_eviction_mode = "WARMUP"
            victim = min(candidates, key=lambda item: item.last_accessed)
        elif len(candidates) > 1 and random.random() < self.exploration_rate:
            self.last_eviction_mode = "EXPLORATION"
            self.exploration_count += 1
            ranked = sorted(candidates, key=self._retention_score)
            bottom_count = max(1, int(len(ranked) * 0.30))
            victim = random.choice(ranked[:bottom_count])
        else:
            self.last_eviction_mode = "EXPLOITATION"
            self.exploitation_count += 1
            victim = min(candidates, key=self._retention_score)
        self.last_evicted_score = self._score(victim)
        self.last_evicted_retention_score = (
            self.last_evicted_score * max(victim.cost, 0.01) / max(victim.size, 1)
        )
        self.last_eviction_metadata = {
            "frequency": victim.frequency,
            "last_access": victim.last_accessed,
            "cost": victim.cost,
            "size": victim.size,
        }
        del self.items[victim.key]
        return victim.key
