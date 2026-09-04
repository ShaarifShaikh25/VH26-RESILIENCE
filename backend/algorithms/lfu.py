"""Least Frequently Used cache policy."""
import json
from backend.algorithms.base import BaseCache
from backend.cache.cache_object import CacheObject


class LFUCache(BaseCache):
    algorithm_name = "LFU"

    def get(self, key: str) -> CacheObject | None:
        return super().get(key)  # touch() increments frequency and last_accessed

    def put(self, key, value, cost=None) -> str | None:
        if key in self.items:
            item = self.items[key]
            item.value = value
            item.cost = 0.0 if cost is None else float(cost)
            item.size = self._value_size(value)
            item.touch()   # preserve and increment existing frequency
            return None
        self.items[key] = self._cache_object(key, value, cost)
        return self.evict() if len(self.items) > self.capacity else None

    def evict(self) -> str | None:
        if not self.items:
            return None
        # lowest frequency wins; last_accessed breaks ties (older = evict first)
        victim = min(self.items.values(), key=lambda x: (x.frequency, x.last_accessed)).key
        del self.items[victim]
        return victim
