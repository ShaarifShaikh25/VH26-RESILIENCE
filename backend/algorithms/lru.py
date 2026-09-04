"""Least Recently Used cache policy."""
import json
from collections import OrderedDict
from backend.algorithms.base import BaseCache
from backend.cache.cache_object import CacheObject


class LRUCache(BaseCache):
    algorithm_name = "LRU"

    def __init__(self, capacity: int) -> None:
        super().__init__(capacity)
        self.items: OrderedDict[str, CacheObject] = OrderedDict()

    def get(self, key: str) -> CacheObject | None:
        item = super().get(key)          # calls touch() on the CacheObject
        if item:
            self.items.move_to_end(key)  # mark as most recently used
        return item

    def put(self, key, value, cost=None) -> str | None:
        if key in self.items:
            item = self.items[key]
            item.value = value
            item.cost = 0.0 if cost is None else float(cost)
            item.size = self._value_size(value)
            item.touch()
            self.items.move_to_end(key)
            return None
        self.items[key] = self._cache_object(key, value, cost)
        return self.evict() if len(self.items) > self.capacity else None

    def evict(self) -> str | None:
        if not self.items:
            return None
        victim, _ = self.items.popitem(last=False)  # pop least recently used (front)
        return victim
