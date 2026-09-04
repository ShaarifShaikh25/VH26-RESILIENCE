"""GreedyDual-Size cache policy: score = (cost / size) + L."""
from backend.algorithms.base import BaseCache
from backend.cache.cache_object import CacheObject


class GDSCache(BaseCache):
    def __init__(self, capacity: int) -> None:
        super().__init__(capacity)
        self.L = 0.0
        self.scores: dict[str, float] = {}

    def put(self, item: CacheObject) -> str | None:
        if item.key in self.items:
            self.items[item.key] = item
            self.scores[item.key] = item.cost / max(item.size, 1) + self.L
            return None
        victim = self.evict() if len(self.items) >= self.capacity else None
        self.items[item.key] = item
        self.scores[item.key] = item.cost / max(item.size, 1) + self.L
        return victim

    def evict(self) -> str | None:
        if not self.items:
            return None
        victim = min(self.scores, key=self.scores.get)
        self.L = self.scores.pop(victim)
        del self.items[victim]
        return victim
