"""Shared contract for cache eviction policies."""
from abc import ABC, abstractmethod
import json
from backend.cache.cache_object import CacheObject


class BaseCache(ABC):
    def __init__(self, capacity: int) -> None:
        self.capacity = capacity
        self.items: dict[str, CacheObject] = {}

    def get(self, key: str) -> CacheObject | None:
        item = self.items.get(key)
        if item:
            item.touch()
        return item

    @abstractmethod
    def put(self, key, value, cost=None) -> str | None:
        """Insert an item and return the key evicted, if any."""

    @staticmethod
    def _cache_object(key, value, cost=None) -> CacheObject:
        """Create the shared metadata record required by all policies."""
        return CacheObject(
            key=key,
            value=value,
            size=max(len(json.dumps(value, default=str)), 1),
            cost=0.0 if cost is None else float(cost),
        )

    @abstractmethod
    def evict(self) -> str | None:
        """Evict one victim and return its key."""
