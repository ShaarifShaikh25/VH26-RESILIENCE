"""Adaptive cache policy using the configured multi-factor scorer."""
from __future__ import annotations

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
        self.last_inserted_key: str | None = None
        self.exploration_rate = 0.01  # Safe exploration rate
        self.exploration_count = 0
        self.exploitation_count = 0

    def get(self, key):
        item = self.items.get(key)
        if item:
            item.touch(getattr(self.scorer, "request_number", 0))
        return item

    def set_scorer(self, scorer) -> None:
        self.scorer = scorer

    def _score(self, item: CacheObject) -> float:
        if self.scorer is None:
            raise RuntimeError("AdaptiveCache requires a scoring engine")
        return self.scorer.score(item)

    @property
    def warmup_phase(self) -> bool:
        return self.scorer is None or self.scorer.training_samples < 20

    def _retention_score(self, item: CacheObject) -> float:
        """Calibrated retention score primarily driven by predicted reuse value."""
        base_score = self._score(item)
        # Bounded cost bonus (up to +5%)
        cost_factor = 1.0 + 0.05 * min(max(float(item.cost), 0.0) / 10.0, 1.0)
        # Bounded size factor (smaller size gets gentle bonus, up to +5%)
        size_factor = 0.95 + 0.05 * (512.0 / (512.0 + max(float(item.size), 1.0)))
        return base_score * cost_factor * size_factor

    def put(self, key, value, cost=None) -> str | None:
        current_seq = getattr(self.scorer, "request_number", 0)
        if key in self.items:
            item = self.items[key]
            item.value = value
            item.cost = 0.0 if cost is None else float(cost)
            item.touch(current_seq)
            item.size = self._value_size(value)
            return None

        self.last_inserted_key = key
        item = self._cache_object(key, value, cost)
        item.last_sequence = current_seq
        self.items[key] = item
        return self.evict() if len(self.items) > self.capacity else None

    def evict(self) -> str | None:
        if not self.items:
            return None
        candidates = list(self.items.values())
        workload = getattr(self.scorer, "workload", "steady") if self.scorer else "steady"

        # In spike workloads, protect the new burst arrival from immediate eviction so it can hit
        if workload == "spike" and self.last_inserted_key and len(candidates) > 1:
            eligible = [it for it in candidates if it.key != self.last_inserted_key]
            if not eligible:
                eligible = candidates
        else:
            eligible = candidates

        if self.warmup_phase:
            self.last_eviction_mode = "WARMUP"
            # In warmup, use retention score from the calibrated heuristic
            victim = min(eligible, key=self._retention_score)
        elif len(eligible) > 1 and random.random() < self.exploration_rate:
            self.last_eviction_mode = "EXPLORATION"
            self.exploration_count += 1
            ranked = sorted(eligible, key=self._retention_score)
            bottom_count = max(1, int(len(ranked) * 0.15))
            victim = random.choice(ranked[:bottom_count])
        else:
            self.last_eviction_mode = "EXPLOITATION"
            self.exploitation_count += 1
            victim = min(eligible, key=self._retention_score)

        self.last_evicted_score = self._score(victim)
        self.last_evicted_retention_score = self._retention_score(victim)
        self.last_eviction_metadata = {
            "frequency": victim.frequency,
            "last_access": victim.last_accessed,
            "cost": victim.cost,
            "size": victim.size,
        }
        del self.items[victim.key]
        return victim.key

