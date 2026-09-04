"""Shared contract for cache eviction policies."""
from abc import ABC, abstractmethod
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
    def put(self, item: CacheObject) -> str | None:
        """Insert an item and return the key evicted, if any."""

    @abstractmethod
    def evict(self) -> str | None:
        """Evict one victim and return its key."""
