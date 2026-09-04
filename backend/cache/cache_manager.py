"""One public cache API that selects a standard or adaptive policy."""
import json
from backend.algorithms.gds import GDSCache
from backend.algorithms.lfu import LFUCache
from backend.algorithms.lru import LRUCache
from backend.cache.cache_object import CacheObject
from backend.cache.redis_client import RedisClient
from backend.config import settings
from backend.core.decision_engine import DecisionEngine
from backend.core.scoring_engine import ScoringEngine
from backend.metrics.logger import log_decision


class AdaptiveCacheManager:
    """Coordinates metadata, eviction policy, and optional Redis persistence."""

    def __init__(self, algorithm: str = settings.algorithm, capacity: int = settings.cache_capacity) -> None:
        self.algorithm = algorithm.lower()
        policies = {"lru": LRUCache, "lfu": LFUCache, "gds": GDSCache, "adaptive": LRUCache}
        if self.algorithm not in policies:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
        self.policy = policies[self.algorithm](capacity)
        self.redis = RedisClient(settings.redis_url)
        self.scorer = ScoringEngine(settings.weights)
        self.decider = DecisionEngine(self.scorer, settings.decision_threshold)

    def set_workload(self, workload: str) -> None:
        if self.algorithm == "adaptive":
            self.scorer.adjust_for_workload(workload)

    def get(self, key: str):
        item = self.policy.get(key)
        if not item:
            return None
        value = self.redis.get(key)
        return item.value if value is None else value

    def put(self, key: str, value, cost: float = 1.0) -> None:
        size = max(len(json.dumps(value)), 1)
        item = CacheObject(key=key, value=value, size=size, cost=cost)
        if self.algorithm == "adaptive" and len(self.policy.items) >= self.policy.capacity and key not in self.policy.items:
            victim = min(self.policy.items.values(), key=self.scorer.score)
            del self.policy.items[victim.key]
            self.redis.delete(victim.key)
            log_decision(victim.key, "evict", self.algorithm)
        evicted = self.policy.put(item)
        if evicted:
            self.redis.delete(evicted)
            log_decision(evicted, "evict", self.algorithm)
        self.redis.set(key, value)
        log_decision(key, "retain", self.algorithm)

    def decide(self, key: str) -> str | None:
        item = self.policy.items.get(key)
        return self.decider.decide(item) if item else None
