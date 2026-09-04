"""Least Recently Used cache policy."""
from backend.algorithms.base import BaseCache
from backend.cache.cache_object import CacheObject


class LRUCache(BaseCache):
    def put(self, item: CacheObject) -> str | None:
        if item.key in self.items:
            self.items[item.key] = item
            return None
        victim = self.evict() if len(self.items) >= self.capacity else None
        self.items[item.key] = item
        return victim

    def evict(self) -> str | None:
        if not self.items:
            return None
        victim = min(self.items.values(), key=lambda x: x.last_accessed).key
        del self.items[victim]
        return victim
