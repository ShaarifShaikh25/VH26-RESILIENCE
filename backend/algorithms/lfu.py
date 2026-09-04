"""Least Frequently Used cache policy."""
from backend.algorithms.base import BaseCache
from backend.cache.cache_object import CacheObject


class LFUCache(BaseCache):
    def put(self, key, value, cost=None) -> str | None:
        """Store a value; cost is accepted for the common cache interface."""
        item = self._cache_object(key, value, cost)
        if item.key in self.items:
            self.items[item.key] = item
            return None
        victim = self.evict() if len(self.items) >= self.capacity else None
        self.items[item.key] = item
        return victim

    def evict(self) -> str | None:
        if not self.items:
            return None
        victim = min(self.items.values(), key=lambda x: (x.frequency, x.last_accessed)).key
        del self.items[victim]
        return victim
